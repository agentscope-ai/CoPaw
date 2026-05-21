# -*- coding: utf-8 -*-
"""Tool to query current session context usage."""

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...config.config import load_agent_config, get_model_max_input_length


async def get_context_usage() -> ToolResponse:
    """Get current session context token usage and health status.

    Use this to check how much of the context window is being used,
    especially before long multi-step operations or when you notice
    degradation in instruction-following quality.

    Returns:
        ToolResponse with context usage details including token counts,
        usage ratio, and message count.
    """
    from ...app.agent_context import (
        get_current_agent_id,
        get_current_session_id,
    )
    from ...token_usage.model_wrapper import TokenRecordingModelWrapper

    agent_id = get_current_agent_id()
    session_id = get_current_session_id()

    if not agent_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Unable to determine current agent context.",
                ),
            ],
        )

    try:
        agent_config = load_agent_config(agent_id)
        max_input_length = get_model_max_input_length(agent_config)
    except Exception:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Unable to load agent configuration.",
                ),
            ],
        )

    # Gather data from TokenRecordingModelWrapper
    prompt_tokens = 0
    completion_tokens = 0
    model_name = "unknown"

    if session_id:
        # pylint: disable-next=protected-access
        usage_data = TokenRecordingModelWrapper._usage_by_session.get(
            session_id,
        )
        if usage_data:
            prompt_tokens = usage_data.get("prompt_tokens", 0)
            completion_tokens = usage_data.get("completion_tokens", 0)
            model_name = usage_data.get("model_name", "unknown")

    usage_ratio = (
        prompt_tokens / max_input_length if max_input_length > 0 else 0
    )

    lines = [
        "**Context Usage**\n",
        f"- Prompt tokens: {prompt_tokens:,}",
        f"- Completion tokens: {completion_tokens:,}",
        f"- Total tokens: {prompt_tokens + completion_tokens:,}",
        f"- Max input length: {max_input_length:,}",
        f"- Usage ratio: {usage_ratio:.1%}",
        f"- Model: {model_name}",
    ]
    if session_id:
        lines.append(f"- Session: {session_id[:40]}")

    if usage_ratio > 0.6:
        lines.append(
            "\n⚠️ Context usage is above 60%. "
            "Consider using `reset_my_context` to start a "
            "fresh session if quality is degrading.",
        )
    elif usage_ratio > 0.4:
        lines.append(
            "\nℹ️ Context usage is moderate. "
            "Quality may start degrading as it increases.",
        )

    text = "\n".join(lines)
    return ToolResponse(
        content=[TextBlock(type="text", text=text)],
    )
