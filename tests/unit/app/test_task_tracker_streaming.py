# -*- coding: utf-8 -*-
"""Streaming behavior tests for TaskTracker."""
from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _import_module_directly(module_name: str, file_path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_SRC = Path(__file__).resolve().parents[3] / "src"
_task_tracker_mod = _import_module_directly(
    "_test_task_tracker_streaming",
    str(_SRC / "qwenpaw" / "app" / "runner" / "task_tracker.py"),
)
TaskTracker = _task_tracker_mod.TaskTracker


@pytest.mark.asyncio
async def test_attach_replays_buffer_for_reconnect() -> None:
    """Reconnects replay buffered events and follow live ones."""
    tracker = TaskTracker()
    gate = asyncio.Event()

    async def stream(payload):
        del payload
        yield "data: first\n\n"
        await gate.wait()
        yield "data: second\n\n"

    first_queue, is_new = await tracker.attach_or_start("chat-1", {}, stream)
    assert is_new is True
    assert await asyncio.wait_for(first_queue.get(), timeout=1.0) == (
        "data: first\n\n"
    )

    reconnect_queue = await tracker.attach("chat-1")
    assert reconnect_queue is not None
    assert await asyncio.wait_for(reconnect_queue.get(), timeout=1.0) == (
        "data: first\n\n"
    )

    gate.set()
    assert await asyncio.wait_for(first_queue.get(), timeout=1.0) == (
        "data: second\n\n"
    )
    assert await asyncio.wait_for(reconnect_queue.get(), timeout=1.0) == (
        "data: second\n\n"
    )
    assert await asyncio.wait_for(first_queue.get(), timeout=1.0) is None
    assert await asyncio.wait_for(reconnect_queue.get(), timeout=1.0) is None


@pytest.mark.asyncio
async def test_attach_or_start_existing_run_has_no_replay() -> None:
    """Duplicate submit attachments should not replay buffered events."""
    tracker = TaskTracker()
    gate = asyncio.Event()

    async def stream(payload):
        del payload
        yield "data: first\n\n"
        await gate.wait()
        yield "data: second\n\n"

    first_queue, is_new = await tracker.attach_or_start("chat-1", {}, stream)
    assert is_new is True
    assert await asyncio.wait_for(first_queue.get(), timeout=1.0) == (
        "data: first\n\n"
    )

    duplicate_queue, duplicate_is_new = await tracker.attach_or_start(
        "chat-1",
        {},
        stream,
    )
    assert duplicate_is_new is False
    assert duplicate_queue.empty()

    gate.set()
    assert await asyncio.wait_for(first_queue.get(), timeout=1.0) == (
        "data: second\n\n"
    )
    assert await asyncio.wait_for(duplicate_queue.get(), timeout=1.0) == (
        "data: second\n\n"
    )
    assert await asyncio.wait_for(first_queue.get(), timeout=1.0) is None
    assert await asyncio.wait_for(duplicate_queue.get(), timeout=1.0) is None
