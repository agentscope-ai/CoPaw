# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib

import pytest
from agentscope.message import Msg, TextBlock

from qwenpaw.app.goal_dispatch import handle_goal_command


def _assistant_msg(text: str) -> Msg:
    return Msg(
        name="QwenPaw",
        role="assistant",
        content=[TextBlock(type="text", text=text)],
    )


@pytest.mark.asyncio
async def test_goal_loop_continues_until_achieved(tmp_path, monkeypatch):
    runner_mod = importlib.import_module("qwenpaw.app.runner.runner")
    responses = [
        "I made progress but still need to verify tests.",
        "Tests pass now.\nGoal status: achieved",
    ]

    class FakeAgent:
        def __init__(self):
            self.calls = []

        async def __call__(self, msgs):
            self.calls.append(msgs)
            return _assistant_msg("unused")

    async def fake_stream(*, agents, coroutine_task):
        _ = agents
        await coroutine_task
        yield _assistant_msg(responses.pop(0)), True

    monkeypatch.setattr(
        runner_mod,
        "_stream_printing_messages_interruptible",
        fake_stream,
    )

    goal = await handle_goal_command(
        "/goal Fix the retry test",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )
    assert isinstance(goal, dict)

    agent = FakeAgent()
    initial_msgs = [
        Msg(
            name="user",
            role="user",
            content=[TextBlock(type="text", text="Fix the retry test")],
        ),
    ]

    streamed = []
    # pylint: disable-next=protected-access
    async for item in runner_mod._stream_goal_auto_continuation(
        agent=agent,
        initial_msgs=initial_msgs,
        goal_info=goal,
    ):
        streamed.append(item)

    assert [last for _, last in streamed] == [False, True]
    assert len(agent.calls) == 2
    continuation_text = agent.calls[1][0].get_text_content()
    assert "[Goal continuation]" in continuation_text
    assert "Objective: Fix the retry test" in continuation_text
