# -*- coding: utf-8 -*-
"""OpenAI chat model compatibility wrappers."""

from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Type

from agentscope.message import TextBlock, ThinkingBlock, ToolUseBlock
from agentscope.model import OpenAIChatModel
from agentscope.model._model_usage import ChatUsage
from agentscope.model._model_response import ChatResponse
from pydantic import BaseModel

from ..local_models.tag_parser import (
    extract_thinking_from_text,
    parse_tool_calls_from_text,
    text_contains_think_tag,
    text_contains_tool_call_tag,
)


def _json_loads_safe(s: str) -> dict:
    """Safely parse JSON string, returning empty dict on failure."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return {}


def _clone_with_overrides(obj: Any, **overrides: Any) -> Any:
    """Clone a stream object into a mutable namespace with overrides."""
    data = dict(getattr(obj, "__dict__", {}))
    data.update(overrides)
    return SimpleNamespace(**data)


def _sanitize_tool_call(tool_call: Any) -> Any | None:
    """Normalize a tool call for parser safety, or drop it if unusable."""
    if not hasattr(tool_call, "index"):
        return None

    function = getattr(tool_call, "function", None)
    if function is None:
        return None

    has_name = hasattr(function, "name")
    has_arguments = hasattr(function, "arguments")

    raw_name = getattr(function, "name", "")
    if isinstance(raw_name, str):
        safe_name = raw_name
    elif raw_name is None:
        safe_name = ""
    else:
        safe_name = str(raw_name)

    raw_arguments = getattr(function, "arguments", "")
    if isinstance(raw_arguments, str):
        safe_arguments = raw_arguments
    elif raw_arguments is None:
        safe_arguments = ""
    else:
        try:
            safe_arguments = json.dumps(raw_arguments, ensure_ascii=False)
        except (TypeError, ValueError):
            safe_arguments = str(raw_arguments)

    if (
        has_name
        and has_arguments
        and isinstance(raw_name, str)
        and isinstance(
            raw_arguments,
            str,
        )
    ):
        return tool_call

    safe_function = SimpleNamespace(
        name=safe_name,
        arguments=safe_arguments,
    )
    return _clone_with_overrides(tool_call, function=safe_function)


def _sanitize_chunk(chunk: Any) -> Any:
    """Drop/normalize malformed tool-calls in a streaming chunk."""
    choices = getattr(chunk, "choices", None)
    if not choices:
        return chunk

    sanitized_choices: list[Any] = []
    changed = False

    for choice in choices:
        delta = getattr(choice, "delta", None)
        if delta is None:
            sanitized_choices.append(choice)
            continue

        raw_tool_calls = getattr(delta, "tool_calls", None)
        if not raw_tool_calls:
            sanitized_choices.append(choice)
            continue

        choice_changed = False
        sanitized_tool_calls: list[Any] = []
        for tool_call in raw_tool_calls:
            sanitized = _sanitize_tool_call(tool_call)
            if sanitized is not tool_call:
                choice_changed = True
            if sanitized is not None:
                sanitized_tool_calls.append(sanitized)

        if choice_changed:
            changed = True
            sanitized_delta = _clone_with_overrides(
                delta,
                tool_calls=sanitized_tool_calls,
            )
            sanitized_choice = _clone_with_overrides(
                choice,
                delta=sanitized_delta,
            )
            sanitized_choices.append(sanitized_choice)
            continue

        sanitized_choices.append(choice)

    if not changed:
        return chunk
    return _clone_with_overrides(chunk, choices=sanitized_choices)


def _sanitize_stream_item(item: Any) -> Any:
    """Sanitize either plain stream chunks or structured stream items."""
    if hasattr(item, "chunk"):
        chunk = item.chunk
        sanitized_chunk = _sanitize_chunk(chunk)
        if sanitized_chunk is chunk:
            return item
        return _clone_with_overrides(item, chunk=sanitized_chunk)

    return _sanitize_chunk(item)


class _SanitizedStream:
    """Proxy OpenAI async stream that sanitizes each emitted item."""

    def __init__(self, stream: Any):
        self._stream = stream
        self._ctx_stream: Any | None = None

    async def __aenter__(self) -> "_SanitizedStream":
        self._ctx_stream = await self._stream.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc: Any,
        tb: Any,
    ) -> bool | None:
        return await self._stream.__aexit__(exc_type, exc, tb)

    def __aiter__(self) -> "_SanitizedStream":
        return self

    async def __anext__(self) -> Any:
        if self._ctx_stream is None:
            raise StopAsyncIteration
        item = await self._ctx_stream.__anext__()
        return _sanitize_stream_item(item)


class OpenAIChatModelCompat(OpenAIChatModel):
    """OpenAIChatModel with robust parsing for malformed tool-call chunks and <think> tags."""

    async def _parse_openai_stream_response(
        self,
        start_datetime: datetime,
        response: Any,
        structured_model: Type[BaseModel] | None = None,
    ) -> AsyncGenerator[ChatResponse, None]:
        sanitized_response = _SanitizedStream(response)

        accumulated_text = ""
        accumulated_thinking = ""
        tool_calls: dict[int, dict] = {}

        async for chunk in sanitized_response:
            choices = getattr(chunk, "choices", [])
            if not choices:
                continue

            delta = getattr(choices[0], "delta", None)
            if not delta:
                continue

            # Accumulate text
            content_piece = getattr(delta, "content", "") or ""
            accumulated_text += content_piece

            # Accumulate reasoning/thinking content
            thinking_piece = getattr(delta, "reasoning_content", "") or ""
            accumulated_thinking += thinking_piece

            # Handle tool calls in delta
            delta_tool_calls = getattr(delta, "tool_calls", []) or []
            for tc in delta_tool_calls:
                idx = getattr(tc, "index", 0)
                if idx not in tool_calls:
                    tool_calls[idx] = {
                        "id": getattr(tc, "id", f"call_{idx}") or f"call_{idx}",
                        "name": getattr(getattr(tc, "function", None), "name", "") or "",
                        "arguments": "",
                    }
                tool_calls[idx]["arguments"] += getattr(getattr(tc, "function", None), "arguments", "") or ""

            # Build content blocks
            contents: list = []

            # Determine effective thinking and display text.
            effective_thinking = accumulated_thinking
            effective_text = accumulated_text

            if (
                not effective_thinking
                and effective_text
                and text_contains_think_tag(effective_text)
            ):
                parsed_thinking = extract_thinking_from_text(effective_text)
                effective_thinking = parsed_thinking.thinking
                effective_text = parsed_thinking.remaining_text
                # If <think> is still open, suppress all text output
                if parsed_thinking.has_open_tag:
                    effective_text = ""

            if effective_thinking:
                contents.append(
                    ThinkingBlock(
                        type="thinking",
                        thinking=effective_thinking,
                    ),
                )

            # Fallback: parse <tool_call> tags from effective text
            if (
                not tool_calls
                and effective_text
                and text_contains_tool_call_tag(effective_text)
            ):
                parsed = parse_tool_calls_from_text(effective_text)
                display_text = parsed.text_before
                if parsed.text_after:
                    display_text = (
                        f"{display_text}\n{parsed.text_after}".strip()
                        if display_text
                        else parsed.text_after
                    )
                if display_text:
                    contents.append(
                        TextBlock(type="text", text=display_text),
                    )
                for ptc in parsed.tool_calls:
                    contents.append(
                        ToolUseBlock(
                            type="tool_use",
                            id=ptc.id,
                            name=ptc.name,
                            input=ptc.arguments,
                            raw_input=ptc.raw_arguments,
                        ),
                    )
            elif effective_text:
                contents.append(
                    TextBlock(type="text", text=effective_text),
                )

            for tc_data in tool_calls.values():
                contents.append(
                    ToolUseBlock(
                        type="tool_use",
                        id=tc_data["id"],
                        name=tc_data["name"],
                        input=_json_loads_safe(tc_data["arguments"]),
                        raw_input=tc_data["arguments"],
                    ),
                )

            usage_raw = getattr(chunk, "usage", None)
            elapsed = (datetime.now() - start_datetime).total_seconds()
            usage = (
                ChatUsage(
                    input_tokens=getattr(usage_raw, "prompt_tokens", 0),
                    output_tokens=getattr(usage_raw, "completion_tokens", 0),
                    time=elapsed,
                )
                if usage_raw
                else None
            )

            if contents:
                yield ChatResponse(content=contents, usage=usage)
