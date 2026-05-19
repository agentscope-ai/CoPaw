# -*- coding: utf-8 -*-
"""Fork subagent API endpoint.

POST /fork/agent — prepare a forked session + git worktree for spawn_subagent.
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config.config import load_agent_config
from ..runner.session import sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fork", tags=["fork"])

_WORKTREE_BASE = ".qwenpaw/worktrees"


class ForkAgentRequest(BaseModel):
    agent_id: str
    parent_session_id: str
    user_id: Optional[str] = None
    channel: Optional[str] = None


class ForkAgentResponse(BaseModel):
    fork_session_id: str
    worktree_path: str
    worktree_branch: str


def _get_agent_workspace(agent_id: str) -> Path:
    """Resolve the workspace directory for *agent_id*."""
    try:
        config = load_agent_config(agent_id)
        return Path(config.workspace_dir).expanduser().resolve()
    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found or config unreadable: {exc}",
        ) from exc


def _session_path(
    sessions_dir: Path,
    session_id: str,
    user_id: Optional[str],
    channel: Optional[str],
) -> Path:
    """Reconstruct the session file path used by SafeJSONSession."""
    safe_sid = sanitize_filename(session_id)
    safe_uid = sanitize_filename(user_id) if user_id else ""
    filename = (
        f"{safe_uid}_{safe_sid}.json" if safe_uid else f"{safe_sid}.json"
    )

    if channel:
        safe_channel = sanitize_filename(channel)
        return sessions_dir / safe_channel / filename
    return sessions_dir / filename


def _read_session_history(session_file: Path) -> list:
    """Read message history from a session JSON file (full copy)."""
    if not session_file.exists():
        return []
    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
        return data.get("messages", [])
    except Exception as exc:
        logger.warning("Failed to read session file %s: %s", session_file, exc)
        return []


def _write_fork_session(
    sessions_dir: Path,
    fork_session_id: str,
    messages: list,
) -> None:
    """Write pre-seeded history into a new fork session file."""
    safe_sid = sanitize_filename(fork_session_id)
    fork_file = sessions_dir / f"{safe_sid}.json"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    fork_file.write_text(
        json.dumps({"messages": messages}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "Fork session written: %s (%d messages)",
        fork_file,
        len(messages),
    )


def _create_worktree(workspace: Path, worktree_id: str) -> tuple[Path, str]:
    """Create a git worktree at <workspace>/.qwenpaw/worktrees/<id>.

    Returns (worktree_path, branch_name).
    """
    branch = f"fork/{worktree_id}"
    worktree_path = workspace / _WORKTREE_BASE / worktree_id
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Created worktree: %s branch=%s", worktree_path, branch)
        logger.debug("git worktree output: %s", result.stdout)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"git worktree add failed: {exc.stderr.strip()}",
        ) from exc

    _copy_worktreeinclude_files(workspace, worktree_path)
    return worktree_path, branch


def _copy_worktreeinclude_files(src: Path, dst: Path) -> None:
    """Copy files listed in .worktreeinclude (like .env) into the worktree."""
    include_file = src / ".worktreeinclude"
    if not include_file.exists():
        return

    for line in include_file.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        src_file = src / name
        dst_file = dst / name
        if src_file.exists():
            try:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                import shutil

                shutil.copy2(str(src_file), str(dst_file))
                logger.debug("Copied %s → %s", src_file, dst_file)
            except OSError as exc:
                logger.warning("Failed to copy %s: %s", src_file, exc)


@router.post("/agent", response_model=ForkAgentResponse)
async def fork_agent(req: ForkAgentRequest) -> ForkAgentResponse:
    """Prepare a forked subagent: copy session history + create worktree.

    This endpoint is called internally by ``spawn_subagent(fork=True)``
    in the tool layer. It does NOT start the subagent — the caller is
    responsible for dispatching the request after receiving the fork metadata.

    Steps:
    1. Resolve agent workspace from config.
    2. Read parent session file (full history copy).
    3. Write fork session file pre-seeded with parent history.
    4. ``git worktree add`` at ``<workspace>/.qwenpaw/worktrees/<id>``.
    5. Copy ``.worktreeinclude`` files (e.g. ``.env``) into the worktree.

    Returns fork_session_id, worktree_path, worktree_branch.
    """
    workspace = _get_agent_workspace(req.agent_id)
    sessions_dir = workspace / "sessions"

    parent_file = _session_path(
        sessions_dir,
        req.parent_session_id,
        req.user_id,
        req.channel,
    )
    history = _read_session_history(parent_file)

    fork_id = str(uuid4())[:8]
    fork_session_id = f"sub-{fork_id}"

    _write_fork_session(sessions_dir, fork_session_id, history)

    worktree_path, worktree_branch = _create_worktree(workspace, fork_id)

    return ForkAgentResponse(
        fork_session_id=fork_session_id,
        worktree_path=str(worktree_path),
        worktree_branch=worktree_branch,
    )
