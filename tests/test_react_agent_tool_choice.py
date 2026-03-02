# -*- coding: utf-8 -*-
import pytest
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.tool import Toolkit

from copaw.agents.react_agent import CoPawAgent


def _dummy_tool() -> str:
    """Dummy tool for testing tool schema presence."""
    return "ok"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("register_tool", "tool_choice_in", "expected"),
    [
        (True, None, "auto"),
        (False, None, None),
        (True, "required", "required"),
        (True, "none", "none"),
    ],
)
async def test_reasoning_tool_choice_fallback(
    monkeypatch: pytest.MonkeyPatch,
    register_tool: bool,
    tool_choice_in: str | None,
    expected: str | None,
) -> None:
    captured: dict[str, str | None] = {"tool_choice": None}

    async def _fake_parent_reasoning(
        self,
        tool_choice: str | None = None,
    ) -> Msg:
        captured["tool_choice"] = tool_choice
        return Msg("assistant", "ok", "assistant")

    monkeypatch.setattr(ReActAgent, "_reasoning", _fake_parent_reasoning)

    agent = CoPawAgent.__new__(CoPawAgent)
    object.__setattr__(agent, "_module_dict", {})
    agent.toolkit = Toolkit()
    if register_tool:
        agent.toolkit.register_tool_function(_dummy_tool)

    msg = await CoPawAgent._reasoning.__wrapped__(  # type: ignore[attr-defined]
        agent,
        tool_choice=tool_choice_in,
    )
    assert msg.get_text_content() == "ok"
    assert captured["tool_choice"] == expected
