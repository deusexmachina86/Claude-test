"""Click-based CLI for patchright-cli."""
import json
import sys
from typing import Optional

import click

from . import client as _c

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"], "max_content_width": 100}


def _print(resp: dict):
    if not resp.get("success"):
        click.echo(f"Error: {resp.get('error', 'Unknown error')}", err=True)
        sys.exit(1)

    data = resp.get("data")
    snapshot = resp.get("snapshot")

    if data is not None:
        if isinstance(data, (dict, list)):
            click.echo(json.dumps(data, indent=2))
        else:
            click.echo(str(data))

    if snapshot:
        click.echo(snapshot)


# ── Root group ─────────────────────────────────────────────────────────────────

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("-s", "--session", default="default", envvar="PATCHRIGHT_SESSION",
              metavar="NAME", help='Browser session name (default: "default").')
@click.pass_context
def cli(ctx, session):
    """Stealth browser automation CLI powered by Patchright.

    Patchright patches Playwright to bypass bot-detection (Cloudflare, DataDome, etc.)
    by avoiding the Runtime.enable CDP command that anti-bot systems detect.

    \b
    Quick start:
      patchright-cli open https://example.com
      patchright-cli snapshot
      patchright-cli click e3
      patchright-cli close
    """
    ctx.ensure_object(dict)
    ctx.obj["session"] = session


def _sn(ctx) -> str:
    return ctx.obj["session"]


# ── Browser lifecycle ──────────────────────────────────────────────────────────

@cli.command()
@click.argument("url", required=False)
@click.option("--browser", default="chrome", show_default=True,
              type=click.Choice(["chrome", "msedge", "chromium"]),
              help="Browser channel (Chromium-based only).")
@click.option("--persistent/--no-persistent", default=True, show_default=True,
              help="Use a persistent browser profile.")
@click.option("--profile", default=None, metavar="PATH",
              help="Custom browser profile directory.")
@click.option("--headless", is_flag=True, help="Run in headless mode (reduces stealth; not recommended for bot-protected sites).")
@click.option("--extension", is_flag=True, hidden=True,
              help="(Reserved) Connect via browser extension.")
@click.option("--config", default=None, hidden=True, metavar="FILE",
              help="(Reserved) Config file path.")
@click.pass_context
def open(ctx, url, browser, persistent, profile, headless, extension, config):
    """Open a browser window, optionally navigating to URL."""
    _print(_c.send(_sn(ctx), "open", {
        "url": url, "browser": browser, "persistent": persistent,
        "profile": profile, "headless": headless,
    }))


@cli.command()
@click.pass_context
def close(ctx):
    """Close the current browser session."""
    _print(_c.send(_sn(ctx), "close"))


@cli.command("close-all")
@click.pass_context
def close_all(ctx):
    """Close all open browser sessions."""
    _print(_c.send(_sn(ctx), "close-all"))


@cli.command("kill-all")
@click.pass_context
def kill_all(ctx):
    """Forcefully kill all browser processes."""
    _print(_c.send(_sn(ctx), "close-all"))


@cli.command("delete-data")
@click.pass_context
def delete_data(ctx):
    """Delete user data for the current session."""
    _print(_c.send(_sn(ctx), "delete-data"))


@cli.command("list")
@click.pass_context
def list_cmd(ctx):
    """List all active browser sessions."""
    sessions = _c.list_sessions()
    if not sessions:
        click.echo("No active sessions.")
        return
    for s in sessions:
        active = " (current)" if s["name"] == _sn(ctx) else ""
        click.echo(f"  {s['name']}{active}  tabs={s['tabs']}  url={s['url'] or 'none'}")


# ── Navigation ─────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("url")
@click.pass_context
def goto(ctx, url):
    """Navigate to URL."""
    _print(_c.send(_sn(ctx), "goto", {"url": url}))


@cli.command("go-back")
@click.pass_context
def go_back(ctx):
    """Navigate back."""
    _print(_c.send(_sn(ctx), "go-back"))


@cli.command("go-forward")
@click.pass_context
def go_forward(ctx):
    """Navigate forward."""
    _print(_c.send(_sn(ctx), "go-forward"))


@cli.command()
@click.pass_context
def reload(ctx):
    """Reload the current page."""
    _print(_c.send(_sn(ctx), "reload"))


# ── Interactions ───────────────────────────────────────────────────────────────

@cli.command()
@click.argument("ref")
@click.pass_context
def click(ctx, ref):
    """Click an element by its snapshot ref (e.g. e3)."""
    _print(_c.send(_sn(ctx), "click", {"ref": ref}))


@cli.command()
@click.argument("ref")
@click.pass_context
def dblclick(ctx, ref):
    """Double-click an element by ref."""
    _print(_c.send(_sn(ctx), "dblclick", {"ref": ref}))


