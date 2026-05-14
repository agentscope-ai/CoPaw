# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

from qwenpaw.providers.retry_chat_model import _inject_reasoning_content


def test_inject_reasoning_content_preserves_thinking_block() -> None:
    messages = [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "thinking",
                    "thinking": "Need to inspect memory before answering.",
                },
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "memory_search",
                    "input": {"query": "preferences"},
                },
            ],
        },
    ]

    assert _inject_reasoning_content((), {"messages": messages})
    assert (
        messages[0]["reasoning_content"]
        == "Need to inspect memory before answering."
    )


def test_inject_reasoning_content_uses_placeholder_without_thinking() -> None:
    messages = [{"role": "assistant", "content": "Plain response"}]

    assert _inject_reasoning_content((messages,), {})
    assert messages[0]["reasoning_content"] == " "


def test_inject_reasoning_content_does_not_overwrite_existing_value() -> None:
    messages = [
        {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "Newly formatted thought"},
            ],
            "reasoning_content": "Already preserved thought",
        },
    ]

    assert not _inject_reasoning_content((), {"messages": messages})
    assert messages[0]["reasoning_content"] == "Already preserved thought"
