# -*- coding: utf-8 -*-
"""Unit tests for the ApprovalService."""

import asyncio

import pytest

from copaw.app.approvals.models import (
    ApprovalMode,
    ApprovalStatus,
    HIGH_RISK_ACTIONS,
)
from copaw.app.approvals.service import ApprovalService


# ---------------------------------------------------------------------------
# Auto mode
# ---------------------------------------------------------------------------


class TestAutoMode:
    """In auto mode everything is approved immediately."""

    def test_needs_approval_always_false(self):
        svc = ApprovalService(mode=ApprovalMode.AUTO)
        for action in HIGH_RISK_ACTIONS:
            assert svc.needs_approval(action) is False

    @pytest.mark.asyncio
    async def test_request_auto_approved(self):
        svc = ApprovalService(mode=ApprovalMode.AUTO)
        req = await svc.request_approval(
            action="execute_shell_command",
            target="ls -la",
            summary="List files",
        )
        assert req.status == ApprovalStatus.APPROVED
        assert req.resolved_at is not None

    @pytest.mark.asyncio
    async def test_no_pending_in_auto(self):
        svc = ApprovalService(mode=ApprovalMode.AUTO)
        await svc.request_approval(action="write_file", target="/tmp/x")
        assert svc.list_pending() == []


# ---------------------------------------------------------------------------
# Manual mode
# ---------------------------------------------------------------------------


class TestManualMode:
    """In manual mode requests wait for human response."""

    def test_needs_approval_for_high_risk(self):
        svc = ApprovalService(mode=ApprovalMode.MANUAL)
        assert svc.needs_approval("execute_shell_command") is True
        assert svc.needs_approval("write_file") is True
        assert svc.needs_approval("read_file") is False
        assert svc.needs_approval("get_current_time") is False

    @pytest.mark.asyncio
    async def test_approve_flow(self):
        svc = ApprovalService(mode=ApprovalMode.MANUAL, timeout=5)

        async def _approve_after_delay():
            await asyncio.sleep(0.1)
            pending = svc.list_pending()
            assert len(pending) == 1
            svc.respond(pending[0].id, ApprovalStatus.APPROVED)

        task = asyncio.create_task(_approve_after_delay())
        req = await svc.request_approval(
            action="execute_shell_command",
            target="rm -rf /tmp/test",
        )
        await task

        assert req.status == ApprovalStatus.APPROVED
        assert svc.list_pending() == []

    @pytest.mark.asyncio
    async def test_deny_flow(self):
        svc = ApprovalService(mode=ApprovalMode.MANUAL, timeout=5)

        async def _deny():
            await asyncio.sleep(0.1)
            pending = svc.list_pending()
            svc.respond(pending[0].id, ApprovalStatus.DENIED)

        task = asyncio.create_task(_deny())
        req = await svc.request_approval(
            action="write_file",
            target="/etc/passwd",
        )
        await task

        assert req.status == ApprovalStatus.DENIED

    @pytest.mark.asyncio
    async def test_timeout_auto_denies(self):
        svc = ApprovalService(mode=ApprovalMode.MANUAL, timeout=0.2)
        req = await svc.request_approval(
            action="browser_use",
            target="https://example.com",
        )
        assert req.status == ApprovalStatus.TIMEOUT
        assert svc.list_pending() == []

    def test_respond_unknown_id_returns_false(self):
        svc = ApprovalService(mode=ApprovalMode.MANUAL)
        assert svc.respond("nonexistent", ApprovalStatus.APPROVED) is False

    @pytest.mark.asyncio
    async def test_get_request(self):
        svc = ApprovalService(mode=ApprovalMode.MANUAL, timeout=5)

        async def _check_and_approve():
            await asyncio.sleep(0.1)
            pending = svc.list_pending()
            req = svc.get_request(pending[0].id)
            assert req is not None
            assert req.action == "edit_file"
            svc.respond(req.id, ApprovalStatus.APPROVED)

        task = asyncio.create_task(_check_and_approve())
        await svc.request_approval(action="edit_file", target="main.py")
        await task

        # After resolution, get_request returns None
        assert svc.get_request("whatever") is None


# ---------------------------------------------------------------------------
# Mode switching
# ---------------------------------------------------------------------------


class TestModeSwitching:
    def test_switch_auto_to_manual(self):
        svc = ApprovalService(mode=ApprovalMode.AUTO)
        assert svc.needs_approval("write_file") is False

        svc.mode = ApprovalMode.MANUAL
        assert svc.needs_approval("write_file") is True

    def test_switch_manual_to_auto(self):
        svc = ApprovalService(mode=ApprovalMode.MANUAL)
        assert svc.needs_approval("write_file") is True

        svc.mode = ApprovalMode.AUTO
        assert svc.needs_approval("write_file") is False
