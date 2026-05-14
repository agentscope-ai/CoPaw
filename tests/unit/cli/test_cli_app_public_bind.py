# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from click.testing import CliRunner

from qwenpaw.cli.app_cmd import app_cmd


def _clear_public_auth_env(monkeypatch) -> None:
    monkeypatch.delenv("QWENPAW_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("QWENPAW_TRUST_PROXY_AUTH", raising=False)


def _patch_server_start(monkeypatch) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def fake_uvicorn_run(*args: Any, **kwargs: Any) -> None:
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr("qwenpaw.cli.app_cmd.uvicorn.run", fake_uvicorn_run)
    monkeypatch.setattr(
        "qwenpaw.cli.app_cmd.write_last_api",
        lambda *args: None,
    )
    return captured


def test_app_refuses_public_bind_when_auth_is_disabled(monkeypatch) -> None:
    _clear_public_auth_env(monkeypatch)

    result = CliRunner().invoke(app_cmd, ["--host", "0.0.0.0"])

    assert result.exit_code != 0
    assert "Refusing to bind QwenPaw to non-loopback host" in result.output
    assert "QWENPAW_AUTH_ENABLED=true" in result.output
    assert "--allow-unauth-public" in result.output


def test_app_allows_public_bind_when_auth_is_enabled(monkeypatch) -> None:
    _clear_public_auth_env(monkeypatch)
    monkeypatch.setenv("QWENPAW_AUTH_ENABLED", "true")
    captured = _patch_server_start(monkeypatch)

    result = CliRunner().invoke(app_cmd, ["--host", "0.0.0.0"])

    assert result.exit_code == 0
    assert captured["kwargs"]["host"] == "0.0.0.0"


def test_app_allows_public_bind_with_proxy_auth_marker(monkeypatch) -> None:
    _clear_public_auth_env(monkeypatch)
    monkeypatch.setenv("QWENPAW_TRUST_PROXY_AUTH", "1")
    captured = _patch_server_start(monkeypatch)

    result = CliRunner().invoke(app_cmd, ["--host", "192.0.2.10"])

    assert result.exit_code == 0
    assert captured["kwargs"]["host"] == "192.0.2.10"


def test_app_allows_public_bind_with_explicit_override(monkeypatch) -> None:
    _clear_public_auth_env(monkeypatch)
    captured = _patch_server_start(monkeypatch)

    result = CliRunner().invoke(
        app_cmd,
        ["--host", "::", "--allow-unauth-public"],
    )

    assert result.exit_code == 0
    assert captured["kwargs"]["host"] == "::"


def test_app_allows_loopback_bind_without_auth(monkeypatch) -> None:
    _clear_public_auth_env(monkeypatch)
    captured = _patch_server_start(monkeypatch)

    result = CliRunner().invoke(app_cmd, ["--host", "localhost"])

    assert result.exit_code == 0
    assert captured["kwargs"]["host"] == "localhost"
