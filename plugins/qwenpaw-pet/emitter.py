# -*- coding: utf-8 -*-
"""Fire-and-forget desktop event emitter."""

from __future__ import annotations

import asyncio
import functools
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("qwenpaw.pet_desktop")

DESKTOP_URL = os.environ.get(
    "QWENPAW_PET_DESKTOP_URL",
    "http://127.0.0.1:8765",
).rstrip("/")

TOKEN_PATH = Path(
    os.environ.get(
        "QWENPAW_PET_TOKEN_PATH",
        str(Path.home() / ".qwenpaw-pet/runtime/update-token"),
    ),
)

EVENT_TO_STATE = {
    "qwenpaw.startup": "waving",
    "qwenpaw.shutdown": "idle",
    "query.received": "jumping",
    "query.running": "running",
    "query.first_token": "review",
    "query.done": "review",
    "tool.detected": "running",
    "tool.result": "review",
    "query.cancelled": "waiting",
    "query.error": "failed",
    "approval.pending": "waiting",
    "approval.resolved": "idle",
    "approval.bulk_cancel": "idle",
    "idle": "idle",
}


def _read_token() -> str | None:
    try:
        token = TOKEN_PATH.read_text(encoding="utf-8").strip()
        return token or None
    except OSError:
        return None


def _headers() -> dict[str, str]:
    token = _read_token()
    if not token:
        return {}
    return {"X-QwenPaw-Pet-Token": token}


def _httpx_client_kwargs() -> dict[str, Any]:
    """Options for calls to the local pet desktop.

    ``trust_env=False`` avoids routing ``127.0.0.1`` through HTTP(S)_PROXY
    (e.g. Clash on 7890), which would time out and break all pet events.
    """
    return {"trust_env": False, "timeout": 0.35}


