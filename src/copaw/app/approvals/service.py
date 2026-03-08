# -*- coding: utf-8 -*-
"""Console-only approval service for sensitive tool execution."""
from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...security.tool_guard.approval import (
    ApprovalDecision,
    format_findings_summary,
)

if TYPE_CHECKING:
    from ...security.tool_guard.models import ToolGuardResult


_DEFAULT_BASE_URL = "http://127.0.0.1:8088"
_DEFAULT_TIMEOUT_SECONDS = 300.0


@dataclass
class PendingApproval:
    """In-memory record for one pending console approval."""

    request_id: str
    session_id: str
    user_id: str
    channel: str
    tool_name: str
    created_at: float
    approve_url: str
    deny_url: str
    future: asyncio.Future[ApprovalDecision]
    status: str = "pending"
    resolved_at: float | None = None
    result_summary: str = ""
    findings_count: int = 0


class ConsoleApprovalService:
    """Manage console approval links and await user decisions."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._pending: dict[str, PendingApproval] = {}
        self._completed: dict[str, PendingApproval] = {}

    def _base_url(self) -> str:
        return os.getenv(
            "COPAW_TOOL_GUARD_APPROVAL_BASE_URL",
            os.getenv("COPAW_BASE_URL", _DEFAULT_BASE_URL),
        ).rstrip("/")

    def _timeout_seconds(self) -> float:
        raw = os.getenv("COPAW_TOOL_GUARD_APPROVAL_TIMEOUT_SECONDS")
        if raw is None:
            return _DEFAULT_TIMEOUT_SECONDS
        try:
            return max(float(raw), 1.0)
        except (TypeError, ValueError):
            return _DEFAULT_TIMEOUT_SECONDS

    def _build_action_url(self, request_id: str, action: str) -> str:
        return f"{self._base_url()}/api/console/approvals/{request_id}/{action}"

    async def create_pending(
        self,
        *,
        session_id: str,
        user_id: str,
        channel: str,
        tool_name: str,
        result: "ToolGuardResult",
    ) -> PendingApproval:
        """Create a pending approval record and return it (no side effects).

        The caller is responsible for presenting the approve/deny URLs
        to the user (e.g. via a chat message).
        """
        request_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        approve_url = self._build_action_url(request_id, "approve")
        deny_url = self._build_action_url(request_id, "deny")
        pending = PendingApproval(
            request_id=request_id,
            session_id=session_id,
            user_id=user_id,
            channel=channel,
            tool_name=tool_name,
            created_at=time.time(),
            approve_url=approve_url,
            deny_url=deny_url,
            future=loop.create_future(),
            result_summary=format_findings_summary(result),
            findings_count=result.findings_count,
        )

        async with self._lock:
            self._pending[request_id] = pending

        return pending

    async def await_decision(
        self,
        pending: PendingApproval,
    ) -> ApprovalDecision:
        """Await the user decision on a pending approval (with timeout)."""
        try:
            decision = await asyncio.wait_for(
                pending.future,
                timeout=self._timeout_seconds(),
            )
        except asyncio.TimeoutError:
            decision = ApprovalDecision.TIMEOUT
            await self.resolve_request(pending.request_id, decision)

        return decision

    async def resolve_request(
        self,
        request_id: str,
        decision: ApprovalDecision,
    ) -> PendingApproval | None:
        """Resolve one pending approval request."""
        async with self._lock:
            pending = self._pending.pop(request_id, None)
            if pending is None:
                pending = self._completed.get(request_id)
                if pending is None:
                    return None
                return pending

            pending.status = decision.value
            pending.resolved_at = time.time()
            self._completed[request_id] = pending

        if not pending.future.done():
            pending.future.set_result(decision)

        return pending

    async def get_request(self, request_id: str) -> PendingApproval | None:
        """Get a request by id whether pending or already resolved."""
        async with self._lock:
            return self._pending.get(request_id) or self._completed.get(
                request_id,
            )


_approval_service: ConsoleApprovalService | None = None


def get_console_approval_service() -> ConsoleApprovalService:
    """Return the process-wide console approval service singleton."""
    global _approval_service
    if _approval_service is None:
        _approval_service = ConsoleApprovalService()
    return _approval_service
