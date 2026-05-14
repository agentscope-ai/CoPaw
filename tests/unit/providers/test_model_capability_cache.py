# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

from typing import Generator

import pytest

from qwenpaw.providers import model_capability_cache


@pytest.fixture(autouse=True)
def reset_singleton() -> Generator[None, None, None]:
    model_capability_cache.ModelCapabilityCache._instance = None
    yield
    model_capability_cache.ModelCapabilityCache._instance = None


def test_get_instance_returns_process_singleton() -> None:
    first = model_capability_cache.ModelCapabilityCache.get_instance()
    second = model_capability_cache.ModelCapabilityCache.get_instance()

    assert first is second
    assert model_capability_cache.get_capability_cache() is first


def test_learn_and_get_returns_cached_value_or_default() -> None:
    cache = model_capability_cache.ModelCapabilityCache()

    assert cache.get("openai:gpt", "rejects_media") is None
    assert cache.get("openai:gpt", "rejects_media", False) is False

    cache.learn("openai:gpt", "rejects_media", True)
    cache.learn("openai:gpt", "needs_reasoning_content", False)

    assert cache.get("openai:gpt", "rejects_media") is True
    assert cache.get("openai:gpt", "needs_reasoning_content") is False
    assert (
        cache.get("anthropic:claude", "rejects_media", "missing") == "missing"
    )


def test_learn_updates_value_and_logs_only_when_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = model_capability_cache.ModelCapabilityCache()
    messages: list[str] = []

    def capture_info(message: str, *args: object) -> None:
        messages.append(message % args)

    monkeypatch.setattr(model_capability_cache.logger, "info", capture_info)

    cache.learn("model-a", "rejects_media", True)
    cache.learn("model-a", "rejects_media", True)
    cache.learn("model-a", "rejects_media", False)

    assert cache.get("model-a", "rejects_media") is False
    assert messages == [
        "Learned capability for model-a: rejects_media=True",
        "Learned capability for model-a: rejects_media=False",
    ]


def test_clear_removes_single_model_or_everything() -> None:
    cache = model_capability_cache.ModelCapabilityCache()
    cache.learn("model-a", "rejects_media", True)
    cache.learn("model-b", "rejects_media", True)

    cache.clear("model-a")

    assert cache.get("model-a", "rejects_media") is None
    assert cache.get("model-b", "rejects_media") is True

    cache.clear()

    assert cache.get("model-b", "rejects_media") is None


def test_clear_unknown_model_is_noop() -> None:
    cache = model_capability_cache.ModelCapabilityCache()
    cache.learn("model-a", "rejects_media", True)

    cache.clear("missing")

    assert cache.get("model-a", "rejects_media") is True