@cli.command()
@click.argument("text")
@click.pass_context
def type(ctx, text):
    """Type text into the focused element."""
    _print(_c.send(_sn(ctx), "type", {"text": text}))


@cli.command()
@click.argument("ref")
@click.argument("value")
@click.pass_context
def fill(ctx, ref, value):
    """Fill an input field (clears first)."""
    _print(_c.send(_sn(ctx), "fill", {"ref": ref, "value": value}))


@cli.command()
@click.argument("src_ref")
@click.argument("dst_ref")
@click.pass_context
def drag(ctx, src_ref, dst_ref):
    """Drag element SRC_REF to DST_REF."""
    _print(_c.send(_sn(ctx), "drag", {"src": src_ref, "dst": dst_ref}))


@cli.command()
@click.argument("ref")
@click.pass_context
def hover(ctx, ref):
    """Hover over an element."""
    _print(_c.send(_sn(ctx), "hover", {"ref": ref}))


@cli.command()
@click.argument("ref")
@click.argument("value")
@click.pass_context
def select(ctx, ref, value):
    """Select an option in a <select> element."""
    _print(_c.send(_sn(ctx), "select", {"ref": ref, "value": value}))


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.argument("ref", required=False)
@click.pass_context
def upload(ctx, file, ref):
    """Upload a file to an <input type=file> element."""
    params = {"file": file}
    if ref:
        params["ref"] = ref
    _print(_c.send(_sn(ctx), "upload", params))


@cli.command()
@click.argument("ref")
@click.pass_context
def check(ctx, ref):
    """Check a checkbox."""
    _print(_c.send(_sn(ctx), "check", {"ref": ref}))


@cli.command()
@click.argument("ref")
@click.pass_context
def uncheck(ctx, ref):
    """Uncheck a checkbox."""
    _print(_c.send(_sn(ctx), "uncheck", {"ref": ref}))


@cli.command()
@click.option("--filename", default=None, metavar="FILE",
              help="Save snapshot to file (auto-named if omitted).")
@click.pass_context
def snapshot(ctx, filename):
    """Take an accessibility snapshot of the current page."""
    params = {}
    if filename:
        params["filename"] = filename
    _print(_c.send(_sn(ctx), "snapshot", params))


@cli.command()
@click.argument("expression")
@click.argument("ref", required=False)
@click.pass_context
def eval(ctx, expression, ref):
    """Evaluate a JavaScript expression, optionally on an element ref."""
    params = {"expression": expression}
    if ref:
        params["ref"] = ref
    _print(_c.send(_sn(ctx), "eval", params))


@cli.command("dialog-accept")
@click.argument("text", required=False)
@click.pass_context
def dialog_accept(ctx, text):
    """Accept the next browser dialog, optionally with TEXT."""
    params = {}
    if text:
        params["text"] = text
    _print(_c.send(_sn(ctx), "dialog-accept", params))


@cli.command("dialog-dismiss")
@click.pass_context
def dialog_dismiss(ctx):
    """Dismiss the next browser dialog."""
    _print(_c.send(_sn(ctx), "dialog-dismiss"))


@cli.command()
@click.argument("width", type=int)
@click.argument("height", type=int)
@click.pass_context
def resize(ctx, width, height):
    """Resize the viewport to WIDTH x HEIGHT pixels."""
    _print(_c.send(_sn(ctx), "resize", {"width": width, "height": height}))


# ── Keyboard ───────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("key")
@click.pass_context
def press(ctx, key):
    """Press a key (e.g. Enter, ArrowDown, Tab)."""
    _print(_c.send(_sn(ctx), "press", {"key": key}))


@cli.command()
@click.argument("key")
@click.pass_context
def keydown(ctx, key):
    """Hold a key down."""
    _print(_c.send(_sn(ctx), "keydown", {"key": key}))


@cli.command()
@click.argument("key")
@click.pass_context
def keyup(ctx, key):
    """Release a held key."""
    _print(_c.send(_sn(ctx), "keyup", {"key": key}))


# ── Mouse ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.pass_context
def mousemove(ctx, x, y):
    """Move the mouse to (X, Y)."""
    _print(_c.send(_sn(ctx), "mousemove", {"x": x, "y": y}))


@cli.command()
@click.argument("button", required=False, default="left",
                type=click.Choice(["left", "right", "middle"]))
@click.pass_context
def mousedown(ctx, button):
    """Press a mouse button down."""
    _print(_c.send(_sn(ctx), "mousedown", {"button": button}))


@cli.command()
@click.argument("button", required=False, default="left",
                type=click.Choice(["left", "right", "middle"]))
@click.pass_context
def mouseup(ctx, button):
    """Release a mouse button."""
    _print(_c.send(_sn(ctx), "mouseup", {"button": button}))


