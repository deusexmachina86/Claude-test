"""Patchright CLI server — manages browser sessions over HTTP."""
import asyncio
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    from patchright.async_api import async_playwright, BrowserContext, Page
except ImportError as exc:
    raise SystemExit(
        "patchright not installed. Run:\n  pip install patchright\n  patchright install chrome"
    ) from exc

app = FastAPI(title="patchright-cli")

# ── Models ─────────────────────────────────────────────────────────────────────

class CommandRequest(BaseModel):
    params: Dict[str, Any] = {}

class CommandResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    snapshot: Optional[str] = None

# ── Session ────────────────────────────────────────────────────────────────────

class Session:
    def __init__(self, name: str):
        self.name = name
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.pages: List[Page] = []
        self.current_page_index: int = 0
        self.refs: Dict[str, Dict] = {}
        self.console_logs: List[Dict] = []
        self.network_logs: List[Dict] = []
        self.routes: Dict[str, Any] = {}
        self.profile_dir: Optional[str] = None
        self._temp_profile: Optional[str] = None

    @property
    def page(self) -> Optional[Page]:
        if self.pages and self.current_page_index < len(self.pages):
            return self.pages[self.current_page_index]
        return None

    async def close(self):
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
            self.context = None
            self.pages = []
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
        if self._temp_profile and os.path.exists(self._temp_profile):
            shutil.rmtree(self._temp_profile, ignore_errors=True)
            self._temp_profile = None


_sessions: Dict[str, Session] = {}


def get_session(name: str) -> Session:
    if name not in _sessions:
        _sessions[name] = Session(name)
    return _sessions[name]


async def require_open(session: Session):
    if session.context is None:
        raise HTTPException(400, "No browser open. Run 'open' first.")


# ── Snapshot ───────────────────────────────────────────────────────────────────

_INTERACTIVE_ROLES = {
    "button", "link", "textbox", "searchbox", "combobox", "listbox",
    "checkbox", "radio", "menuitem", "tab", "switch", "spinbutton",
    "slider", "option", "menuitemcheckbox", "menuitemradio", "treeitem",
    "gridcell", "cell",
}


def _walk(node: Dict, refs: Dict, counter: List[int], indent: int) -> List[str]:
    if not node:
        return []

    role = node.get("role", "")
    name = node.get("name", "")
    value = node.get("value", "")

    # Skip empty containers
    if role in ("generic", "none", "") and not name:
        lines = []
        for child in node.get("children", []):
            lines.extend(_walk(child, refs, counter, indent))
        return lines

    ref_str = ""
    if role in _INTERACTIVE_ROLES or node.get("focusable"):
        counter[0] += 1
        ref = f"e{counter[0]}"
        refs[ref] = node
        ref_str = f" [{ref}]"

    parts = [f"{'  ' * indent}- {role}"]
    if name:
        parts.append(f'"{name}"')
    if value:
        parts.append(f'value="{value}"')
    if node.get("checked") is True:
        parts.append("[checked]")
    if node.get("disabled"):
        parts.append("[disabled]")
    if node.get("expanded") is not None:
        parts.append(f'[expanded={node["expanded"]}]')

    lines = [" ".join(parts) + ref_str]
    for child in node.get("children", []):
        lines.extend(_walk(child, refs, counter, indent + 1))
    return lines


async def take_snapshot(session: Session, filename: Optional[str] = None) -> str:
    if not session.page:
        return "No page open."
    try:
        url = session.page.url
        title = await session.page.title()
        tree = await session.page.accessibility.snapshot()

        session.refs = {}
        counter = [0]
        tree_lines = _walk(tree, session.refs, counter, 0) if tree else ["(empty page)"]

        lines = [
            "Page",
            f"  • Page URL: {url}",
            f"  • Page Title: {title}",
            f"  • Tab [{session.current_page_index}] of {len(session.pages)}",
            "",
            "Snapshot",
        ] + tree_lines

        text = "\n".join(lines)
        if filename:
            Path(filename).write_text(text)
            text += f"\n\n(Saved to {filename})"
        return text
    except Exception as exc:
        return f"Snapshot error: {exc}"


