# -*- coding: utf-8 -*-
"""Core approval service — gate-keeper for high-risk agent operations."""

import asyncio
import logging
import time
from typing import Dict, List, Optional

from .models import (
    ApprovalMode,
    ApprovalRequest,
    ApprovalStatus,
    HIGH_RISK_ACTIONS,
)

logger = logging.getLogger(__name__)

# Default timeout (seconds) for manual approval before auto-deny.
_DEFAULT_TIMEOUT = 120


class ApprovalService:
    """Manages approval lifecycle for high-risk tool calls.

    In ``auto`` mode every request is approved immediately.
    In ``manual`` mode the request is parked until a human responds
    via :meth:`respond` or the timeout fires (auto-deny).
    """

    def __init__(
        self,
        mode: ApprovalMode = ApprovalMode.AUTO,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._mode = mode
        self._timeout = timeout

        # request-id -> (request, asyncio.Event)
        self._pending: Dict[str, tuple[ApprovalRequest, asyncio.Event]] = {}

    # -- properties -----------------------------------------------------------

    @property
    def mode(self) -> ApprovalMode:
        return self._mode

    @mode.setter
    def mode(self, value: ApprovalMode) -> None:
        self._mode = value

    @property
    def timeout(self) -> float:
        return self._timeout

    # -- public API -----------------------------------------------------------

    def needs_approval(self, action: str) -> bool:
        """Return True when *action* requires approval under current mode."""
        if self._mode == ApprovalMode.AUTO:
            return False
        return action in HIGH_RISK_ACTIONS

    async def request_approval(
        self,
        action: str,
        target: str = "",
        summary: str = "",
        actor: str = "agent",
    ) -> ApprovalRequest:
        """Create an approval request and wait for resolution.

        In ``auto`` mode the request is immediately approved.
        In ``manual`` mode the call blocks until :meth:`respond` is
        called or the timeout expires (results in *denied/timeout*).

        Returns the resolved :class:`ApprovalRequest`.
        """
        req = ApprovalRequest(
            action=action,
            target=target,
            summary=summary,
            actor=actor,
        )

        if self._mode == ApprovalMode.AUTO:
            req.status = ApprovalStatus.APPROVED
            req.resolved_at = time.time()
            logger.debug("Auto-approved: %s %s", action, target)
            return req

        # Manual mode — park and wait.
        event = asyncio.Event()
        self._pending[req.id] = (req, event)
        logger.info(
            "Approval requested [%s]: %s — %s",
            req.id,
            action,
            summary or target,
        )

        try:
            await asyncio.wait_for(event.wait(), timeout=self._timeout)
        except asyncio.TimeoutError:
            req.status = ApprovalStatus.TIMEOUT
            req.resolved_at = time.time()
            logger.warning("Approval timed out [%s]: %s", req.id, action)
        finally:
            self._pending.pop(req.id, None)

        return req

    def respond(self, request_id: str, reply: ApprovalStatus) -> bool:
        """Resolve a pending approval request.

        Args:
            request_id: The id of the pending request.
            reply: ``approved`` or ``denied``.

        Returns:
            ``True`` if the request was found and resolved, ``False``
            if it was already resolved or unknown.
        """
        entry = self._pending.get(request_id)
        if entry is None:
            return False

        req, event = entry
        req.status = reply
        req.resolved_at = time.time()
        event.set()
        logger.info(
            "Approval %s [%s]: %s",
            reply.value,
            request_id,
            req.action,
        )
        return True

    def list_pending(self) -> List[ApprovalRequest]:
        """Return a snapshot of all currently pending requests."""
        return [req for req, _event in self._pending.values()]

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Look up a request by id (pending only)."""
        entry = self._pending.get(request_id)
        if entry is None:
            return None
        return entry[0]
