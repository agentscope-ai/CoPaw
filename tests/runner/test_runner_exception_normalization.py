# -*- coding: utf-8 -*-

from copaw.app.runner.runner import _normalize_user_facing_exception


def _make_exception(class_name: str, message: str) -> Exception:
    cls = type(class_name, (Exception,), {})
    return cls(message)


def test_normalize_timeout_exception_to_runtime_error() -> None:
    exc = _make_exception("APITimeoutError", "Request timed out.")
    normalized = _normalize_user_facing_exception(exc)

    assert isinstance(normalized, RuntimeError)
    assert "timed out" in str(normalized).lower()


def test_keep_unknown_exception_unchanged() -> None:
    exc = ValueError("bad input")
    normalized = _normalize_user_facing_exception(exc)

    assert normalized is exc
