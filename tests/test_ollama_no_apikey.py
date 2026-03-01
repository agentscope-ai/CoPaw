# -*- coding: utf-8 -*-
"""Regression tests for issue #165: Ollama (no API key) model creation."""
import asyncio
from unittest.mock import patch, MagicMock

from agentscope.model import OpenAIChatModel

from copaw.agents.model_factory import (
    _create_remote_model_instance,
    _create_formatter_instance,
    create_model_and_formatter,
)
from copaw.providers.models import ResolvedModelConfig


def test_ollama_no_apikey_uses_base_url():
    """Providers with base_url but no api_key should not fall back to DashScope."""
    cfg = ResolvedModelConfig(
        model="qwen3:0.6b",
        base_url="http://localhost:11434/v1",
        api_key="",
        is_local=False,
    )
    model = _create_remote_model_instance(cfg, OpenAIChatModel)

    assert model.model_name == "qwen3:0.6b", (
        f"Expected qwen3:0.6b, got {model.model_name}"
    )
    assert "localhost:11434" in str(model.client._base_url), (
        f"Expected Ollama base_url, got {model.client._base_url}"
    )
    print("✅ PASS — Ollama config with base_url but no api_key works")


def test_dashscope_fallback_still_works():
    """When both api_key and base_url are empty, should still fall back to DashScope."""
    cfg = ResolvedModelConfig(
        model="",
        base_url="",
        api_key="",
        is_local=False,
    )
    model = _create_remote_model_instance(cfg, OpenAIChatModel)

    assert model.model_name == "qwen3-max", (
        f"Expected DashScope fallback model qwen3-max, got {model.model_name}"
    )
    print("✅ PASS — DashScope fallback still works when no config")


def test_none_config_falls_back():
    """None config should fall back to DashScope."""
    model = _create_remote_model_instance(None, OpenAIChatModel)

    assert model.model_name == "qwen3-max", (
        f"Expected DashScope fallback, got {model.model_name}"
    )
    print("✅ PASS — None config falls back to DashScope")


def test_apikey_provider_still_works():
    """Providers with api_key (e.g. Kimi, DashScope) should still work."""
    cfg = ResolvedModelConfig(
        model="kimi-k2.5",
        base_url="https://api.moonshot.cn/v1",
        api_key="sk-test-key",
        is_local=False,
    )
    model = _create_remote_model_instance(cfg, OpenAIChatModel)

    assert model.model_name == "kimi-k2.5", (
        f"Expected kimi-k2.5, got {model.model_name}"
    )
    assert "moonshot" in str(model.client._base_url), (
        f"Expected Kimi base_url, got {model.client._base_url}"
    )
    print("✅ PASS — API key provider still works correctly")


def test_full_pipeline_with_ollama_config():
    """Full create_model_and_formatter with Ollama-like config."""
    cfg = ResolvedModelConfig(
        model="qwen3:0.6b",
        base_url="http://localhost:11434/v1",
        api_key="",
        is_local=False,
    )
    model, formatter = create_model_and_formatter(cfg)

    assert model.model_name == "qwen3:0.6b"
    assert formatter is not None
    print("✅ PASS — Full pipeline works with Ollama config")


if __name__ == "__main__":
    test_ollama_no_apikey_uses_base_url()
    test_dashscope_fallback_still_works()
    test_none_config_falls_back()
    test_apikey_provider_still_works()
    test_full_pipeline_with_ollama_config()
    print("\nAll tests passed!")
