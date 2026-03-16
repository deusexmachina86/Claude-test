"""HTTP client that talks to the patchright-cli server."""
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9223
_BASE = f"http://{SERVER_HOST}:{SERVER_PORT}"
_PID_FILE = Path.home() / ".patchright-cli" / "server.pid"


def _server_running() -> bool:
    try:
        r = httpx.get(f"{_BASE}/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def _start_server() -> bool:
    _PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, "-c",
         "from patchright_cli.server import start_server; start_server()"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    _PID_FILE.write_text(str(proc.pid))
    for _ in range(20):
        time.sleep(0.5)
        if _server_running():
            return True
    return False


def ensure_server():
    if not _server_running():
        if not _start_server():
            raise RuntimeError(
                "Could not start patchright-cli server.\n"
                "Make sure patchright is installed: pip install patchright && patchright install chrome"
            )


def send(session: str, command: str, params: Optional[Dict[str, Any]] = None) -> Dict:
    ensure_server()
    try:
        r = httpx.post(
            f"{_BASE}/sessions/{session}/{command}",
            json={"params": params or {}},
            timeout=60.0,
        )
        return r.json()
    except httpx.TimeoutException:
        return {"success": False, "error": "Command timed out."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def list_sessions() -> List[Dict]:
    ensure_server()
    try:
        r = httpx.get(f"{_BASE}/sessions", timeout=5.0)
        return r.json()
    except Exception:
        return []
