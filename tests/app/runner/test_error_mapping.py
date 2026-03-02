# -*- coding: utf-8 -*-
"""Tests for runtime exception mapping in query handler."""
from __future__ import annotations

from typing import Type

from copaw.app.runner.error_mapping import (
    AgentModelTimeoutError,
    is_model_timeout_error,
    map_query_exception,
)


OpenAITimeoutError: Type[Exception] = type(
    "APITimeoutError",
    (Exception,),
    {"__module__": "openai"},
)
HttpxReadTimeout: Type[Exception] = type(
    "ReadTimeout",
    (Exception,),
    {"__module__": "httpx"},
)


def test_map_query_exception_returns_timeout_error() -> None:
    exc = OpenAITimeoutError("Request timed out.")

    mapped = map_query_exception(exc)

    assert isinstance(mapped, AgentModelTimeoutError)
    assert "Model provider request timed out." in str(mapped)
    assert "APITimeoutError: Request timed out." in str(mapped)


def test_map_query_exception_timeout_via_cause_chain() -> None:
    try:
        try:
            raise HttpxReadTimeout("Read timed out")
        except HttpxReadTimeout as inner:
            raise RuntimeError("Model call failed") from inner
    except RuntimeError as outer:
        mapped = map_query_exception(outer)

    assert isinstance(mapped, AgentModelTimeoutError)
    assert "RuntimeError: Model call failed" in str(mapped)


def test_map_query_exception_passes_non_timeout_error() -> None:
    exc = ValueError("Invalid model name")
    mapped = map_query_exception(exc)
    assert mapped is exc


def test_plain_timeout_without_network_module_is_not_model_timeout() -> None:
    exc = TimeoutError("Tool execution timed out")
    assert not is_model_timeout_error(exc)
