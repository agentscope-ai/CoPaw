# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from agentscope.message import Msg

from qwenpaw.app.channels.renderer import MessageRenderer, RenderStyle
from qwenpaw.app.runner.utils import agentscope_msg_to_message
from qwenpaw.providers.openai_chat_model_compat import (
    OpenAIChatModelCompat,
    _sanitize_tool_call,
)


class CompatHarnessOpenAIChatModel(OpenAIChatModelCompat):
    async def parse_stream_for_test(
        self,
        start_datetime: datetime,
        stream: Any,
    ) -> list[Any]:
        responses = []
        async for response in self._parse_openai_stream_response(
            start_datetime,
            stream,
        ):
            responses.append(response)
        return responses

    def parse_completion_for_test(
        self,
        start_datetime: datetime,
        response: Any,
    ) -> Any:
        return self._parse_openai_completion_response(
            start_datetime,
            response,
        )


class FakeAsyncStream:
    def __init__(self, items: list[Any]):
        self._items = items
        self._iter = None

    async def __aenter__(self) -> "FakeAsyncStream":
        self._iter = iter(self._items)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    def __aiter__(self) -> "FakeAsyncStream":
        return self

    async def __anext__(self) -> Any:
        assert self._iter is not None
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def _make_chunk(tool_calls: list[Any]) -> Any:
    delta = SimpleNamespace(
        reasoning_content=None,
        content=None,
        tool_calls=tool_calls,
    )
    choice = SimpleNamespace(delta=delta)
    return SimpleNamespace(usage=None, choices=[choice])


def _render_with_thinking_filter(content: list[dict[str, Any]]) -> list[Any]:
    runtime_messages = agentscope_msg_to_message(
        Msg(
            name="assistant",
            role="assistant",
            content=content,
        ),
    )
    renderer = MessageRenderer(RenderStyle(filter_thinking=True))
    parts = []
    for message in runtime_messages:
        parts.extend(renderer.message_to_parts(message))
    return parts


async def test_stream_parser_skips_tool_call_without_function() -> None:
    model = CompatHarnessOpenAIChatModel(
        "dummy",
        api_key="sk-test",
        stream=True,
    )

    malformed_tool_call = SimpleNamespace(
        index=0,
        id="call_bad",
        function=None,
    )
    none_arguments_tool_call = SimpleNamespace(
        index=1,
        id="call_partial",
        function=SimpleNamespace(name="ping", arguments=None),
    )
    valid_tool_call = SimpleNamespace(
        index=0,
        id="call_ok",
        function=SimpleNamespace(name="ping", arguments='{"x":1}'),
    )

    stream = FakeAsyncStream(
        [
            _make_chunk([malformed_tool_call]),
            _make_chunk([none_arguments_tool_call]),
            _make_chunk([valid_tool_call]),
        ],
    )

    responses = await model.parse_stream_for_test(
        datetime.now(),
        stream,
    )

    assert responses
    tool_blocks = [
        block
        for response in responses
        for block in response.content
        if block.get("type") == "tool_use"
    ]
    assert tool_blocks
    assert tool_blocks[-1]["name"] == "ping"
    assert tool_blocks[-1]["input"] == {"x": 1}


def test_completion_reasoning_content_in_model_extra_is_filterable() -> None:
    model = CompatHarnessOpenAIChatModel(
        "dummy",
        api_key="sk-test",
        stream=False,
    )
    response = SimpleNamespace(
        id="resp_1",
        usage=None,
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    model_extra={
                        "reasoning_content": "hidden reasoning",
                    },
                    content="visible answer",
                    audio=None,
                    tool_calls=None,
                ),
            ),
        ],
    )

    parsed = model.parse_completion_for_test(datetime.now(), response)

    assert parsed.content[0] == {
        "type": "thinking",
        "thinking": "hidden reasoning",
    }
    parts = _render_with_thinking_filter(parsed.content)
    assert [part.text for part in parts] == ["visible answer"]


async def test_stream_reasoning_content_in_model_extra_is_filterable() -> None:
    model = CompatHarnessOpenAIChatModel(
        "dummy",
        api_key="sk-test",
        stream=True,
    )
    delta = SimpleNamespace(
        model_extra={
            "reasoning_content": "hidden reasoning",
        },
        content="visible answer",
        tool_calls=None,
    )
    stream = FakeAsyncStream(
        [
            SimpleNamespace(
                id="resp_1",
                usage=None,
                choices=[SimpleNamespace(delta=delta)],
            ),
        ],
    )

    responses = await model.parse_stream_for_test(datetime.now(), stream)

    assert responses[-1].content[0] == {
        "type": "thinking",
        "thinking": "hidden reasoning",
    }
    parts = _render_with_thinking_filter(responses[-1].content)
    assert [part.text for part in parts] == ["visible answer"]


def test_sanitize_tool_call_normalizes_non_string_arguments() -> None:
    none_arguments_tool_call = SimpleNamespace(
        index=0,
        id="call_partial",
        function=SimpleNamespace(name="ping", arguments=None),
    )
    non_string_arguments_tool_call = SimpleNamespace(
        index=1,
        id="call_dict",
        function=SimpleNamespace(name="ping", arguments={"x": 2}),
    )
    missing_arguments_tool_call = SimpleNamespace(
        index=2,
        id="call_missing_args",
        function=SimpleNamespace(name="ping"),
    )
    missing_name_tool_call = SimpleNamespace(
        index=3,
        id="call_missing_name",
        function=SimpleNamespace(arguments={"x": 3}),
    )
    missing_name_and_arguments_tool_call = SimpleNamespace(
        index=4,
        id="call_missing_both",
        function=SimpleNamespace(),
    )

    sanitized_none_arguments = _sanitize_tool_call(none_arguments_tool_call)
    assert sanitized_none_arguments is not None
    assert sanitized_none_arguments.function.name == "ping"
    assert sanitized_none_arguments.function.arguments == ""

    sanitized_non_string_arguments = _sanitize_tool_call(
        non_string_arguments_tool_call,
    )
    assert sanitized_non_string_arguments is not None
    assert sanitized_non_string_arguments.function.name == "ping"
    assert isinstance(sanitized_non_string_arguments.function.arguments, str)
    assert json.loads(sanitized_non_string_arguments.function.arguments) == {
        "x": 2,
    }

    sanitized_missing_arguments = _sanitize_tool_call(
        missing_arguments_tool_call,
    )
    assert sanitized_missing_arguments is not None
    assert sanitized_missing_arguments.function.name == "ping"
    assert sanitized_missing_arguments.function.arguments == ""

    sanitized_missing_name = _sanitize_tool_call(missing_name_tool_call)
    assert sanitized_missing_name is not None
    assert sanitized_missing_name.function.name == ""
    assert isinstance(sanitized_missing_name.function.arguments, str)
    assert json.loads(sanitized_missing_name.function.arguments) == {"x": 3}

    sanitized_missing_name_and_arguments = _sanitize_tool_call(
        missing_name_and_arguments_tool_call,
    )
    assert sanitized_missing_name_and_arguments is not None
    assert sanitized_missing_name_and_arguments.function.name == ""
    assert sanitized_missing_name_and_arguments.function.arguments == ""
