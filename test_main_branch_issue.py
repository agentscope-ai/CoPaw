#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test if Issue #388 can be reproduced on main branch."""
import asyncio
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel

from copaw.agents.model_factory import create_model_and_formatter


async def test_main_branch():
    """Test if reasoning_content is preserved on main branch."""

    print("Testing main branch for Issue #388...")

    # Create model and formatter using CoPaw's factory
    # This will use FileBlockSupportFormatter
    model, formatter = create_model_and_formatter()

    # Override with Kimi K2.5 for testing
    model = OpenAIChatModel(
        model_name="kimi-k2.5",
        api_key="sk-sp-19b38f5cadda4b58874bfb5230302fac",
        stream=False,
        client_kwargs={
            "base_url": "https://coding.dashscope.aliyuncs.com/v1",
        },
    )

    print(f"Formatter type: {type(formatter).__name__}")

    # Create a message with thinking block
    msg = Msg(
        name="assistant",
        role="assistant",
        content=[
            {
                "type": "thinking",
                "thinking": "Test reasoning content",
            },
            {
                "type": "text",
                "text": "I'll help you.",
            },
            {
                "type": "tool_use",
                "id": "test_call",
                "name": "test_tool",
                "input": {},
            },
        ],
        timestamp="2024-01-01T00:00:00",
    )

    # Format the message
    formatted = await formatter._format([msg])

    print(f"\nFormatted messages: {len(formatted)}")
    for i, fm in enumerate(formatted):
        print(f"\nMessage {i}:")
        print(f"  Role: {fm.get('role')}")
        print(f"  Has tool_calls: {'tool_calls' in fm}")
        print(f"  Has reasoning_content: {'reasoning_content' in fm}")
        if 'reasoning_content' in fm:
            print(f"  reasoning_content: {fm['reasoning_content']}")

    # Check if reasoning_content is preserved
    has_reasoning = any(
        'reasoning_content' in fm
        for fm in formatted
        if fm.get('role') == 'assistant' and 'tool_calls' in fm
    )

    if has_reasoning:
        print("\n✅ Main branch: reasoning_content IS preserved")
        print("Issue #388 may already be fixed on main branch")
        return True
    else:
        print("\n❌ Main branch: reasoning_content NOT preserved")
        print("Issue #388 can be reproduced on main branch")
        return False


if __name__ == "__main__":
    asyncio.run(test_main_branch())
