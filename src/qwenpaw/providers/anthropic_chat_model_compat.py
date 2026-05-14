# -*- coding: utf-8 -*-
"""Compatibility helpers for Anthropic-compatible chat models."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any, AsyncGenerator, AsyncIterable, Type

from agentscope.model import AnthropicChatModel, ChatResponse
from pydantic import BaseModel


_ANTHROPIC_DELTA_TYPES = {
    "text_delta",
    "thinking_delta",
    "signature_delta",
    "input_json_delta",
}


def _value(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _text_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _content_block_delta_event(event: Any, delta: Any) -> SimpleNamespace:
    return SimpleNamespace(
        type="content_block_delta",
        index=_value(event, "index"),
        delta=delta,
    )


async def _normalize_openai_style_reasoning_deltas(
    response: AsyncIterable[Any],
) -> AsyncGenerator[Any, None]:
    """Map MiMo/OpenAI-style Anthropic deltas into native Anthropic deltas."""
    async for event in response:
        if _value(event, "type") != "content_block_delta":
            yield event
            continue

        delta = _value(event, "delta")
        delta_type = _value(delta, "type")
        if delta_type in _ANTHROPIC_DELTA_TYPES:
            yield event
            continue

        reasoning_content = _text_or_none(_value(delta, "reasoning_content"))
        content = _text_or_none(_value(delta, "content"))
        if not reasoning_content and not content:
            yield event
            continue

        if reasoning_content:
            yield _content_block_delta_event(
                event,
                SimpleNamespace(
                    type="thinking_delta",
                    thinking=reasoning_content,
                ),
            )
        if content:
            yield _content_block_delta_event(
                event,
                SimpleNamespace(
                    type="text_delta",
                    text=content,
                ),
            )


class AnthropicChatModelCompat(AnthropicChatModel):
    """Anthropic model wrapper for compatible-provider stream quirks."""

    async def _parse_anthropic_stream_completion_response(
        self,
        start_datetime: datetime,
        response: AsyncIterable[Any],
        structured_model: Type[BaseModel] | None = None,
    ) -> AsyncGenerator[ChatResponse, None]:
        normalized_response = _normalize_openai_style_reasoning_deltas(
            response,
        )
        async for chunk in super()._parse_anthropic_stream_completion_response(
            start_datetime,
            normalized_response,
            structured_model,
        ):
            yield chunk
