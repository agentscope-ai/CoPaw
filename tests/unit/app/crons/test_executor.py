# -*- coding: utf-8 -*-
"""Tests for cron job execution."""
from __future__ import annotations

# pylint: disable=too-few-public-methods

from types import SimpleNamespace
from typing import Any, AsyncGenerator

import pytest

from qwenpaw.app.crons import executor as executor_module
from qwenpaw.app.crons.executor import CronExecutor
from qwenpaw.app.crons.models import CronJobSpec


class DummyRunner:
    """Runner stub that records requests passed to stream_query."""

    def __init__(self, chat_manager: Any | None = None) -> None:
        self.requests: list[dict[str, Any]] = []
        self._chat_manager = chat_manager

    async def stream_query(
        self,
        request: dict[str, Any],
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Record one request and yield one event."""
        self.requests.append(dict(request))
        yield {"type": "message"}


class DummyChannelManager:
    """Channel manager stub that records outbound events."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def send_event(self, **kwargs: Any) -> None:
        """Record an outbound event."""
        self.events.append(kwargs)


class DummyChatManager:
    """Chat manager stub that returns active chat specs."""

    def __init__(self, session_ids: list[str]) -> None:
        self.session_ids = session_ids

    async def list_chats(
        self,
        user_id: str | None = None,  # pylint: disable=unused-argument
        channel: str | None = None,  # pylint: disable=unused-argument
    ) -> list[Any]:
        """Return active chat records."""
        return [
            SimpleNamespace(session_id=session_id)
            for session_id in self.session_ids
        ]


def _build_agent_job(*, share_session: bool) -> CronJobSpec:
    return CronJobSpec(
        id="job-1",
        name="Daily agent task",
        schedule={
            "type": "cron",
            "cron": "0 9 * * *",
        },
        task_type="agent",
        request={
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "hello"}],
                },
            ],
        },
        dispatch={
            "type": "channel",
            "channel": "console",
            "target": {
                "user_id": "user-1",
                "session_id": "session-1",
            },
            "mode": "final",
        },
        runtime={
            "share_session": share_session,
            "timeout_seconds": 5,
        },
    )


@pytest.fixture(autouse=True)
def stub_trace_store(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid filesystem trace writes in CronExecutor tests."""

    async def _read_session_messages(**_: Any) -> list[dict[str, Any]]:
        return []

    async def _create_trace(*_: Any, **__: Any) -> None:
        return None

    async def _append_trace_from_session_delta(
        **_: Any,
    ) -> list[dict[str, Any]]:
        return []

    async def _finalize_trace(*_: Any, **__: Any) -> None:
        return None

    monkeypatch.setattr(
        executor_module,
        "read_session_messages",
        _read_session_messages,
    )
    monkeypatch.setattr(executor_module, "create_trace", _create_trace)
    monkeypatch.setattr(
        executor_module,
        "append_trace_from_session_delta",
        _append_trace_from_session_delta,
    )
    monkeypatch.setattr(executor_module, "finalize_trace", _finalize_trace)


@pytest.mark.asyncio
async def test_share_session_uses_target_session() -> None:
    """Shared cron jobs reuse the configured target session."""
    runner = DummyRunner()
    executor = CronExecutor(
        runner=runner,
        channel_manager=DummyChannelManager(),
    )

    await executor.execute(_build_agent_job(share_session=True))

    assert runner.requests[0]["session_id"] == "session-1"


@pytest.mark.asyncio
async def test_share_session_reuses_existing_target_session() -> None:
    """Shared cron jobs reuse target sessions still present in chats."""
    runner = DummyRunner(chat_manager=DummyChatManager(["session-1"]))
    executor = CronExecutor(
        runner=runner,
        channel_manager=DummyChannelManager(),
    )

    await executor.execute(_build_agent_job(share_session=True))

    assert runner.requests[0]["session_id"] == "session-1"


@pytest.mark.asyncio
async def test_share_session_uses_fresh_run_when_target_deleted() -> None:
    """Deleted target sessions are not resurrected by shared cron jobs."""
    runner = DummyRunner(chat_manager=DummyChatManager([]))
    executor = CronExecutor(
        runner=runner,
        channel_manager=DummyChannelManager(),
    )

    await executor.execute(_build_agent_job(share_session=True))

    session_id = runner.requests[0]["session_id"]
    assert session_id != "session-1"
    assert session_id.startswith("session-1:cron:job-1:run:")


@pytest.mark.asyncio
async def test_non_shared_session_is_unique_per_execution() -> None:
    """Non-shared cron jobs create a fresh session on every run."""
    runner = DummyRunner()
    executor = CronExecutor(
        runner=runner,
        channel_manager=DummyChannelManager(),
    )
    job = _build_agent_job(share_session=False)

    await executor.execute(job)
    await executor.execute(job)

    session_ids = [request["session_id"] for request in runner.requests]
    assert len(set(session_ids)) == 2
    assert all(
        session_id.startswith("session-1:cron:job-1:run:")
        for session_id in session_ids
    )
