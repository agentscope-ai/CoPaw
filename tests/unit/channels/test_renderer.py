# -*- coding: utf-8 -*-
"""Tests for channel message rendering."""
from types import SimpleNamespace

from agentscope_runtime.engine.schemas.agent_schemas import (
    ContentType,
    MessageType,
)

from qwenpaw.app.channels.renderer import MessageRenderer


def test_message_to_parts_preserves_raw_string_message_content():
    """Raw final message text should be sent back to non-console channels."""
    message = SimpleNamespace(
        type=MessageType.MESSAGE,
        content="Final answer for the channel",
    )

    parts = MessageRenderer().message_to_parts(message)

    assert len(parts) == 1
    assert parts[0].type == ContentType.TEXT
    assert parts[0].text == "Final answer for the channel"
