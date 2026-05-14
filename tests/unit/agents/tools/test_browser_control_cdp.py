# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Tests for browser CDP connection handling."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from qwenpaw.agents.tools import browser_control


def _response_text(response) -> str:
    block = response.content[0]
    if isinstance(block, dict):
        return str(block["text"])
    return str(block.text)


@pytest.mark.asyncio
async def test_connect_over_cdp_uses_bounded_timeout(monkeypatch):
    captured: dict[str, object] = {}

    class FakeChromium:
        async def connect_over_cdp(self, cdp_url: str):
            captured["cdp_url"] = cdp_url
            return "browser"

    async def fake_wait_for(awaitable, timeout):
        captured["timeout"] = timeout
        return await awaitable

    monkeypatch.setattr(browser_control.asyncio, "wait_for", fake_wait_for)

    result = await browser_control._connect_over_cdp_with_timeout(
        SimpleNamespace(chromium=FakeChromium()),
        "http://127.0.0.1:9222",
        timeout=3.5,
    )

    assert result == "browser"
    assert captured == {
        "cdp_url": "http://127.0.0.1:9222",
        "timeout": 3.5,
    }


@pytest.mark.asyncio
async def test_connect_cdp_timeout_stops_playwright(monkeypatch, tmp_path):
    class FakePlaywright:
        def __init__(self):
            self.stopped = False

        async def stop(self):
            self.stopped = True

    class FakePlaywrightStarter:
        def __init__(self, playwright):
            self.playwright = playwright

        async def start(self):
            return self.playwright

    playwright = FakePlaywright()

    def fake_async_playwright():
        return FakePlaywrightStarter(playwright)

    async def raise_timeout(_pw, _cdp_url):
        raise asyncio.TimeoutError

    monkeypatch.setattr(
        browser_control,
        "_ensure_playwright_async",
        lambda: fake_async_playwright,
    )
    monkeypatch.setattr(
        browser_control,
        "_connect_over_cdp_with_timeout",
        raise_timeout,
    )

    state = browser_control._make_fresh_state("test", str(tmp_path))

    response = await browser_control._action_connect_cdp(
        state,
        "http://127.0.0.1:9222",
    )
    payload = json.loads(_response_text(response))

    assert payload["ok"] is False
    assert "timed out after 15s" in payload["error"]
    assert "http://127.0.0.1:9222" in payload["error"]
    assert playwright.stopped is True
    assert state["playwright"] is None
