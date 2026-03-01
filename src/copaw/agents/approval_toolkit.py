# -*- coding: utf-8 -*-
"""Toolkit subclass that gates high-risk tool calls behind approval."""

import logging
from typing import TYPE_CHECKING, AsyncGenerator, Optional

from agentscope.message import TextBlock
from agentscope.tool import Toolkit, ToolResponse

if TYPE_CHECKING:
    from agentscope.message._message_block import ToolUseBlock

    from ..app.approvals.service import ApprovalService

from ..app.approvals.models import ApprovalStatus

logger = logging.getLogger(__name__)


class ApprovalToolkit(Toolkit):
    """A Toolkit that checks with an ApprovalService before executing
    high-risk tools.

    If no *approval_service* is set, or the service is in ``auto`` mode,
    this behaves identically to the base :class:`Toolkit`.
    """

    def __init__(self) -> None:
        super().__init__()
        self._approval_service: Optional["ApprovalService"] = None

    def set_approval_service(
        self,
        service: Optional["ApprovalService"],
    ) -> None:
        self._approval_service = service

    def _build_summary(self, tool_call: "ToolUseBlock") -> str:
        """Build a human-readable one-liner from a tool call block."""
        name = tool_call.get("name", "unknown")
        inputs = tool_call.get("input", {})

        if name == "execute_shell_command":
            cmd = inputs.get("command", "")
            return f"Run shell command: {cmd[:120]}"
        if name in ("write_file", "edit_file", "append_file"):
            path = inputs.get("file_path", "")
            return f"{name}: {path}"
        if name == "browser_use":
            url = inputs.get("url", "")
            return f"Browser navigate: {url[:120]}"
        return f"Call tool: {name}"

    async def call_tool_function(
        self,
        tool_call: "ToolUseBlock",
    ) -> AsyncGenerator[ToolResponse, None]:
        """Override to inject approval gate before high-risk tools."""
        name = tool_call.get("name", "")

        if (
            self._approval_service is not None
            and self._approval_service.needs_approval(name)
        ):
            inputs = tool_call.get("input", {})
            # Derive the primary target from tool inputs
            target = (
                inputs.get("command", "")
                or inputs.get("file_path", "")
                or inputs.get("url", "")
                or str(inputs)[:200]
            )

            req = await self._approval_service.request_approval(
                action=name,
                target=target,
                summary=self._build_summary(tool_call),
            )

            if req.status != ApprovalStatus.APPROVED:
                reason = req.status.value  # "denied" or "timeout"
                logger.info(
                    "Tool call blocked (%s) [%s]: %s",
                    reason,
                    req.id,
                    name,
                )
                denied_resp = ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=(
                                f"⚠️ Tool call '{name}' was {reason} by the user. "
                                f"Please inform the user and suggest alternatives."
                            ),
                        ),
                    ],
                )
                yield denied_resp
                return

        # Approved (or not high-risk) — delegate to base Toolkit
        async for chunk in super().call_tool_function(tool_call):
            yield chunk
