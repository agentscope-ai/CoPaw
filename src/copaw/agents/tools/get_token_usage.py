# -*- coding: utf-8 -*-
"""Tool to query token usage statistics."""

from datetime import date, timedelta

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...token_usage import get_token_usage_summary


async def get_token_usage(
    days: int = 30,
    model_name: str | None = None,
) -> ToolResponse:
    """Query LLM token usage over the past N days.

    Use this when the user asks about token consumption, API usage,
    or how many tokens have been used.

    Args:
        days: Number of days to look back (default: 30).
        model_name: Optional model name to filter by.

    Returns:
        ToolResponse with a formatted summary of token usage.
    """
    end = date.today()
    start = end - timedelta(days=max(1, min(days, 365)))
    summary = get_token_usage_summary(
        start_date=start,
        end_date=end,
        model_name=model_name,
    )

    lines: list[str] = []
    lines.append(
        f"Token usage ({start} ~ {end}, "
        + (f"model={model_name}" if model_name else "all models")
        + "):",
    )
    lines.append("")
    lines.append(f"- Total tokens: {summary['total_tokens']:,}")
    lines.append(f"- Prompt tokens: {summary['total_prompt_tokens']:,}")
    lines.append(
        f"- Completion tokens: {summary['total_completion_tokens']:,}",
    )
    lines.append(f"- Total calls: {summary['total_calls']:,}")
    lines.append("")

    if summary["by_model"]:
        lines.append("By model:")
        for model, stats in summary["by_model"].items():
            lines.append(
                f"  - {model}: {stats['total_tokens']:,} tokens "
                f"({stats['call_count']} calls)",
            )
        lines.append("")

    if summary["by_date"] and len(summary["by_date"]) <= 14:
        lines.append("By date:")
        for dt, stats in list(summary["by_date"].items())[-7:]:
            lines.append(
                f"  - {dt}: {stats['total_tokens']:,} tokens "
                f"({stats['call_count']} calls)",
            )
    elif summary["by_date"]:
        lines.append(
            f"By date: {len(summary['by_date'])} days with usage "
            "(see console for details)",
        )

    text = "\n".join(lines) if lines else "No token usage data in this period."
    return ToolResponse(
        content=[TextBlock(type="text", text=text)],
    )