async def find_element(page: Page, ref_info: Dict):
    role = ref_info.get("role", "")
    name = ref_info.get("name", "")

    _role_map = {
        "button": "button", "link": "link", "textbox": "textbox",
        "searchbox": "searchbox", "combobox": "combobox", "listbox": "listbox",
        "checkbox": "checkbox", "radio": "radio", "menuitem": "menuitem",
        "tab": "tab", "switch": "switch", "option": "option",
    }

    if role in _role_map and name:
        loc = page.get_by_role(_role_map[role], name=name)
        if await loc.count() >= 1:
            return loc.first

    if name:
        loc = page.get_by_text(name, exact=True)
        if await loc.count() == 1:
            return loc

    raise HTTPException(404, f"Element not found for ref (role={role}, name={name})")


def resolve_ref(session: Session, ref: str) -> Dict:
    if ref not in session.refs:
        raise HTTPException(404, f"Ref '{ref}' not found. Run 'snapshot' first.")
    return session.refs[ref]


# ── Open / Close ───────────────────────────────────────────────────────────────

def _attach_page_listeners(page: Page, session: Session):
    page.on("console", lambda m: session.console_logs.append(
        {"type": m.type, "text": m.text, "time": datetime.now().isoformat()}
    ))
    page.on("request", lambda r: session.network_logs.append(
        {"type": "request", "method": r.method, "url": r.url, "time": datetime.now().isoformat()}
    ))
    page.on("response", lambda r: session.network_logs.append(
        {"type": "response", "status": r.status, "url": r.url, "time": datetime.now().isoformat()}
    ))


@app.post("/sessions/{sn}/open", response_model=CommandResponse)
async def cmd_open(sn: str, req: CommandRequest):
    session = get_session(sn)
    p = req.params

    if session.context:
        await session.close()

    session.playwright = await async_playwright().start()

    channel = p.get("browser", "chrome")
    if channel in ("firefox", "webkit"):
        channel = "chrome"  # patchright only supports Chromium

    profile_dir = p.get("profile")
    if not profile_dir:
        profile_dir = tempfile.mkdtemp(prefix=f"pr-cli-{sn}-")
        session._temp_profile = profile_dir
    session.profile_dir = profile_dir

    launch_kwargs: Dict[str, Any] = {
        "headless": p.get("headless", False),
        "args": ["--no-sandbox", "--disable-setuid-sandbox"],
    }
    if channel != "chromium":
        launch_kwargs["channel"] = channel

    context = await session.playwright.chromium.launch_persistent_context(
        profile_dir, **launch_kwargs
    )
    session.context = context

    if context.pages:
        session.pages = list(context.pages)
    else:
        session.pages = [await context.new_page()]
    session.current_page_index = 0

    for pg in session.pages:
        _attach_page_listeners(pg, session)

    url = p.get("url")
    if url:
        await session.page.goto(url, wait_until="domcontentloaded")

    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/close", response_model=CommandResponse)
async def cmd_close(sn: str, req: CommandRequest):
    session = get_session(sn)
    await session.close()
    _sessions.pop(sn, None)
    return CommandResponse(success=True, data="Browser closed.")


@app.post("/sessions/{sn}/close-all", response_model=CommandResponse)
async def cmd_close_all(sn: str, req: CommandRequest):
    for sess in list(_sessions.values()):
        await sess.close()
    _sessions.clear()
    return CommandResponse(success=True, data="All browsers closed.")


@app.post("/sessions/{sn}/delete-data", response_model=CommandResponse)
async def cmd_delete_data(sn: str, req: CommandRequest):
    session = get_session(sn)
    profile = session.profile_dir
    await session.close()
    _sessions.pop(sn, None)
    if profile and os.path.exists(profile):
        shutil.rmtree(profile, ignore_errors=True)
    return CommandResponse(success=True, data="User data deleted.")


@app.get("/sessions")
async def list_sessions_endpoint():
    result = []
    for name, sess in _sessions.items():
        result.append({
            "name": name,
            "url": sess.page.url if sess.page else None,
            "tabs": len(sess.pages),
            "open": sess.context is not None,
        })
    return result


