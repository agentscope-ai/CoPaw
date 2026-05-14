# -*- coding: utf-8 -*-
"""Watch agent.json and trigger a graceful workspace reload on change.

Delegates to ``MultiAgentManager.reload_agent`` so disk-edit reloads
go through the same atomic workspace swap as frontend saves and wait
for in-flight tasks. Only triggers when runtime-affecting sections
change, so runtime bookkeeping rewrites (e.g. ``last_dispatch``) do not
cause spurious reloads.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

from ..config.config import load_agent_config

if TYPE_CHECKING:
    from ..config.config import HeartbeatConfig
    from .workspace.workspace import Workspace

logger = logging.getLogger(__name__)

# How often to poll (seconds)
DEFAULT_POLL_INTERVAL = 2.0


def _to_jsonable(value: Any) -> Any:
    """Return a JSON-serializable representation for stable hashing."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _to_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


def _section_hash(value: Any) -> Optional[int]:
    """Hash a config section after normalizing key order and models."""
    if value is None:
        return None
    normalized = json.dumps(
        _to_jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hash(normalized)


def _channels_hash(channels: Any) -> Optional[int]:
    """Hash of channels section for change detection."""
    return _section_hash(channels)


def _heartbeat_hash(hb: Optional["HeartbeatConfig"]) -> Optional[int]:
    """Hash of heartbeat config for change detection."""
    return _section_hash(hb)


def _mcp_hash(mcp: Any) -> Optional[int]:
    """Hash of MCP clients for change detection."""
    if mcp is None:
        return None
    return _section_hash(getattr(mcp, "clients", None))


def _skill_manifest_hash(manifest_path: Path) -> Optional[int]:
    """Hash of workspace skill manifest for change detection."""
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = raw
    return _section_hash(payload)


class AgentConfigWatcher:
    """Poll ``agent.json`` and trigger a graceful workspace reload."""

    def __init__(
        self,
        agent_id: str,
        workspace_dir: Path,
        workspace: "Workspace",
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ):
        """Initialize agent config watcher.

        Args:
            agent_id: Agent ID to monitor.
            workspace_dir: Path to agent's workspace directory.
            workspace: Owning ``Workspace`` instance. The manager is
                resolved lazily from it, since ``set_manager`` runs
                after ``Workspace.start()``.
            poll_interval: How often to check for changes (seconds).
        """
        self._agent_id = agent_id
        self._workspace_dir = workspace_dir
        self._config_path = workspace_dir / "agent.json"
        self._skill_manifest_path = workspace_dir / "skill.json"
        self._workspace = workspace
        self._poll_interval = poll_interval
        self._task: Optional[asyncio.Task] = None

        self._last_mtime: tuple[float, float] = (0.0, 0.0)
        self._last_channels_hash: Optional[int] = None
        self._last_heartbeat_hash: Optional[int] = None
        self._last_mcp_hash: Optional[int] = None
        self._last_skill_manifest_hash: Optional[int] = None

        # Set before triggering reload; poll loop checks this to stop.
        self._disabled: bool = False

    async def start(self) -> None:
        """Take initial snapshot and start the polling task."""
        self._snapshot()
        self._task = asyncio.create_task(
            self._poll_loop(),
            name=f"agent_config_watcher_{self._agent_id}",
        )
        logger.info(
            f"AgentConfigWatcher started for agent {self._agent_id} "
            f"(poll={self._poll_interval}s, path={self._config_path})",
        )

    async def stop(self) -> None:
        """Stop the polling task (no-op if already disabled)."""
        if self._disabled:
            logger.info(
                f"AgentConfigWatcher already disabled for agent "
                f"{self._agent_id}, skipping cancel",
            )
            return
        self._disabled = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info(f"AgentConfigWatcher stopped for agent {self._agent_id}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _path_mtime(path: Path) -> float:
        """Return current mtime of a path, 0.0 if missing."""
        try:
            return path.stat().st_mtime
        except FileNotFoundError:
            return 0.0

    def _read_mtime(self) -> tuple[float, float]:
        """Return current mtimes of agent.json and skill.json."""
        return (
            self._path_mtime(self._config_path),
            self._path_mtime(self._skill_manifest_path),
        )

    def _snapshot(self) -> None:
        """Record current mtime and section hashes as the new baseline."""
        self._last_mtime = self._read_mtime()
        try:
            agent_config = load_agent_config(self._agent_id)
        except Exception:
            logger.exception(
                f"AgentConfigWatcher ({self._agent_id}): "
                f"failed to load initial config",
            )
            return
        self._last_channels_hash = _channels_hash(
            getattr(agent_config, "channels", None),
        )
        self._last_heartbeat_hash = _heartbeat_hash(
            getattr(agent_config, "heartbeat", None),
        )
        self._last_mcp_hash = _mcp_hash(
            getattr(agent_config, "mcp", None),
        )
        self._last_skill_manifest_hash = _skill_manifest_hash(
            self._skill_manifest_path,
        )

    def _resolve_manager(self):
        """Return ``MultiAgentManager`` from the workspace, or ``None``."""
        # pylint: disable=protected-access
        return getattr(self._workspace, "_manager", None)

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while not self._disabled:
            try:
                await asyncio.sleep(self._poll_interval)
                if self._disabled:
                    break
                await self._check()
            except Exception:
                logger.exception(
                    f"AgentConfigWatcher ({self._agent_id}): "
                    f"poll iteration failed",
                )

    async def _check(self) -> None:
        """Check for meaningful config changes and trigger a reload."""
        mtime = self._read_mtime()
        if mtime == self._last_mtime:
            return
        self._last_mtime = mtime

        try:
            agent_config = load_agent_config(self._agent_id)
        except Exception:
            logger.exception(
                f"AgentConfigWatcher ({self._agent_id}): "
                f"failed to parse agent.json",
            )
            return

        new_channels_hash = _channels_hash(
            getattr(agent_config, "channels", None),
        )
        new_heartbeat_hash = _heartbeat_hash(
            getattr(agent_config, "heartbeat", None),
        )
        new_mcp_hash = _mcp_hash(
            getattr(agent_config, "mcp", None),
        )
        new_skill_manifest_hash = _skill_manifest_hash(
            self._skill_manifest_path,
        )

        old_channels_hash = self._last_channels_hash
        old_heartbeat_hash = self._last_heartbeat_hash
        old_mcp_hash = self._last_mcp_hash
        old_skill_manifest_hash = self._last_skill_manifest_hash

        changed = (
            new_channels_hash != old_channels_hash
            or new_heartbeat_hash != old_heartbeat_hash
            or new_mcp_hash != old_mcp_hash
            or new_skill_manifest_hash != old_skill_manifest_hash
        )

        # Refresh hashes regardless so non-meaningful rewrites
        # (e.g. last_dispatch) re-baseline silently.
        self._last_channels_hash = new_channels_hash
        self._last_heartbeat_hash = new_heartbeat_hash
        self._last_mcp_hash = new_mcp_hash
        self._last_skill_manifest_hash = new_skill_manifest_hash

        if not changed:
            return

        manager = self._resolve_manager()
        if manager is None:
            logger.warning(
                f"AgentConfigWatcher ({self._agent_id}): "
                f"config changed but MultiAgentManager not attached; "
                f"skipping reload",
            )
            return

        self._disabled = True

        logger.info(
            f"AgentConfigWatcher ({self._agent_id}): "
            f"config changed, triggering graceful reload "
            f"(channels: {old_channels_hash} -> {new_channels_hash}, "
            f"heartbeat: {old_heartbeat_hash} -> {new_heartbeat_hash}, "
            f"mcp: {old_mcp_hash} -> {new_mcp_hash}, "
            f"skills: {old_skill_manifest_hash} -> "
            f"{new_skill_manifest_hash})",
        )
        try:
            await manager.reload_agent(self._agent_id)
        except Exception:
            logger.exception(
                f"AgentConfigWatcher ({self._agent_id}): "
                f"reload_agent failed",
            )
