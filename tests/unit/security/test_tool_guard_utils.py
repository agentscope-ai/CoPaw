# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

from types import SimpleNamespace

import pytest

from qwenpaw.security.tool_guard import utils
from qwenpaw.security.tool_guard.models import (
    GuardFinding,
    GuardSeverity,
    GuardThreatCategory,
    ToolGuardResult,
)


@pytest.fixture(autouse=True)
def clean_tool_guard_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(utils.EnvVarLoader, "get_str", lambda _key: "")
    monkeypatch.setattr(utils, "_load_config_tool_guard", lambda: None)


def test_resolve_guarded_tools_user_defined_overrides_env_and_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        utils.EnvVarLoader,
        "get_str",
        lambda _key: "all",
    )
    monkeypatch.setattr(
        utils,
        "_load_config_tool_guard",
        lambda: SimpleNamespace(guarded_tools=["write_file"]),
    )

    assert utils.resolve_guarded_tools([" read_file ", ""]) == {"read_file"}


def test_resolve_guarded_tools_env_all_and_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(utils.EnvVarLoader, "get_str", lambda _key: "all")
    assert utils.resolve_guarded_tools() is None

    monkeypatch.setattr(utils.EnvVarLoader, "get_str", lambda _key: "off")
    assert utils.resolve_guarded_tools() == set()


def test_resolve_guarded_tools_uses_config_before_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        utils,
        "_load_config_tool_guard",
        lambda: SimpleNamespace(
            guarded_tools=["execute_shell_command", " read_file "],
        ),
    )

    assert utils.resolve_guarded_tools() == {
        "execute_shell_command",
        "read_file",
    }


def test_resolve_guarded_tools_default_covers_high_risk_tools() -> None:
    guarded = utils.resolve_guarded_tools()

    assert isinstance(guarded, set)
    assert "execute_shell_command" in guarded
    assert "read_file" in guarded
    assert "write_file" in guarded


def test_resolve_denied_tools_trims_env_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        utils.EnvVarLoader,
        "get_str",
        lambda _key: " write_file, ,execute_shell_command ",
    )

    assert utils.resolve_denied_tools() == {
        "write_file",
        "execute_shell_command",
    }


def test_resolve_auto_denied_rules_trims_config_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        utils,
        "_load_config_tool_guard",
        lambda: SimpleNamespace(
            auto_denied_rules=[" dangerous_shell ", "", "path_traversal"],
        ),
    )

    assert utils.resolve_auto_denied_rules() == {
        "dangerous_shell",
        "path_traversal",
    }


def test_log_findings_uses_warning_for_high_severity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warnings: list[str] = []
    infos: list[str] = []
    monkeypatch.setattr(
        utils.logger,
        "warning",
        lambda message, *args: warnings.append(message % args),
    )
    monkeypatch.setattr(
        utils.logger,
        "info",
        lambda message, *args: infos.append(message % args),
    )
    result = ToolGuardResult(
        tool_name="execute_shell_command",
        params={"command": "rm -rf /tmp/demo"},
        findings=[
            GuardFinding(
                id="finding-1",
                rule_id="dangerous_shell",
                category=GuardThreatCategory.COMMAND_INJECTION,
                severity=GuardSeverity.HIGH,
                title="Dangerous shell command",
                description="Command may be destructive",
                tool_name="execute_shell_command",
                param_name="command",
                matched_value="rm -rf",
            ),
        ],
        guard_duration_seconds=0.25,
    )

    utils.log_findings("execute_shell_command", result)

    assert any("dangerous_shell" in msg for msg in warnings)
    assert any("max_severity=HIGH" in msg for msg in warnings)
    assert not infos


def test_log_findings_uses_info_for_safe_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    infos: list[str] = []
    monkeypatch.setattr(
        utils.logger,
        "info",
        lambda message, *args: infos.append(message % args),
    )
    result = ToolGuardResult(
        tool_name="read_file",
        params={"path": "notes.md"},
        findings=[],
        guard_duration_seconds=0.01,
    )

    utils.log_findings("read_file", result)

    assert any("max_severity=SAFE" in message for message in infos)
