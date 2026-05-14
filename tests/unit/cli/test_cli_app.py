# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import errno
import socket

import pytest
from click.testing import CliRunner

from qwenpaw.cli import app_cmd as app_cmd_module
from qwenpaw.cli.main import cli


def test_bind_preflight_detects_busy_port() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        bind_error = app_cmd_module._bind_preflight_error(
            "127.0.0.1",
            port,
        )

    assert bind_error is not None
    assert bind_error.errno == errno.EADDRINUSE


def test_app_command_reports_port_conflict_before_start(monkeypatch) -> None:
    bind_error = OSError(errno.EADDRINUSE, "Address already in use")

    monkeypatch.setattr(
        app_cmd_module,
        "_bind_preflight_error",
        lambda _host, _port: bind_error,
    )
    monkeypatch.setattr(
        app_cmd_module,
        "write_last_api",
        lambda _host, _port: pytest.fail("should not persist failed bind"),
    )
    monkeypatch.setattr(
        app_cmd_module.uvicorn,
        "run",
        lambda *args, **kwargs: pytest.fail("should not start uvicorn"),
    )

    result = CliRunner().invoke(cli, ["app", "--port", "8088"])

    assert result.exit_code != 0
    assert "127.0.0.1:8088 is already in use" in result.output
    assert "qwenpaw shutdown" in result.output
    assert "qwenpaw app --port 8090" in result.output


def test_app_command_starts_when_port_is_available(monkeypatch) -> None:
    writes: list[tuple[str, int]] = []
    runs: list[tuple[tuple[object, ...], dict[str, object]]] = []

    monkeypatch.setattr(
        app_cmd_module,
        "_bind_preflight_error",
        lambda _host, _port: None,
    )
    monkeypatch.setattr(app_cmd_module, "setup_logger", lambda _level: None)
    monkeypatch.setattr(
        app_cmd_module,
        "write_last_api",
        lambda host, port: writes.append((host, port)),
    )
    monkeypatch.setattr(
        app_cmd_module.uvicorn,
        "run",
        lambda *args, **kwargs: runs.append((args, kwargs)),
    )

    result = CliRunner().invoke(
        cli,
        ["app", "--host", "0.0.0.0", "--port", "8090"],
    )

    assert result.exit_code == 0
    assert writes == [("127.0.0.1", 8090)]
    assert runs
    kwargs = runs[0][1]
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 8090