@cli.command()
@click.argument("delta_x", type=float)
@click.argument("delta_y", type=float)
@click.pass_context
def mousewheel(ctx, delta_x, delta_y):
    """Scroll the mouse wheel by (DELTA_X, DELTA_Y)."""
    _print(_c.send(_sn(ctx), "mousewheel", {"deltaX": delta_x, "deltaY": delta_y}))


# ── Save As ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("ref", required=False)
@click.option("--filename", default=None, metavar="FILE",
              help="Output filename (auto-named if omitted).")
@click.pass_context
def screenshot(ctx, ref, filename):
    """Take a screenshot of the page or an element."""
    params = {}
    if ref:
        params["ref"] = ref
    if filename:
        params["filename"] = filename
    _print(_c.send(_sn(ctx), "screenshot", params))


@cli.command()
@click.option("--filename", default=None, metavar="FILE",
              help="Output filename (auto-named if omitted).")
@click.pass_context
def pdf(ctx, filename):
    """Save the page as a PDF."""
    params = {}
    if filename:
        params["filename"] = filename
    _print(_c.send(_sn(ctx), "pdf", params))


# ── Tabs ───────────────────────────────────────────────────────────────────────

@cli.command("tab-list")
@click.pass_context
def tab_list(ctx):
    """List all open tabs."""
    _print(_c.send(_sn(ctx), "tab-list"))


@cli.command("tab-new")
@click.argument("url", required=False)
@click.pass_context
def tab_new(ctx, url):
    """Open a new tab, optionally navigating to URL."""
    params = {}
    if url:
        params["url"] = url
    _print(_c.send(_sn(ctx), "tab-new", params))


@cli.command("tab-close")
@click.argument("index", required=False, type=int)
@click.pass_context
def tab_close(ctx, index):
    """Close a tab by INDEX (default: current tab)."""
    params = {}
    if index is not None:
        params["index"] = index
    _print(_c.send(_sn(ctx), "tab-close", params))


@cli.command("tab-select")
@click.argument("index", type=int)
@click.pass_context
def tab_select(ctx, index):
    """Switch to tab at INDEX."""
    _print(_c.send(_sn(ctx), "tab-select", {"index": index}))


# ── Storage State ──────────────────────────────────────────────────────────────

@cli.command("state-save")
@click.argument("filename", required=False, default="state.json")
@click.pass_context
def state_save(ctx, filename):
    """Save cookies and storage state to FILENAME."""
    _print(_c.send(_sn(ctx), "state-save", {"filename": filename}))


@cli.command("state-load")
@click.argument("filename", default="state.json")
@click.pass_context
def state_load(ctx, filename):
    """Load cookies from a saved state FILENAME."""
    _print(_c.send(_sn(ctx), "state-load", {"filename": filename}))


# ── Cookies ────────────────────────────────────────────────────────────────────

@cli.command("cookie-list")
@click.option("--domain", default=None, help="Filter by domain.")
@click.pass_context
def cookie_list(ctx, domain):
    """List all cookies."""
    params = {}
    if domain:
        params["domain"] = domain
    _print(_c.send(_sn(ctx), "cookie-list", params))


@cli.command("cookie-get")
@click.argument("name")
@click.pass_context
def cookie_get(ctx, name):
    """Get a cookie by NAME."""
    _print(_c.send(_sn(ctx), "cookie-get", {"name": name}))


@cli.command("cookie-set")
@click.argument("name")
@click.argument("value")
@click.option("--domain", default=None)
@click.option("--http-only", "http_only", is_flag=True)
@click.option("--secure", is_flag=True)
@click.pass_context
def cookie_set(ctx, name, value, domain, http_only, secure):
    """Set a cookie."""
    params: dict = {"name": name, "value": value}
    if domain:
        params["domain"] = domain
    if http_only:
        params["httpOnly"] = True
    if secure:
        params["secure"] = True
    _print(_c.send(_sn(ctx), "cookie-set", params))


@cli.command("cookie-delete")
@click.argument("name")
@click.pass_context
def cookie_delete(ctx, name):
    """Delete a cookie by NAME."""
    _print(_c.send(_sn(ctx), "cookie-delete", {"name": name}))


@cli.command("cookie-clear")
@click.pass_context
def cookie_clear(ctx):
    """Clear all cookies."""
    _print(_c.send(_sn(ctx), "cookie-clear"))


# ── LocalStorage ───────────────────────────────────────────────────────────────

@cli.command("localstorage-list")
@click.pass_context
def localstorage_list(ctx):
    """List all localStorage entries."""
    _print(_c.send(_sn(ctx), "localstorage-list"))


@cli.command("localstorage-get")
@click.argument("key")
@click.pass_context
def localstorage_get(ctx, key):
    """Get a localStorage entry by KEY."""
    _print(_c.send(_sn(ctx), "localstorage-get", {"key": key}))


