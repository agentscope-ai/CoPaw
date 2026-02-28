# -*- coding: utf-8 -*-
"""Tool that returns the current time in the configured timezone."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


async def get_current_time() -> ToolResponse:
    """Get the current system time with timezone information.

    Returns the time in the timezone configured in config.json (``timezone``
    field).  Falls back to the system local timezone when no timezone is
    configured, and to UTC if the local timezone cannot be determined.

    Returns:
        `ToolResponse`:
            The current local time string,
            e.g. "2026-02-13 19:30:45 CST (UTC+0800)".
    """
    try:
        from copaw.config.utils import get_timezone

        tz_name = get_timezone()
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        time_str = now.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    except Exception:
        time_str = datetime.now(timezone.utc).isoformat() + " (UTC)"

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=time_str,
            ),
        ],
    )
