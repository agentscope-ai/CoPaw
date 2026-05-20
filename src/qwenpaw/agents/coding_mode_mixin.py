# -*- coding: utf-8 -*-
"""Coding Mode mixin for QwenPawAgent.

Provides two behaviours activated when ``coding_mode.enabled`` is
``True`` in the agent configuration:

1. **System Prompt Injection** — appends a coding-focused persona
   and workflow guidelines to the agent system prompt.

2. **TodoWrite post-hook** — after ``todo_write`` executes, reads the
   updated task list and emits a ``todo_update`` SSE event so the
   frontend can display real-time task progress.
"""
from __future__ import annotations

import json as _json
import logging
from pathlib import Path

from agentscope.message import Msg, TextBlock

logger = logging.getLogger(__name__)


_CODING_SYSTEM_PROMPT_TEMPLATE = """\
## Coding Mode

You are currently operating in **Coding Mode**.  The user is working inside \
the code workspace at: `{workspace_dir}`

### Working guidelines
1. **Break large tasks down** — use `todo_write` for any task with more than \
two steps so the user can track progress in real time.
2. **Read before you write** — always read the relevant file(s) first.
3. **Prefer targeted edits** — use `edit_file` over full-file rewrites \
whenever possible.
4. **Announce changes** — before modifying a file, state the file path and \
the intent in plain language.
5. **Summarise after each batch** — briefly note what was done and what \
remains.

Keep reasoning concise.  Prefer small, verifiable steps over large monolithic \
changes.
"""


class CodingModeMixin:
    """Mixin that adds Coding Mode features to a ReActAgent.

    At runtime this class is mixed into ``QwenPawAgent`` and always
    combined with ``ToolGuardMixin`` and ``ReActAgent`` via MRO, so
    ``super()._acting`` resolves through the whole chain.
    """

    # ------------------------------------------------------------------
    # System prompt injection
    # ------------------------------------------------------------------

    def _build_sys_prompt(self) -> str:  # noqa: D102
        """Append the Coding Mode persona block to the base system prompt."""
        base: str = super()._build_sys_prompt()  # type: ignore[misc]
        if not self._coding_mode_enabled():
            return base
        workspace_dir = str(getattr(self, "_workspace_dir", ""))
        coding_block = _CODING_SYSTEM_PROMPT_TEMPLATE.format(
            workspace_dir=workspace_dir or "(unknown)",
        )
        return base + "\n\n" + coding_block

    # ------------------------------------------------------------------
    # Helpers: config access
    # ------------------------------------------------------------------

    def _coding_mode_enabled(self) -> bool:
        """Return ``True`` when Coding Mode is active."""
        agent_config = getattr(self, "_agent_config", None)
        if agent_config is None:
            return False
        if isinstance(agent_config, dict):
            cm = agent_config.get("coding_mode") or {}
            return bool(cm.get("enabled", False))
        cm = getattr(agent_config, "coding_mode", None)
        if cm is None:
            return False
        return bool(getattr(cm, "enabled", False))

    # ------------------------------------------------------------------
    # _acting override
    # ------------------------------------------------------------------

    async def _acting(  # type: ignore[override]
        self,
        tool_call: dict,
    ) -> dict | None:
        """Post-hook: emit todo_update after todo_write executes.

        Args:
            tool_call: AgentScope tool call dict with ``name`` and
                ``input`` keys.

        Returns:
            Tool result dict or ``None``.
        """
        tool_name = str(tool_call.get("name", ""))

        outcome = await super()._acting(tool_call)  # type: ignore[misc]

        if tool_name == "todo_write" and self._coding_mode_enabled():
            await self._emit_todo_update()

        return outcome

    # ------------------------------------------------------------------
    # SSE event emitters
    # ------------------------------------------------------------------

    async def _emit_todo_update(self) -> None:
        """Read current todos from disk and emit a todo_update SSE event.

        Called after every successful ``todo_write`` execution.
        """
        from ..config.context import (
            get_current_workspace_dir,
            get_current_session_id,
        )
        from .tools.todo import _todos_path, _load_todos

        workspace_dir = get_current_workspace_dir()
        session_id = get_current_session_id()
        if workspace_dir is None or not session_id:
            return

        path = _todos_path(Path(workspace_dir), session_id)
        todos = await _load_todos(path)

        msg = Msg(
            self.name,  # type: ignore[attr-defined]
            [
                TextBlock(
                    type="text",
                    text=_json.dumps(todos, ensure_ascii=False),
                ),
            ],
            "assistant",
            metadata={
                "message_type": "todo_update",
                "todos": todos,
            },
        )
        await self.print(msg, True)  # type: ignore[attr-defined]
