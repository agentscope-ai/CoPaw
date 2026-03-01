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
