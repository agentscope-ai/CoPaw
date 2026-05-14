# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import pytest

from qwenpaw.providers import rate_limiter


@pytest.fixture(autouse=True)
def reset_global_limiter() -> None:
    rate_limiter.reset_rate_limiter()


def _monotonic_sequence(*values: float):
    iterator = iter(values)
    current = values[-1]

    def fake_monotonic() -> float:
        nonlocal current
        try:
            current = next(iterator)
        except StopIteration:
            pass
        return current

    return fake_monotonic


async def test_acquire_and_release_update_stats() -> None:
    limiter = rate_limiter.LLMRateLimiter(
        max_concurrent=2,
        max_qpm=0,
        default_pause_seconds=5.0,
        jitter_range=0.0,
    )

    await limiter.acquire()
    stats = limiter.stats()

    assert stats["current_in_flight"] == 1
    assert stats["current_available"] == 1
    assert stats["total_acquired"] == 1

    limiter.release()
    stats = limiter.stats()
    assert stats["current_in_flight"] == 0
    assert stats["current_available"] == 2


async def test_report_rate_limit_sets_pause_and_does_not_shorten(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rate_limiter.time,
        "monotonic",
        _monotonic_sequence(100.0, 101.0),
    )
    limiter = rate_limiter.LLMRateLimiter(
        default_pause_seconds=5.0,
        jitter_range=0.0,
    )

    await limiter.report_rate_limit(retry_after=10.0)
    await limiter.report_rate_limit(retry_after=1.0)

    stats = limiter.stats()
    assert stats["is_paused"] is True
    assert stats["pause_remaining_s"] == 9.0
    assert stats["total_rate_limited"] == 1


async def test_acquire_waits_for_active_pause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(
        rate_limiter.time,
        "monotonic",
        _monotonic_sequence(90.0, 101.0),
    )
    monkeypatch.setattr(rate_limiter.random, "uniform", lambda *_args: 0.0)
    monkeypatch.setattr(rate_limiter.asyncio, "sleep", fake_sleep)
    limiter = rate_limiter.LLMRateLimiter(
        max_qpm=0,
        default_pause_seconds=5.0,
        jitter_range=0.0,
    )
    limiter._pause_until = 100.0

    await limiter.acquire()

    assert sleeps == [10.0]
    assert limiter.stats()["total_paused"] == 1
    limiter.release()


async def test_qpm_slot_prunes_expired_timestamps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rate_limiter.time, "monotonic", lambda: 100.0)
    limiter = rate_limiter.LLMRateLimiter(max_qpm=2)
    limiter._request_times.extend([30.0, 50.0])

    await limiter._acquire_qpm_slot()

    assert list(limiter._request_times) == [50.0, 100.0]


async def test_qpm_slot_waits_until_window_has_room(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(
        rate_limiter.time,
        "monotonic",
        _monotonic_sequence(120.0, 160.1),
    )
    monkeypatch.setattr(rate_limiter.asyncio, "sleep", fake_sleep)
    limiter = rate_limiter.LLMRateLimiter(max_qpm=1)
    limiter._request_times.append(100.0)

    await limiter._acquire_qpm_slot()

    assert sleeps == [40.05]
    assert list(limiter._request_times) == [160.1]
    assert limiter.stats()["total_qpm_waited"] == 1


async def test_get_rate_limiter_returns_singleton_until_reset() -> None:
    first = await rate_limiter.get_rate_limiter(
        max_concurrent=1,
        max_qpm=2,
        default_pause_seconds=3.0,
        jitter_range=0.0,
    )
    second = await rate_limiter.get_rate_limiter(max_concurrent=9)

    assert first is second
    assert second.stats()["max_concurrent"] == 1
    assert second.stats()["max_qpm"] == 2

    rate_limiter.reset_rate_limiter()
    third = await rate_limiter.get_rate_limiter(max_concurrent=4)
    assert third is not first
    assert third.stats()["max_concurrent"] == 4
