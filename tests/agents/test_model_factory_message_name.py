# -*- coding: utf-8 -*-

from copaw.agents.model_factory import _strip_message_name_fields


def test_strip_message_name_fields_for_single_payload() -> None:
    payload = {
        "model": "demo",
        "messages": [
            {"role": "system", "name": "system", "content": "rules"},
            {"role": "user", "name": "user", "content": "hello"},
            {
                "role": "assistant",
                "name": "assistant",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "write_file",
                            "arguments": "{}",
                        },
                    },
                ],
            },
        ],
    }

    out = _strip_message_name_fields(payload)
    assert out is payload
    assert "name" not in payload["messages"][0]
    assert "name" not in payload["messages"][1]
    assert "name" not in payload["messages"][2]
    assert (
        payload["messages"][2]["tool_calls"][0]["function"]["name"]
        == "write_file"
    )


def test_strip_message_name_fields_for_batch_payload() -> None:
    payloads = [
        {
            "messages": [{"role": "user", "name": "user", "content": "a"}],
        },
        {
            "messages": [{"role": "assistant", "name": "assistant"}],
        },
    ]

    out = _strip_message_name_fields(payloads)
    assert out is payloads
    assert "name" not in payloads[0]["messages"][0]
    assert "name" not in payloads[1]["messages"][0]
