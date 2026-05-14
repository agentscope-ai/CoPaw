# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest

from qwenpaw.providers.anthropic_chat_model_compat import (
    AnthropicChatModelCompat,
)


async def _aiter_events(*events: Any):
    for event in events:
        yield event


def _message_start():
    return SimpleNamespace(
        type="message_start",
        message=SimpleNamespace(
            id="msg_1",
            usage=SimpleNamespace(input_tokens=3, output_tokens=0),
        ),
    )


@pytest.mark.asyncio
async def test_stream_parser_preserves_openai_style_reasoning_content():
    model = AnthropicChatModelCompat(
        model_name="mimo",
        api_key="test",
        stream=True,
        stream_tool_parsing=False,
    )
    stream = _aiter_events(
        _message_start(),
        SimpleNamespace(
            type="content_block_delta",
            index=0,
            delta={
                "content": "",
                "reasoning_content": "Need memory before answering.",
            },
        ),
        SimpleNamespace(
            type="content_block_start",
            index=1,
            content_block=SimpleNamespace(
                type="tool_use",
                id="toolu_1",
                name="memory_search",
            ),
        ),
        SimpleNamespace(
            type="content_block_delta",
            index=1,
            delta=SimpleNamespace(
                type="input_json_delta",
                partial_json='{"query":"preferences"}',
            ),
        ),
    )

    chunks = [
        chunk
        async for chunk in model._parse_anthropic_stream_completion_response(
            datetime.now(),
            stream,
        )
    ]

    final_content = chunks[-1].content
    assert final_content[0]["type"] == "thinking"
    assert final_content[0]["thinking"] == "Need memory before answering."
    assert final_content[1]["type"] == "tool_use"
    assert final_content[1]["input"] == {"query": "preferences"}


@pytest.mark.asyncio
async def test_stream_parser_maps_openai_style_content_delta_to_text():
    model = AnthropicChatModelCompat(
        model_name="mimo",
        api_key="test",
        stream=True,
        stream_tool_parsing=False,
    )
    stream = _aiter_events(
        _message_start(),
        SimpleNamespace(
            type="content_block_delta",
            index=0,
            delta={
                "content": "Hello",
                "reasoning_content": "",
            },
        ),
    )

    chunks = [
        chunk
        async for chunk in model._parse_anthropic_stream_completion_response(
            datetime.now(),
            stream,
        )
    ]

    assert chunks[-1].content == [{"type": "text", "text": "Hello"}]
