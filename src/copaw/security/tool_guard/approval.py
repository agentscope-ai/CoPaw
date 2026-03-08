# -*- coding: utf-8 -*-
"""Approval helpers for tool-guard mediated tool execution."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import ToolGuardResult


TOOL_GUARD_CONTROL_KEY = "__copaw_tool_guard__"


class ApprovalDecision(str, Enum):
    """Possible approval outcomes for a guarded tool call."""

    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"


def format_findings_summary(
    result: "ToolGuardResult",
    *,
    max_items: int = 3,
) -> str:
    """Format findings into a concise markdown summary."""
    if not result.findings:
        return "未发现具体风险规则命中。"

    lines = []
    for finding in result.findings[:max_items]:
        lines.append(
            f"- [{finding.severity.value}] {finding.description}"
        )
    remaining = result.findings_count - len(lines)
    if remaining > 0:
        lines.append(f"- 其余 {remaining} 条风险已省略")
    return "\n".join(lines)


def build_denied_guard_payload(
    *,
    tool_name: str,
    decision: ApprovalDecision,
    result: "ToolGuardResult",
    reason: str | None = None,
) -> dict[str, Any]:
    """Build control payload injected into a denied tool call."""
    message_reason = reason or {
        ApprovalDecision.DENIED: "用户拒绝了此次敏感工具调用。",
        ApprovalDecision.TIMEOUT: "等待用户审批超时，此次敏感工具调用已取消。",
    }.get(decision, "此次敏感工具调用已被拦截。")

    return {
        "denied": True,
        "decision": decision.value,
        "tool_name": tool_name,
        "message": (
            f"Tool execution denied for '{tool_name}'. {message_reason} "
            f"风险等级: {result.max_severity.value}; 命中 {result.findings_count} 条规则。"
        ),
        "findings": [finding.to_dict() for finding in result.findings],
    }
