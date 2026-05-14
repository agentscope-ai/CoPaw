# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pytest

from qwenpaw.tunnel import cloudflare


class FakeBinaryManager:
    def __init__(self, path: str = "cloudflared") -> None:
        self.path = path

    async def get_binary_path(self) -> str:
        return self.path


class FakeStderr:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = list(lines)

    async def readline(self) -> bytes:
        if self._lines:
            return self._lines.pop(0)
        return b""


class FakeProcess:
    def __init__(
        self,
        stderr_lines: list[bytes] | None = None,
        pid: int = 1234,
    ) -> None:
        self.pid = pid
        self.stderr = FakeStderr(stderr_lines or [])
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    async def wait(self) -> int | None:
        return self.returncode


async def test_start_launches_cloudflared_and_sets_info(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Any, ...]] = []
    process = FakeProcess(pid=9876)

    async def fake_create_subprocess_exec(*args: Any, **_kwargs: Any):
        calls.append(args)
        return process

    async def fake_wait_for_url(timeout: float) -> str:
        assert timeout == 30
        return "https://abc123.trycloudflare.com"

    async def fake_monitor() -> None:
        return None

    monkeypatch.setattr(
        cloudflare.asyncio,
        "create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    driver = cloudflare.CloudflareTunnelDriver(FakeBinaryManager("cf"))
    monkeypatch.setattr(driver, "_wait_for_url", fake_wait_for_url)
    monkeypatch.setattr(driver, "_monitor", fake_monitor)

    info = await driver.start(8088)

    assert calls == [("cf", "tunnel", "--url", "http://localhost:8088")]
    assert info.public_url == "https://abc123.trycloudflare.com"
    assert info.public_wss_url == "wss://abc123.trycloudflare.com"
    assert info.pid == 9876
    assert driver.get_public_url() == info.public_url
    assert driver.get_info() == info
    assert await driver.health_check() is True

    await driver.stop()


async def test_start_stops_process_when_url_is_not_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = FakeProcess(pid=100)

    async def fake_create_subprocess_exec(*_args: Any, **_kwargs: Any):
        return process

    async def fake_wait_for_url(timeout: float) -> None:
        assert timeout == 30
        return None

    monkeypatch.setattr(
        cloudflare.asyncio,
        "create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    driver = cloudflare.CloudflareTunnelDriver(FakeBinaryManager())
    monkeypatch.setattr(driver, "_wait_for_url", fake_wait_for_url)

    with pytest.raises(RuntimeError, match="did not produce a tunnel URL"):
        await driver.start(8088)

    assert process.terminated is True
    assert driver.get_info() is None


async def test_start_restarts_existing_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_process = FakeProcess(pid=1)
    new_process = FakeProcess(pid=2)
    processes = [new_process]

    async def fake_create_subprocess_exec(*_args: Any, **_kwargs: Any):
        return processes.pop(0)

    async def fake_wait_for_url(timeout: float) -> str:
        assert timeout == 30
        return "https://next.trycloudflare.com"

    async def fake_monitor() -> None:
        return None

    monkeypatch.setattr(
        cloudflare.asyncio,
        "create_subprocess_exec",
        fake_create_subprocess_exec,
    )
    driver = cloudflare.CloudflareTunnelDriver(FakeBinaryManager())
    driver._process = old_process  # pylint: disable=protected-access
    monkeypatch.setattr(driver, "_wait_for_url", fake_wait_for_url)
    monkeypatch.setattr(driver, "_monitor", fake_monitor)

    info = await driver.start(9000)

    assert old_process.terminated is True
    assert info.pid == 2
    await driver.stop()


async def test_wait_for_url_extracts_trycloudflare_url() -> None:
    driver = cloudflare.CloudflareTunnelDriver(FakeBinaryManager())
    driver._process = FakeProcess(  # pylint: disable=protected-access
        [
            b"info: starting\n",
            b"https://abc-123.trycloudflare.com is ready\n",
        ],
    )

    assert (
        await driver._wait_for_url(timeout=1)
        == "https://abc-123.trycloudflare.com"
    )


async def test_wait_for_url_returns_none_without_process_or_stderr() -> None:
    driver = cloudflare.CloudflareTunnelDriver(FakeBinaryManager())

    assert await driver._wait_for_url(timeout=0.1) is None

    driver._process = FakeProcess()  # pylint: disable=protected-access
    driver._process.stderr = None

    assert await driver._wait_for_url(timeout=0.1) is None


async def test_stop_kills_process_after_graceful_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = FakeProcess()
    driver = cloudflare.CloudflareTunnelDriver(FakeBinaryManager())
    driver._process = process  # pylint: disable=protected-access

    async def fake_wait_for(awaitable: Any, timeout: float) -> None:
        awaitable.close()
        assert timeout == 5
        raise asyncio.TimeoutError

    monkeypatch.setattr(cloudflare.asyncio, "wait_for", fake_wait_for)

    await driver.stop()

    assert process.terminated is True
    assert process.killed is True
    assert driver.get_info() is None


async def test_monitor_clears_info_after_process_exits() -> None:
    process = FakeProcess()
    process.returncode = 1
    driver = cloudflare.CloudflareTunnelDriver(FakeBinaryManager())
    driver._process = process  # pylint: disable=protected-access
    driver._info = cloudflare.TunnelInfo(  # pylint: disable=protected-access
        public_url="https://dead.trycloudflare.com",
        public_wss_url="wss://dead.trycloudflare.com",
        started_at=datetime.now(timezone.utc),
        pid=process.pid,
    )

    await driver._monitor()

    assert driver.get_info() is None