def desktop_health() -> dict[str, Any] | None:
    try:
        response = httpx.get(
            f"{DESKTOP_URL}/health",
            **_httpx_client_kwargs(),
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else None
    except Exception:
        return None


_MISSING_DEPS_HINT = (
    "Desktop runtime import failed (likely a missing dependency in "
    "QwenPaw's interpreter). Install into the same environment: "
    'pip install "fastapi>=0.110" "uvicorn>=0.27" "pillow>=10.0" '
    '"pyside6>=6.6" (PySide6 requires Python 3.10-3.13).'
)


def _spawn_desktop_background() -> tuple[bool, str | None]:
    """Start the pet desktop in a detached process.

    Runs ``sys.executable -m qwenpaw_pet_desktop.app``. The package lives
    next to this plugin and is on the *parent's* ``sys.path`` because
    ``plugin.py`` injects the plugin directory; the child process gets
    that location via ``PYTHONPATH`` so ``python -m qwenpaw_pet_desktop.app``
    resolves without any ``pip install``. Third-party deps (fastapi,
    uvicorn, pillow, PySide6) still need to be available to ``sys.executable``.

    Returns:
        ``(True, None)`` if a process was spawned, else
        ``(False, user-facing reason)``.
    """
    port = int(os.environ.get("QWENPAW_PET_DESKTOP_PORT", "8765"))
    try:
        from qwenpaw_pet_desktop import runtime as pet_rt
    except ImportError as exc:
        return False, f"{_MISSING_DEPS_HINT} ({exc})"

    try:
        pet_rt.ensure_runtime()
        # log_file is held open for the lifetime of the spawned child
        # so subprocess can write to it; a ``with`` block would close
        # it before the child writes anything.
        log_file = (
            pet_rt.log_path().open(  # pylint: disable=consider-using-with
                "ab",
            )
        )
        cmd: list[str] = [
            sys.executable,
            "-m",
            "qwenpaw_pet_desktop.app",
            "--port",
            str(port),
        ]
        scale = os.environ.get("QWENPAW_PET_DESKTOP_SCALE")
        if scale:
            cmd.extend(["--scale", str(scale)])
        pet_dir = os.environ.get("QWENPAW_PET_DESKTOP_PET_DIR")
        if pet_dir:
            cmd.extend(["--pet-dir", pet_dir])
        # subprocess does *not* inherit the parent's runtime sys.path
        # mutations (plugin.py adds the plugin dir to sys.path so the
        # embedded ``qwenpaw_pet_desktop`` package is importable here).
        # Propagate that path via PYTHONPATH so ``python -m
        # qwenpaw_pet_desktop.app`` can find the package.
        env = os.environ.copy()
        plugin_dir = str(Path(__file__).resolve().parent)
        existing_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            plugin_dir + os.pathsep + existing_pp
            if existing_pp
            else plugin_dir
        )
        # Fire-and-forget detached process; ``with`` would block on
        # exit and is not the lifecycle we want here.
        proc = subprocess.Popen(  # pylint: disable=consider-using-with
            cmd,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
        pet_rt.write_pid(proc.pid)
        return True, None
    except OSError as exc:
        return False, f"failed to start desktop: {exc}"


def ensure_desktop_available() -> None:
    """Best-effort start of the desktop runtime.

    If the executable is not installed or the user prefers manual startup,
    this stays quiet. QwenPaw should never fail because the pet is absent.
    """
    if desktop_health():
        return
    if os.environ.get("QWENPAW_PET_AUTOSTART", "1") == "0":
        return
    ok, hint = _spawn_desktop_background()
    if not ok:
        logger.warning("Could not autostart pet desktop: %s", hint)
        return
    deadline = time.time() + 2.0
    while time.time() < deadline:
        if desktop_health():
            return
        time.sleep(0.1)


def start_desktop_interactive() -> dict[str, Any]:
    """Explicit start from HTTP/UI.

    Always tries to spawn (ignores ``QWENPAW_PET_AUTOSTART``). Returns
    a JSON-friendly dict so the console can show *why* start failed.
    """
    health = desktop_health()
    if health and health.get("ok"):
        return {
            "ok": True,
            "alreadyRunning": True,
            "launchAttempted": False,
            "desktop": health,
            "message": "Desktop pet is already running.",
        }

    ok, hint = _spawn_desktop_background()
    if not ok:
        return {
            "ok": True,
            "alreadyRunning": False,
            "launchAttempted": False,
            "desktop": desktop_health(),
            "message": hint or "Could not start the desktop pet process.",
            "hint": _MISSING_DEPS_HINT,
        }

    deadline = time.time() + 3.0
    while time.time() < deadline:
        h = desktop_health()
        if h and h.get("ok"):
            return {
                "ok": True,
                "alreadyRunning": False,
                "launchAttempted": True,
                "desktop": h,
                "message": "Desktop pet started.",
            }
        time.sleep(0.12)

    return {
        "ok": True,
        "alreadyRunning": False,
        "launchAttempted": True,
        "desktop": desktop_health(),
        "message": (
            "A desktop process was spawned but /health is not ready yet "
            "(it may still be starting, or it exited immediately)."
        ),
        "hint": (
            "See log file under QwenPaw pet runtime "
            "(often ~/.qwenpaw-pet/runtime/pet-desktop.log)."
        ),
    }


def schedule_emit_pet_event(event: str, **payload: Any) -> None:
    """Notify desktop from async QwenPaw code without blocking the event loop.

    Calling sync ``httpx`` inside an ``async def`` blocks the entire asyncio
    runner (including the request that is waiting on tool approval).
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        emit_pet_event(event, **payload)
        return

    async def _run() -> None:
        await asyncio.to_thread(
            functools.partial(emit_pet_event, event, **payload),
        )

    task = loop.create_task(_run())

    def _done(t: asyncio.Task) -> None:
        try:
            t.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.warning(
                "schedule_emit_pet_event task failed",
                exc_info=True,
            )

    task.add_done_callback(_done)


def emit_pet_event(event: str, **payload: Any) -> None:
    """Send a lifecycle event to QwenPaw Pet Desktop.

    This function is intentionally fire-and-forget: short timeout, no
    exception escapes into QwenPaw's main request path.
    """
    state = payload.pop("state", None) or EVENT_TO_STATE.get(event, "idle")
    body = {
        "event": event,
        "state": state,
        "source": "qwenpaw",
        **payload,
    }
    try:
        response = httpx.post(
            f"{DESKTOP_URL}/event",
            json=body,
            headers=_headers(),
            **_httpx_client_kwargs(),
        )
        if response.status_code >= 400:
            logger.warning(
                "QwenPaw Pet Desktop POST /event HTTP %s "
                "event=%s detail=%s",
                response.status_code,
                event,
                (response.text or "")[:200],
            )
    except Exception:
        logger.warning("QwenPaw Pet Desktop POST /event failed", exc_info=True)


def switch_pet_desktop(
    *,
    pet_dir: str | None = None,
    pet_id: str | None = None,
) -> dict[str, Any]:
    """Hot-switch the running pet via ``POST /pet`` (no desktop restart)."""
    body: dict[str, str] = {}
    if pet_dir and str(pet_dir).strip():
        body["pet_dir"] = str(pet_dir).strip()
    elif pet_id and str(pet_id).strip():
        body["pet_id"] = str(pet_id).strip()
    else:
        return {"ok": False, "error": "missing pet_dir or pet_id"}
    client_kw = dict(_httpx_client_kwargs())
    client_kw["timeout"] = 3.0
    try:
        response = httpx.post(
            f"{DESKTOP_URL}/pet",
            json=body,
            headers=_headers(),
            **client_kw,
        )
        try:
            data = response.json()
        except Exception:
            data = {"ok": response.is_success}
        if not isinstance(data, dict):
            data = {"ok": response.is_success}
        if response.status_code >= 400:
            logger.warning(
                "QwenPaw Pet Desktop POST /pet HTTP %s detail=%s",
                response.status_code,
                (response.text or "")[:300],
            )
        return data
    except Exception as exc:
        logger.warning("QwenPaw Pet Desktop POST /pet failed: %s", exc)
        return {"ok": False, "error": str(exc)}
