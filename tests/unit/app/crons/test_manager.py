# -*- coding: utf-8 -*-
"""Tests for CronManager execution coordination."""
from __future__ import annotations

# pylint: disable=too-few-public-methods,protected-access

import asyncio
from typing import Any

import pytest

from qwenpaw.app.crons.manager import CronManager
from qwenpaw.app.crons.models import CronExecutionRecord, CronJobSpec


class DummyRepo:
    """Repository stub for CronManager execution tests."""

    def __init__(self) -> None:
        self.history: dict[str, list[CronExecutionRecord]] = {}

    async def append_history(
        self,
        job_id: str,
        record: CronExecutionRecord,
        *,
        limit: int = 50,
    ) -> list[CronExecutionRecord]:
        """Store one history record and return the bounded history list."""
        records = self.history.setdefault(job_id, [])
        records.insert(0, record)
        del records[limit:]
        return records


def _build_job(job_id: str, *, share_session: bool) -> CronJobSpec:
    return CronJobSpec(
        id=job_id,
        name=f"Job {job_id}",
        enabled=True,
        save_result_to_inbox=False,
        schedule={"type": "cron", "cron": "0 9 * * *"},
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
            "channel": "wechat",
            "target": {
                "user_id": "user-1",
                "session_id": "shared-session",
            },
            "mode": "final",
        },
        runtime={
            "share_session": share_session,
            "max_concurrency": 1,
            "timeout_seconds": 5,
        },
    )


@pytest.mark.asyncio
async def test_shared_session_agent_jobs_are_serialized() -> None:
    """Different cron jobs sharing one session should not run together."""
    manager = CronManager(
        repo=DummyRepo(),
        runner=None,
        channel_manager=None,
    )
    running = 0
    max_running = 0
    starts: list[str] = []

    async def execute(job: CronJobSpec) -> dict[str, Any]:
        nonlocal running, max_running
        running += 1
        max_running = max(max_running, running)
        starts.append(job.id or "")
        await asyncio.sleep(0.01)
        running -= 1
        return {"delivery_status": "success"}

    manager._executor.execute = execute

    await asyncio.gather(
        manager._execute_once(_build_job("job-1", share_session=True)),
        manager._execute_once(_build_job("job-2", share_session=True)),
    )

    assert starts == ["job-1", "job-2"]
    assert max_running == 1


@pytest.mark.asyncio
async def test_non_shared_session_agent_jobs_can_run_concurrently() -> None:
    """Non-shared cron jobs should keep independent execution slots."""
    manager = CronManager(
        repo=DummyRepo(),
        runner=None,
        channel_manager=None,
    )
    running = 0
    max_running = 0
    both_started = asyncio.Event()

    async def execute(_: CronJobSpec) -> dict[str, Any]:
        nonlocal running, max_running
        running += 1
        max_running = max(max_running, running)
        if running == 2:
            both_started.set()
        await both_started.wait()
        running -= 1
        return {"delivery_status": "success"}

    manager._executor.execute = execute

    await asyncio.gather(
        manager._execute_once(_build_job("job-1", share_session=False)),
        manager._execute_once(_build_job("job-2", share_session=False)),
    )

    assert max_running == 2
