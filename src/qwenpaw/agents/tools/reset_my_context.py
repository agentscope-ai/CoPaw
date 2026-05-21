# -*- coding: utf-8 -*-
"""Tool to reset agent context with optional checkpoint."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

logger = logging.getLogger(__name__)


async def reset_my_context(
    checkpoint_file: str = "",
) -> ToolResponse:
    """Reset the current session context, starting fresh.

    Use this when you notice degradation in instruction-following quality
    due to context accumulation. A checkpoint of the current session state
    is saved before resetting.

    Args:
        checkpoint_file: Optional custom filename for the checkpoint.
            If empty, a timestamp-based name is generated automatically.

    Returns:
        ToolResponse with reset status and checkpoint path.
    """
    from ...app.agent_context import (
        get_current_agent_id,
        get_current_session_id,
    )

    agent_id = get_current_agent_id()
    session_id = get_current_session_id()

    if not session_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="No active session found. Cannot reset context.",
                ),
            ],
        )

    # Save checkpoint before reset
    checkpoint_path = ""
    now = datetime.now(tz=timezone.utc)
    try:
        # Build checkpoint directory under working directory
        working_dir = os.environ.get("QWENPAW_WORKING_DIR", ".")
        cp_dir = Path(working_dir) / "checkpoints"
        cp_dir.mkdir(parents=True, exist_ok=True)

        ts = now.strftime("%Y%m%d-%H%M%S")
        filename = (
            checkpoint_file
            if checkpoint_file
            else f"reset-{session_id[:20]}-{ts}.json"
        )
        filepath = cp_dir / filename

        # Collect current session data for checkpoint
        checkpoint_data = {
            "agent_id": agent_id,
            "session_id": session_id,
            "timestamp": now.isoformat(),
        }

        # Try to get current messages from TokenRecordingModelWrapper
        from ...token_usage.model_wrapper import TokenRecordingModelWrapper

        # pylint: disable-next=protected-access
        usage_data = TokenRecordingModelWrapper._usage_by_session.get(
            session_id,
        )
        if usage_data:
            checkpoint_data["last_usage"] = usage_data

        filepath.write_text(
            json.dumps(checkpoint_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        checkpoint_path = str(filepath)
        logger.info(
            "Context reset checkpoint saved: %s",
            checkpoint_path,
        )
    except Exception as e:
        logger.warning("Failed to save checkpoint during reset: %s", e)

    # Perform the reset by clearing the session state
    try:
        # Clear token usage tracking for this session
        from ...token_usage.model_wrapper import TokenRecordingModelWrapper

        TokenRecordingModelWrapper.pop_usage_for_session(session_id)

        # Mark session for reset on next query
        # We use a session state flag that the runner picks up.
        # Since we can't directly access the agent from a tool,
        # we store a reset signal in session state.
        try:
            _reset_signal_path = (
                Path(
                    os.environ.get("QWENPAW_WORKING_DIR", "."),
                )
                / ".reset_signals"
            )
            _reset_signal_path.mkdir(parents=True, exist_ok=True)
            signal_file = _reset_signal_path / f"{session_id}.json"
            signal_file.write_text(
                json.dumps(
                    {
                        "session_id": session_id,
                        "reset_at": now.isoformat(),
                        "checkpoint_path": checkpoint_path,
                    },
                ),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Failed to write reset signal: %s", e)

    except Exception as e:
        logger.warning("Failed to clear token usage: %s", e)

    lines = [
        "**Context Reset Initiated**\n",
        "- Session context has been flagged for reset",
        "- Token usage tracking cleared",
    ]
    if checkpoint_path:
        lines.append(f"- Checkpoint saved: {checkpoint_path}")
    lines.append(
        "\nThe reset will take full effect on the next query. "
        "Your execution quality should improve with a fresh context.",
    )

    return ToolResponse(
        content=[TextBlock(type="text", text="\n".join(lines))],
    )