# ── Navigation ─────────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/goto", response_model=CommandResponse)
async def cmd_goto(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.goto(req.params.get("url", ""), wait_until="domcontentloaded")
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/go-back", response_model=CommandResponse)
async def cmd_go_back(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.go_back()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/go-forward", response_model=CommandResponse)
async def cmd_go_forward(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.go_forward()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/reload", response_model=CommandResponse)
async def cmd_reload(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.reload()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


# ── Interactions ───────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/click", response_model=CommandResponse)
async def cmd_click(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    ref_info = resolve_ref(session, req.params.get("ref", ""))
    el = await find_element(session.page, ref_info)
    await el.click()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/dblclick", response_model=CommandResponse)
async def cmd_dblclick(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    ref_info = resolve_ref(session, req.params.get("ref", ""))
    el = await find_element(session.page, ref_info)
    await el.dbl_click()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/type", response_model=CommandResponse)
async def cmd_type(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.keyboard.type(req.params.get("text", ""))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/fill", response_model=CommandResponse)
async def cmd_fill(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    ref_info = resolve_ref(session, req.params.get("ref", ""))
    el = await find_element(session.page, ref_info)
    await el.fill(req.params.get("value", ""))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/drag", response_model=CommandResponse)
async def cmd_drag(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    src_el = await find_element(session.page, resolve_ref(session, req.params.get("src", "")))
    dst_el = await find_element(session.page, resolve_ref(session, req.params.get("dst", "")))
    await src_el.drag_to(dst_el)
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/hover", response_model=CommandResponse)
async def cmd_hover(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    ref_info = resolve_ref(session, req.params.get("ref", ""))
    el = await find_element(session.page, ref_info)
    await el.hover()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/select", response_model=CommandResponse)
async def cmd_select(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    ref_info = resolve_ref(session, req.params.get("ref", ""))
    el = await find_element(session.page, ref_info)
    await el.select_option(req.params.get("value", ""))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/upload", response_model=CommandResponse)
async def cmd_upload(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    ref_info = resolve_ref(session, req.params.get("ref", ""))
    el = await find_element(session.page, ref_info)
    await el.set_input_files(req.params.get("file", ""))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/check", response_model=CommandResponse)
async def cmd_check(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    ref_info = resolve_ref(session, req.params.get("ref", ""))
    el = await find_element(session.page, ref_info)
    await el.check()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/uncheck", response_model=CommandResponse)
async def cmd_uncheck(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    ref_info = resolve_ref(session, req.params.get("ref", ""))
    el = await find_element(session.page, ref_info)
    await el.uncheck()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/snapshot", response_model=CommandResponse)
async def cmd_snapshot(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    return CommandResponse(success=True, snapshot=await take_snapshot(session, req.params.get("filename")))


@app.post("/sessions/{sn}/eval", response_model=CommandResponse)
async def cmd_eval(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    expr = req.params.get("expression", "")
    ref = req.params.get("ref")
    if ref:
        ref_info = resolve_ref(session, ref)
        el = await find_element(session.page, ref_info)
        result = await el.evaluate(expr)
    else:
        result = await session.page.evaluate(expr)
    return CommandResponse(success=True, data=str(result), snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/dialog-accept", response_model=CommandResponse)
async def cmd_dialog_accept(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    text = req.params.get("text")

    async def _accept(dialog):
        await dialog.accept(text) if text else await dialog.accept()

    session.page.once("dialog", _accept)
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/dialog-dismiss", response_model=CommandResponse)
async def cmd_dialog_dismiss(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    session.page.once("dialog", lambda d: asyncio.ensure_future(d.dismiss()))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/resize", response_model=CommandResponse)
async def cmd_resize(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.set_viewport_size({
        "width": int(req.params.get("width", 1280)),
        "height": int(req.params.get("height", 720)),
    })
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


# ── Keyboard ───────────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/press", response_model=CommandResponse)
async def cmd_press(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.keyboard.press(req.params.get("key", ""))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/keydown", response_model=CommandResponse)
async def cmd_keydown(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.keyboard.down(req.params.get("key", ""))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/keyup", response_model=CommandResponse)
async def cmd_keyup(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.keyboard.up(req.params.get("key", ""))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


# ── Mouse ──────────────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/mousemove", response_model=CommandResponse)
async def cmd_mousemove(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.mouse.move(float(req.params.get("x", 0)), float(req.params.get("y", 0)))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/mousedown", response_model=CommandResponse)
async def cmd_mousedown(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.mouse.down(button=req.params.get("button", "left"))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/mouseup", response_model=CommandResponse)
async def cmd_mouseup(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.mouse.up(button=req.params.get("button", "left"))
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/mousewheel", response_model=CommandResponse)
async def cmd_mousewheel(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.mouse.wheel(
        float(req.params.get("deltaX", 0)),
        float(req.params.get("deltaY", 0)),
    )
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


# ── Save As ────────────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/screenshot", response_model=CommandResponse)
async def cmd_screenshot(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    filename = req.params.get("filename") or f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    ref = req.params.get("ref")
    if ref:
        el = await find_element(session.page, resolve_ref(session, ref))
        await el.screenshot(path=filename)
    else:
        await session.page.screenshot(path=filename)
    return CommandResponse(success=True, data=f"Saved to {filename}", snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/pdf", response_model=CommandResponse)
async def cmd_pdf(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    filename = req.params.get("filename") or f"page-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
    await session.page.pdf(path=filename)
    return CommandResponse(success=True, data=f"Saved to {filename}", snapshot=await take_snapshot(session))


# ── Tabs ───────────────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/tab-list", response_model=CommandResponse)
async def cmd_tab_list(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    tabs = [
        {"index": i, "url": pg.url, "title": await pg.title(), "active": i == session.current_page_index}
        for i, pg in enumerate(session.pages)
    ]
    return CommandResponse(success=True, data=tabs)


@app.post("/sessions/{sn}/tab-new", response_model=CommandResponse)
async def cmd_tab_new(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    page = await session.context.new_page()
    _attach_page_listeners(page, session)
    session.pages.append(page)
    session.current_page_index = len(session.pages) - 1
    url = req.params.get("url")
    if url:
        await page.goto(url, wait_until="domcontentloaded")
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/tab-close", response_model=CommandResponse)
async def cmd_tab_close(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    idx = int(req.params.get("index", session.current_page_index))
    if idx >= len(session.pages):
        raise HTTPException(400, "Tab index out of range.")
    await session.pages[idx].close()
    session.pages.pop(idx)
    if not session.pages:
        return CommandResponse(success=True, data="All tabs closed.")
    session.current_page_index = min(session.current_page_index, len(session.pages) - 1)
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/tab-select", response_model=CommandResponse)
async def cmd_tab_select(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    idx = int(req.params.get("index", 0))
    if idx >= len(session.pages):
        raise HTTPException(400, "Tab index out of range.")
    session.current_page_index = idx
    await session.page.bring_to_front()
    return CommandResponse(success=True, snapshot=await take_snapshot(session))


# ── Storage State ──────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/state-save", response_model=CommandResponse)
async def cmd_state_save(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    filename = req.params.get("filename", "state.json")
    await session.context.storage_state(path=filename)
    return CommandResponse(success=True, data=f"State saved to {filename}", snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/state-load", response_model=CommandResponse)
async def cmd_state_load(sn: str, req: CommandRequest):
    session = get_session(sn)
    filename = req.params.get("filename", "state.json")
    state = json.loads(Path(filename).read_text())
    if session.context:
        cookies = state.get("cookies", [])
        if cookies:
            await session.context.add_cookies(cookies)
    return CommandResponse(success=True, data=f"State loaded from {filename}")


# ── Cookies ────────────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/cookie-list", response_model=CommandResponse)
async def cmd_cookie_list(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    domain = req.params.get("domain")
    cookies = await session.context.cookies()
    if domain:
        cookies = [c for c in cookies if domain in c.get("domain", "")]
    return CommandResponse(success=True, data=cookies)


@app.post("/sessions/{sn}/cookie-get", response_model=CommandResponse)
async def cmd_cookie_get(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    name = req.params.get("name", "")
    cookies = await session.context.cookies()
    return CommandResponse(success=True, data=[c for c in cookies if c["name"] == name])


@app.post("/sessions/{sn}/cookie-set", response_model=CommandResponse)
async def cmd_cookie_set(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    cookie: Dict[str, Any] = {
        "name": req.params.get("name", ""),
        "value": req.params.get("value", ""),
        "url": session.page.url,
    }
    if "domain" in req.params:
        cookie["domain"] = req.params["domain"]
        del cookie["url"]
    if req.params.get("httpOnly"):
        cookie["httpOnly"] = True
    if req.params.get("secure"):
        cookie["secure"] = True
    await session.context.add_cookies([cookie])
    return CommandResponse(success=True, data="Cookie set.")


@app.post("/sessions/{sn}/cookie-delete", response_model=CommandResponse)
async def cmd_cookie_delete(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    name = req.params.get("name", "")
    cookies = await session.context.cookies()
    kept = [c for c in cookies if c["name"] != name]
    await session.context.clear_cookies()
    if kept:
        await session.context.add_cookies(kept)
    return CommandResponse(success=True, data=f"Cookie '{name}' deleted.")


@app.post("/sessions/{sn}/cookie-clear", response_model=CommandResponse)
async def cmd_cookie_clear(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.context.clear_cookies()
    return CommandResponse(success=True, data="All cookies cleared.")


# ── LocalStorage ───────────────────────────────────────────────────────────────

_LS_LIST = """() => { const o = {}; for (let i=0;i<localStorage.length;i++){const k=localStorage.key(i);o[k]=localStorage.getItem(k);} return o; }"""
_SS_LIST = """() => { const o = {}; for (let i=0;i<sessionStorage.length;i++){const k=sessionStorage.key(i);o[k]=sessionStorage.getItem(k);} return o; }"""


@app.post("/sessions/{sn}/localstorage-list", response_model=CommandResponse)
async def cmd_ls_list(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    return CommandResponse(success=True, data=await session.page.evaluate(_LS_LIST))


@app.post("/sessions/{sn}/localstorage-get", response_model=CommandResponse)
async def cmd_ls_get(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    key = req.params.get("key", "")
    val = await session.page.evaluate(f"() => localStorage.getItem({json.dumps(key)})")
    return CommandResponse(success=True, data=val)


@app.post("/sessions/{sn}/localstorage-set", response_model=CommandResponse)
async def cmd_ls_set(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    k, v = req.params.get("key", ""), req.params.get("value", "")
    await session.page.evaluate(f"() => localStorage.setItem({json.dumps(k)},{json.dumps(v)})")
    return CommandResponse(success=True, data=f"Set {k}={v}")


@app.post("/sessions/{sn}/localstorage-delete", response_model=CommandResponse)
async def cmd_ls_delete(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    k = req.params.get("key", "")
    await session.page.evaluate(f"() => localStorage.removeItem({json.dumps(k)})")
    return CommandResponse(success=True, data=f"Deleted '{k}'")


@app.post("/sessions/{sn}/localstorage-clear", response_model=CommandResponse)
async def cmd_ls_clear(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.evaluate("() => localStorage.clear()")
    return CommandResponse(success=True, data="localStorage cleared.")


# ── SessionStorage ─────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/sessionstorage-list", response_model=CommandResponse)
async def cmd_ss_list(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    return CommandResponse(success=True, data=await session.page.evaluate(_SS_LIST))


@app.post("/sessions/{sn}/sessionstorage-get", response_model=CommandResponse)
async def cmd_ss_get(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    k = req.params.get("key", "")
    val = await session.page.evaluate(f"() => sessionStorage.getItem({json.dumps(k)})")
    return CommandResponse(success=True, data=val)


@app.post("/sessions/{sn}/sessionstorage-set", response_model=CommandResponse)
async def cmd_ss_set(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    k, v = req.params.get("key", ""), req.params.get("value", "")
    await session.page.evaluate(f"() => sessionStorage.setItem({json.dumps(k)},{json.dumps(v)})")
    return CommandResponse(success=True, data=f"Set {k}={v}")


@app.post("/sessions/{sn}/sessionstorage-delete", response_model=CommandResponse)
async def cmd_ss_delete(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    k = req.params.get("key", "")
    await session.page.evaluate(f"() => sessionStorage.removeItem({json.dumps(k)})")
    return CommandResponse(success=True, data=f"Deleted '{k}'")


@app.post("/sessions/{sn}/sessionstorage-clear", response_model=CommandResponse)
async def cmd_ss_clear(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.page.evaluate("() => sessionStorage.clear()")
    return CommandResponse(success=True, data="sessionStorage cleared.")


# ── Network Routes ─────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/route", response_model=CommandResponse)
async def cmd_route(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    pattern = req.params.get("pattern", "")
    status = req.params.get("status")
    body = req.params.get("body")

    async def handler(route):
        if status is not None or body is not None:
            await route.fulfill(
                status=int(status) if status else 200,
                body=body or "",
                content_type="application/json" if body else "text/plain",
            )
        else:
            await route.continue_()

    await session.page.route(pattern, handler)
    session.routes[pattern] = {"status": status, "body": body}
    return CommandResponse(success=True, data=f"Route set for {pattern}")


@app.post("/sessions/{sn}/route-list", response_model=CommandResponse)
async def cmd_route_list(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    return CommandResponse(success=True, data=list(session.routes.keys()))


@app.post("/sessions/{sn}/unroute", response_model=CommandResponse)
async def cmd_unroute(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    pattern = req.params.get("pattern")
    if pattern:
        await session.page.unroute(pattern)
        session.routes.pop(pattern, None)
    else:
        for p in list(session.routes):
            await session.page.unroute(p)
        session.routes.clear()
    return CommandResponse(success=True, data="Routes cleared.")


# ── DevTools ───────────────────────────────────────────────────────────────────

@app.post("/sessions/{sn}/console", response_model=CommandResponse)
async def cmd_console(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    level = req.params.get("level")
    logs = session.console_logs
    if level:
        logs = [l for l in logs if l.get("type") == level]
    return CommandResponse(success=True, data=logs)


@app.post("/sessions/{sn}/network", response_model=CommandResponse)
async def cmd_network_logs(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    return CommandResponse(success=True, data=session.network_logs)


@app.post("/sessions/{sn}/run-code", response_model=CommandResponse)
async def cmd_run_code(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    code = req.params.get("code", "")
    result = await session.page.evaluate(f"async () => {{ {code} }}")
    return CommandResponse(success=True, data=str(result) if result is not None else None,
                           snapshot=await take_snapshot(session))


@app.post("/sessions/{sn}/tracing-start", response_model=CommandResponse)
async def cmd_tracing_start(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    await session.context.tracing.start(screenshots=True, snapshots=True)
    return CommandResponse(success=True, data="Tracing started.")


@app.post("/sessions/{sn}/tracing-stop", response_model=CommandResponse)
async def cmd_tracing_stop(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    filename = req.params.get("filename") or f"trace-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    await session.context.tracing.stop(path=filename)
    return CommandResponse(success=True, data=f"Trace saved to {filename}")


@app.post("/sessions/{sn}/video-start", response_model=CommandResponse)
async def cmd_video_start(sn: str, req: CommandRequest):
    return CommandResponse(success=False, error="Video recording must be enabled at browser open time (not yet supported via CLI flag).")


@app.post("/sessions/{sn}/video-stop", response_model=CommandResponse)
async def cmd_video_stop(sn: str, req: CommandRequest):
    session = get_session(sn)
    await require_open(session)
    filename = req.params.get("filename") or f"video-{datetime.now().strftime('%Y%m%d-%H%M%S')}.webm"
    if session.page.video:
        await session.page.video.save_as(filename)
        return CommandResponse(success=True, data=f"Video saved to {filename}")
    return CommandResponse(success=False, error="No video recording in progress.")


# ── Health & Server Start ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


def start_server(host: str = "127.0.0.1", port: int = 9223):
    uvicorn.run(app, host=host, port=port, log_level="error")


if __name__ == "__main__":
    start_server()
