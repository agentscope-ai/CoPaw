# -*- coding: utf-8 -*-
"""Tool that returns the current time in the user-configured timezone."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...config import load_config


async def get_current_time() -> ToolResponse:
    """Get the current time.

    Returns the current time in the user-configured timezone.
    Useful for time-sensitive tasks such as scheduling cron jobs.

    Returns:
        `ToolResponse`:
            The current time string,
            e.g. "2026-02-13 19:30:45 Asia/Shanghai (Friday)".
    """
    user_tz = load_config().user_timezone or "UTC"
    try:
        now = datetime.now(ZoneInfo(user_tz))
    except (KeyError, Exception):
        now = datetime.now(timezone.utc)
        user_tz = "UTC"

    time_str = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} "
        f"{user_tz} ({now.strftime('%A')})"
    )

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=time_str,
            ),
        ],
    )
