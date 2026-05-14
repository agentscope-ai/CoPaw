# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

from types import SimpleNamespace

import pytest
from agentscope.message import Msg

from qwenpaw.agents.react_agent import QwenPawAgent
from qwenpaw.agents.tool_guard_mixin import ToolGuardMixin


class _MemoryRecorder:
    def __init__(self) -> None:
        self.added: list[tuple[Msg, object]] = []

    async def add(self, msg: Msg, marks=None) -> None:
        self.added.append((msg, marks))


def _make_agent() -> QwenPawAgent:
    agent = object.__new__(QwenPawAgent)
    agent._agent_config = SimpleNamespace(
        language="en",
        running=SimpleNamespace(auto_continue_on_text_only=True),
    )
    agent.memory = _MemoryRecorder()
    agent.plan_notebook = None
    return agent


@pytest.mark.asyncio
async def test_auto_continue_replaces_thinking_only_with_visible_text(
    monkeypatch,
) -> None:
    agent = _make_agent()
    thinking_only = Msg(
        "assistant",
        [{"type": "thinking", "thinking": "I should answer now."}],
        "assistant",
    )
    visible_answer = Msg("assistant", "Done.", "assistant")

    async def fake_reasoning(
        self,
        tool_choice=None,
    ):  # pylint: disable=unused-argument
        return visible_answer

    monkeypatch.setattr(ToolGuardMixin, "_reasoning", fake_reasoning)

    result = await agent._auto_continue_if_text_only(thinking_only, "auto")

    assert result is visible_answer
    assert "no user-visible text answer" in agent.memory.added[0][0].content


@pytest.mark.asyncio
async def test_auto_continue_keeps_original_visible_text_on_text_retry(
    monkeypatch,
) -> None:
    agent = _make_agent()
    original_answer = Msg("assistant", "First answer.", "assistant")
    retry_answer = Msg("assistant", "Second answer.", "assistant")

    async def fake_reasoning(
        self,
        tool_choice=None,
    ):  # pylint: disable=unused-argument
        return retry_answer

    monkeypatch.setattr(ToolGuardMixin, "_reasoning", fake_reasoning)

    result = await agent._auto_continue_if_text_only(original_answer, "auto")

    assert result is original_answer
    assert "previous assistant turn had text only" in (
        agent.memory.added[0][0].content
    )
