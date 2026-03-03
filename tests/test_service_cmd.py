# -*- coding: utf-8 -*-
from pathlib import Path

from click.testing import CliRunner

from copaw.cli.main import cli
from copaw.cli.service_cmd import (
    _parse_launchctl_print,
    _parse_systemctl_show,
    build_launchd_plist,
    build_systemd_unit,
)


def test_build_launchd_plist_contains_core_fields() -> None:
    plist = build_launchd_plist(
        label="ai.copaw.app",
        program_arguments=["/usr/bin/python3", "-m", "copaw.cli.main", "app"],
        working_directory=Path("/tmp/copaw"),
        environment={"COPAW_WORKING_DIR": "/tmp/copaw", "COPAW_LOG_LEVEL": "info"},
        stdout_path=Path("/tmp/copaw/logs/service.log"),
        stderr_path=Path("/tmp/copaw/logs/service.err.log"),
    )
    assert "<key>Label</key>" in plist
    assert "ai.copaw.app" in plist
    assert "<key>ProgramArguments</key>" in plist
    assert "copaw.cli.main" in plist
    assert "<key>EnvironmentVariables</key>" in plist
    assert "COPAW_WORKING_DIR" in plist
    assert "COPAW_LOG_LEVEL" in plist
    assert "<key>KeepAlive</key>" in plist
    assert "service.err.log" in plist


def test_build_systemd_unit_contains_exec_and_env() -> None:
    unit = build_systemd_unit(
        description="CoPaw application service",
        program_arguments=[
            "/usr/bin/python3",
            "-m",
            "copaw.cli.main",
            "app",
            "--port",
            "8088",
        ],
        working_directory=Path("/opt/copaw"),
        environment={"COPAW_WORKING_DIR": "/opt/copaw", "COPAW_LOG_LEVEL": "info"},
    )
    assert "[Service]" in unit
    assert "ExecStart=" in unit
    assert "copaw.cli.main" in unit
    assert 'Environment="COPAW_WORKING_DIR=/opt/copaw"' in unit
    assert 'Environment="COPAW_LOG_LEVEL=info"' in unit
    assert "Restart=always" in unit


def test_parse_launchctl_print_detects_running_and_pid() -> None:
    output = """
    state = running
    pid = 9527
    """
    running, pid, state = _parse_launchctl_print(output)
    assert running is True
    assert pid == 9527
    assert state == "running"


def test_parse_systemctl_show_detects_running_and_pid() -> None:
    output = """
    ActiveState=active
    MainPID=1234
    """
    running, pid, state = _parse_systemctl_show(output)
    assert running is True
    assert pid == 1234
    assert state == "active"


def test_daemon_alias_exposes_service_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["daemon", "--help"])
    assert result.exit_code == 0
    assert "install" in result.output
    assert "restart" in result.output