@cli.command("localstorage-set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def localstorage_set(ctx, key, value):
    """Set a localStorage KEY=VALUE."""
    _print(_c.send(_sn(ctx), "localstorage-set", {"key": key, "value": value}))


@cli.command("localstorage-delete")
@click.argument("key")
@click.pass_context
def localstorage_delete(ctx, key):
    """Delete a localStorage entry."""
    _print(_c.send(_sn(ctx), "localstorage-delete", {"key": key}))


@cli.command("localstorage-clear")
@click.pass_context
def localstorage_clear(ctx):
    """Clear all localStorage entries."""
    _print(_c.send(_sn(ctx), "localstorage-clear"))


# ── SessionStorage ─────────────────────────────────────────────────────────────

@cli.command("sessionstorage-list")
@click.pass_context
def sessionstorage_list(ctx):
    """List all sessionStorage entries."""
    _print(_c.send(_sn(ctx), "sessionstorage-list"))


@cli.command("sessionstorage-get")
@click.argument("key")
@click.pass_context
def sessionstorage_get(ctx, key):
    """Get a sessionStorage entry by KEY."""
    _print(_c.send(_sn(ctx), "sessionstorage-get", {"key": key}))


@cli.command("sessionstorage-set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def sessionstorage_set(ctx, key, value):
    """Set a sessionStorage KEY=VALUE."""
    _print(_c.send(_sn(ctx), "sessionstorage-set", {"key": key, "value": value}))


@cli.command("sessionstorage-delete")
@click.argument("key")
@click.pass_context
def sessionstorage_delete(ctx, key):
    """Delete a sessionStorage entry."""
    _print(_c.send(_sn(ctx), "sessionstorage-delete", {"key": key}))


@cli.command("sessionstorage-clear")
@click.pass_context
def sessionstorage_clear(ctx):
    """Clear all sessionStorage entries."""
    _print(_c.send(_sn(ctx), "sessionstorage-clear"))


# ── Network Routes ─────────────────────────────────────────────────────────────

@cli.command()
@click.argument("pattern")
@click.option("--status", default=None, type=int, help="HTTP status to return.")
@click.option("--body", default=None, help="Response body to return.")
@click.pass_context
def route(ctx, pattern, status, body):
    """Intercept network requests matching PATTERN."""
    params: dict = {"pattern": pattern}
    if status is not None:
        params["status"] = status
    if body is not None:
        params["body"] = body
    _print(_c.send(_sn(ctx), "route", params))


@cli.command("route-list")
@click.pass_context
def route_list(ctx):
    """List active network routes."""
    _print(_c.send(_sn(ctx), "route-list"))


@cli.command()
@click.argument("pattern", required=False)
@click.pass_context
def unroute(ctx, pattern):
    """Remove a network route (or all routes if PATTERN omitted)."""
    params = {}
    if pattern:
        params["pattern"] = pattern
    _print(_c.send(_sn(ctx), "unroute", params))


# ── DevTools ───────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("level", required=False,
                type=click.Choice(["log", "info", "warning", "error", "debug"]))
@click.pass_context
def console(ctx, level):
    """Show captured console messages, optionally filtered by LEVEL."""
    params = {}
    if level:
        params["level"] = level
    _print(_c.send(_sn(ctx), "console", params))


@cli.command()
@click.pass_context
def network(ctx):
    """Show captured network requests and responses."""
    _print(_c.send(_sn(ctx), "network"))


@cli.command("run-code")
@click.argument("code")
@click.pass_context
def run_code(ctx, code):
    """Run arbitrary JavaScript CODE in the page context."""
    _print(_c.send(_sn(ctx), "run-code", {"code": code}))


@cli.command("tracing-start")
@click.pass_context
def tracing_start(ctx):
    """Start Playwright tracing."""
    _print(_c.send(_sn(ctx), "tracing-start"))


@cli.command("tracing-stop")
@click.option("--filename", default=None, metavar="FILE")
@click.pass_context
def tracing_stop(ctx, filename):
    """Stop tracing and save to FILENAME (auto-named if omitted)."""
    params = {}
    if filename:
        params["filename"] = filename
    _print(_c.send(_sn(ctx), "tracing-stop", params))


@cli.command("video-start")
@click.pass_context
def video_start(ctx):
    """Start video recording (requires browser to be opened with recording enabled)."""
    _print(_c.send(_sn(ctx), "video-start"))


@cli.command("video-stop")
@click.argument("filename", required=False)
@click.pass_context
def video_stop(ctx, filename):
    """Stop video recording and save to FILENAME."""
    params = {}
    if filename:
        params["filename"] = filename
    _print(_c.send(_sn(ctx), "video-stop", params))
