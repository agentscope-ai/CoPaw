# -*- coding: utf-8 -*-
"""Data models for the approval system."""

import enum
import time
import uuid
from typing import Optional

from pydantic import BaseModel, Field


class ApprovalMode(str, enum.Enum):
    """How the approval service handles incoming requests."""

    AUTO = "auto"
    MANUAL = "manual"


class ApprovalStatus(str, enum.Enum):
    """Lifecycle state of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"


# Actions that require approval in manual mode.
# Tool function names are mapped to human-readable labels.
HIGH_RISK_ACTIONS = frozenset(
    {
        "execute_shell_command",
        "write_file",
        "edit_file",
        "append_file",
        "browser_use",
    },
)


class ApprovalRequest(BaseModel):
    """A single approval request created when an agent invokes a
    high-risk tool."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    action: str = Field(
        ...,
        description="Tool function name, e.g. 'execute_shell_command'",
    )
    target: str = Field(
        default="",
        description="Primary argument (command string, file path, …)",
    )
    summary: str = Field(
        default="",
        description="Human-readable one-line summary of what will happen",
    )
    actor: str = Field(
        default="agent",
        description="Who triggered this (agent / cron / system)",
    )
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = Field(default_factory=time.time)
    resolved_at: Optional[float] = None


class ApprovalResponse(BaseModel):
    """Payload sent by the reviewer to approve or deny a request."""

    reply: ApprovalStatus = Field(
        ...,
        description="Must be 'approved' or 'denied'",
    )
