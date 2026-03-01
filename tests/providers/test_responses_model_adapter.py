import asyncio
from datetime import datetime

from copaw.providers.responses_model import OpenAIResponsesChatModel


def test_responses_input_drops_message_name_field() -> None:
    """Avoid sending unsupported `input[].name` in Responses payload."""
    messages = [
        {
            "role": "user",
            "name": "user",
            "content": [{"type": "text", "text": "hello"}],
        },
    ]

    formatted = OpenAIResponsesChatModel._format_messages_for_responses(messages)

    assert formatted[0]["role"] == "user"
    assert "name" not in formatted[0]
    assert formatted[0]["content"][0]["type"] == "input_text"


def test_responses_tools_converted_to_top_level_name() -> None:
    """Responses API requires tools[].name (not tools[].function.name)."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read file content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                    },
                },
            },
        },
    ]

    formatted = OpenAIResponsesChatModel._format_tools_for_responses(tools)

    assert formatted[0]["type"] == "function"
    assert formatted[0]["name"] == "read_file"
    assert "function" not in formatted[0]


def test_assistant_history_uses_output_text_blocks() -> None:
    """Assistant history must be output_text, not input_text."""
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": "question 1"}],
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "answer 1"}],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": "question 2"}],
        },
    ]

    formatted = OpenAIResponsesChatModel._format_messages_for_responses(messages)

    assistant_msg = formatted[1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["content"][0]["type"] == "output_text"
    assert all(block.get("type") != "input_text" for block in assistant_msg["content"])


class _FakeResponsesStream:
    def __init__(self, events):
        self._events = iter(events)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._events)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def test_responses_stream_parses_text_deltas() -> None:
    events = [
        {"type": "response.output_text.delta", "delta": "Hel"},
        {"type": "response.output_text.delta", "delta": "lo"},
        {
            "type": "response.completed",
            "response": {
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 2,
                },
            },
        },
    ]

    async def _collect():
        chunks = []
        async for chunk in OpenAIResponsesChatModel._parse_responses_stream_response(
            datetime.now(),
            _FakeResponsesStream(events),
        ):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(_collect())

    assert chunks
    assert chunks[-1].content[0]["type"] == "text"
    assert chunks[-1].content[0]["text"] == "Hello"
    assert chunks[-1].usage is not None


def test_responses_stream_parses_function_call_arguments() -> None:
    events = [
        {
            "type": "response.output_item.added",
            "item": {
                "id": "fc_1",
                "type": "function_call",
                "call_id": "call_1",
                "name": "read_file",
                "arguments": "",
            },
        },
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "delta": '{"path":"a',
        },
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "delta": '.txt"}',
        },
        {
            "type": "response.function_call_arguments.done",
            "item_id": "fc_1",
            "arguments": '{"path":"a.txt"}',
            "name": "read_file",
        },
    ]

    async def _collect():
        chunks = []
        async for chunk in OpenAIResponsesChatModel._parse_responses_stream_response(
            datetime.now(),
            _FakeResponsesStream(events),
        ):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(_collect())

    assert chunks
    tool_use = next(block for block in chunks[-1].content if block["type"] == "tool_use")
    assert tool_use["id"] == "call_1"
    assert tool_use["name"] == "read_file"
    assert tool_use["input"] == {"path": "a.txt"}
