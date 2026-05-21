# -*- coding: utf-8 -*-
"""Goal mode dispatch for lightweight, session-scoped objectives.

Goal mode is intentionally smaller than Mission Mode:

- it stores one active objective per channel/user/session;
- it keeps execution on the normal main-agent path;
- it does not create workers, PRDs, or bypass tool approvals.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentscope.message import Msg, TextBlock

logger = logging.getLogger(__name__)

GOAL_COMMAND = "/goal"
GOAL_STATUS_ACTIVE = "active"
GOAL_STATUS_PAUSED = "paused"
GOAL_STATUS_ACHIEVED = "achieved"
DEFAULT_GOAL_MAX_TURNS = 5

_GOAL_MIN_LEN = 5
_GOAL_DONE_RE = re.compile(
    r"(?im)^\s*(goal status:\s*achieved|\[goal:\s*achieved\])\s*$",
)
_GOAL_PAUSED_RE = re.compile(
    r"(?im)^\s*(goal status:\s*paused|\[goal:\s*paused\])\s*$",
)
_UNSAFE_FILENAME_RE = re.compile(r'[\\/:*?"<>|]')


def _sanitize_filename(name: str) -> str:
    """Replace characters that are illegal in cross-platform filenames."""
    return _UNSAFE_FILENAME_RE.sub("--", name)


def is_goal_command(query: str | None) -> bool:
    """Return True if *query* starts with the goal command token."""
    if not query or not isinstance(query, str):
        return False
    token = query.strip().split(None, 1)[0].lower()
    return token == GOAL_COMMAND


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _goal_dir(workspace_dir: Path, channel: str = "") -> Path:
    root = workspace_dir / "goals"
    if channel:
        root = root / _sanitize_filename(channel)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _goal_path(
    workspace_dir: Path,
    session_id: str,
    user_id: str = "",
    channel: str = "",
) -> Path:
    safe_sid = _sanitize_filename(session_id or "default")
    safe_uid = _sanitize_filename(user_id) if user_id else ""
    filename = (
        f"{safe_uid}_{safe_sid}.json" if safe_uid else f"{safe_sid}.json"
    )
    return _goal_dir(workspace_dir, channel) / filename


def _read_goal(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        logger.warning(
            "Failed to read goal state from %s",
            path,
            exc_info=True,
        )
    return None


def _write_goal(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp_path, path)


def _delete_goal(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _usage() -> str:
    return (
        "**Goal Mode**\n\n"
        "Usage:\n"
        "- `/goal <objective>` - set a lightweight standing objective\n"
        "- `/goal status` - show the current goal\n"
        "- `/goal pause` - pause goal injection\n"
        "- `/goal resume` - resume a paused goal\n"
        "- `/goal clear` - remove the current goal\n\n"
        "Goal Mode keeps using the main agent and the normal tool "
        "approval flow. It does not create Mission workers or PRD files."
    )


def _format_status(state: dict[str, Any] | None, path: Path) -> str:
    if not state:
        return (
            "**Goal Status**: No goal is set for this session.\n\n"
            "Use `/goal <objective>` to start one."
        )

    max_turns = _goal_max_turns(state)
    lines = [
        "**Goal Status**",
        f"- Status: `{state.get('status', 'unknown')}`",
        f"- Objective: {state.get('objective', '')}",
        f"- Attempts: {state.get('attempts', 0)}/{max_turns}",
        f"- Updated: `{state.get('updated_at', '')}`",
        f"- State file: `{path}`",
    ]
    last_result = state.get("last_result")
    if last_result:
        lines.append(f"- Last result: {last_result}")
    paused_reason = state.get("paused_reason")
    if paused_reason:
        lines.append(f"- Paused reason: {paused_reason}")
    return "\n".join(lines)


def _goal_max_turns(state: dict[str, Any] | None) -> int:
    if not state:
        return DEFAULT_GOAL_MAX_TURNS
    try:
        max_turns = int(state.get("max_turns") or DEFAULT_GOAL_MAX_TURNS)
    except (TypeError, ValueError):
        return DEFAULT_GOAL_MAX_TURNS
    return max(max_turns, 1)


def _new_goal_state(
    *,
    objective: str,
    session_id: str,
    user_id: str,
    channel: str,
) -> dict[str, Any]:
    now = _utc_now()
    return {
        "version": 1,
        "objective": objective,
        "status": GOAL_STATUS_ACTIVE,
        "created_at": now,
        "updated_at": now,
        "session_id": session_id,
        "user_id": user_id,
        "channel": channel,
        "attempts": 0,
        "max_turns": DEFAULT_GOAL_MAX_TURNS,
        "last_result": "",
        "last_response_excerpt": "",
        "paused_reason": "",
    }


async def handle_goal_command(  # pylint: disable=too-many-return-statements
    query: str,
    workspace_dir: Path,
    session_id: str = "",
    user_id: str = "",
    channel: str = "",
) -> str | dict[str, Any]:
    """Process a ``/goal`` command.

    Returns display text for subcommands, or a goal state dict when the
    caller should continue through the normal agent path.
    """
    parts = query.strip().split(None, 1)
    raw_arg = parts[1].strip() if len(parts) > 1 else ""
    subcommand = raw_arg.lower()
    path = _goal_path(workspace_dir, session_id, user_id, channel)

    if not raw_arg or subcommand == "help":
        return _usage()

    if subcommand == "status":
        return _format_status(_read_goal(path), path)

    if subcommand == "clear":
        existed = path.exists()
        _delete_goal(path)
        if existed:
            return "**Goal Cleared**: Removed the current session goal."
        return "**Goal Cleared**: No goal was set for this session."

    if subcommand in {"pause", "resume"}:
        state = _read_goal(path)
        if not state:
            return (
                "**Goal Status**: No goal is set for this session.\n\n"
                "Use `/goal <objective>` to start one."
            )
        state["status"] = (
            GOAL_STATUS_PAUSED if subcommand == "pause" else GOAL_STATUS_ACTIVE
        )
        if subcommand == "pause":
            state["paused_reason"] = "user-paused"
        else:
            state["paused_reason"] = ""
        state["updated_at"] = _utc_now()
        _write_goal(path, state)
        return _format_status(state, path)

    objective = raw_arg
    if len(objective.strip()) < _GOAL_MIN_LEN:
        return (
            "**Goal Mode**\n\n"
            "Please provide a more specific objective, for example:\n"
            "`/goal Finish the retry handling patch and verify tests`"
        )

    state = _new_goal_state(
        objective=objective,
        session_id=session_id,
        user_id=user_id,
        channel=channel,
    )
    _write_goal(path, state)
    state["_goal_path"] = str(path)
    state["_goal_started"] = True
    return state


async def maybe_handle_goal_command(
    query: str | None,
    workspace_dir: Path,
    session_id: str = "",
    user_id: str = "",
    channel: str = "",
    agent_name: str = "QwenPaw",
) -> Msg | dict[str, Any] | None:
    """Handle ``/goal`` if the query matches."""
    if not query or not is_goal_command(query):
        return None

    result = await handle_goal_command(
        query=query,
        workspace_dir=workspace_dir,
        session_id=session_id,
        user_id=user_id,
        channel=channel,
    )

    if isinstance(result, str):
        return Msg(
            name=agent_name,
            role="assistant",
            content=[TextBlock(type="text", text=result)],
        )

    return result


def detect_active_goal(
    workspace_dir: Path,
    session_id: str = "",
    user_id: str = "",
    channel: str = "",
) -> dict[str, Any] | None:
    """Return the active goal state for the current session, if any."""
    path = _goal_path(workspace_dir, session_id, user_id, channel)
    state = _read_goal(path)
    if not state or state.get("status") != GOAL_STATUS_ACTIVE:
        return None
    state["_goal_path"] = str(path)
    return state


def build_goal_refresher(
    goal_info: dict[str, Any],
    user_text: str,
) -> str:
    """Build the prompt prefix injected into the normal agent turn."""
    objective = goal_info.get("objective", "")
    state_path = goal_info.get("_goal_path", "")
    attempts = int(goal_info.get("attempts", 0) or 0)
    max_turns = _goal_max_turns(goal_info)
    started = bool(goal_info.get("_goal_started"))
    action = (
        "The user just started this goal. Begin working on it now."
        if started
        else "A goal is active for this session. Keep making progress on it."
    )
    cleaned_user_text = user_text.strip()
    if started and cleaned_user_text.lower().startswith(GOAL_COMMAND):
        cleaned_user_text = objective

    return (
        "[Goal active]\n"
        f"Objective: {objective}\n"
        f"State file: `{state_path}`\n"
        f"Turn budget: {attempts}/{max_turns} completed\n"
        f"{action}\n\n"
        "Constraints:\n"
        "- Use the normal main-agent tools and approval flow.\n"
        "- Do not create Mission workers, PRD files, or background agents "
        "unless the user explicitly asks.\n"
        "- If the objective is fully achieved in this turn, include a final "
        "line exactly: `Goal status: achieved`.\n"
        "- If you are blocked and need the user to answer or approve a "
        "choice, include a final line exactly: `Goal status: paused`.\n\n"
        "User message:\n"
        f"{cleaned_user_text}"
    )


def build_goal_continuation(goal_info: dict[str, Any]) -> str:
    """Build the next automatic goal turn prompt."""
    objective = goal_info.get("objective", "")
    state_path = goal_info.get("_goal_path", "")
    attempts = int(goal_info.get("attempts", 0) or 0)
    max_turns = _goal_max_turns(goal_info)
    last_result = goal_info.get("last_result", "") or "in_progress"
    excerpt = (goal_info.get("last_response_excerpt", "") or "").strip()
    previous = f"Previous response excerpt:\n{excerpt}\n\n" if excerpt else ""

    return (
        "[Goal continuation]\n"
        f"Objective: {objective}\n"
        f"State file: `{state_path}`\n"
        f"Turn budget: {attempts}/{max_turns} completed\n"
        f"Last result: {last_result}\n\n"
        f"{previous}"
        "Continue working toward this goal. Take the next concrete step "
        "using the normal main-agent tools and approval flow. Do not create "
        "Mission workers, PRD files, or background agents unless the user "
        "explicitly asks.\n\n"
        "If the objective is fully achieved in this turn, include a final "
        "line exactly: `Goal status: achieved`.\n"
        "If you are blocked and need the user to answer or approve a choice, "
        "include a final line exactly: `Goal status: paused`."
    )


def should_continue_goal(goal_info: dict[str, Any] | None) -> bool:
    """Return True when another automatic goal turn should be launched."""
    if not goal_info:
        return False
    return goal_info.get("status") == GOAL_STATUS_ACTIVE


def _msg_text(msg: Any) -> str:
    if msg is None:
        return ""
    if hasattr(msg, "get_text_content"):
        text = msg.get_text_content()
        return text if isinstance(text, str) else ""
    content = getattr(msg, "content", None)
    if isinstance(msg, dict):
        content = msg.get("content") or msg.get("text")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
            else:
                text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "\n".join(parts)
    return ""


def update_goal_from_message(
    goal_info: dict[str, Any] | None,
    assistant_msg: Any,
) -> dict[str, Any] | None:
    """Persist a lightweight progress update from the final assistant msg."""
    if not goal_info:
        return None
    path_value = goal_info.get("_goal_path")
    if not path_value:
        return None
    path = Path(path_value)
    state = _read_goal(path)
    if not state:
        return None

    text = _msg_text(assistant_msg).strip()
    state["attempts"] = int(state.get("attempts", 0) or 0) + 1
    state["updated_at"] = _utc_now()
    state["last_response_excerpt"] = text[:500]
    if _GOAL_DONE_RE.search(text):
        state["status"] = GOAL_STATUS_ACHIEVED
        state["last_result"] = "achieved"
        state["paused_reason"] = ""
    elif _GOAL_PAUSED_RE.search(text):
        state["status"] = GOAL_STATUS_PAUSED
        state["last_result"] = "paused"
        state["paused_reason"] = "model-requested-user-input"
    elif state["attempts"] >= _goal_max_turns(state):
        state["status"] = GOAL_STATUS_PAUSED
        state["last_result"] = "turn_budget_exhausted"
        state["paused_reason"] = (
            f"turn budget exhausted ({state['attempts']}/"
            f"{_goal_max_turns(state)})"
        )
    else:
        state["last_result"] = "in_progress"
        state["paused_reason"] = ""
    state.pop("_goal_path", None)
    _write_goal(path, state)
    state["_goal_path"] = str(path)
    return state
