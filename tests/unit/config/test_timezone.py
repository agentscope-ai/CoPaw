# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import pytest

from qwenpaw.config import timezone as timezone_config


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Asia/Jakarta", "Asia/Jakarta"),
        ("Asia/Calcutta", "Asia/Kolkata"),
        ("Europe/Kiev", "Europe/Kyiv"),
        ("PRC", "Asia/Shanghai"),
        ("", None),
        ("Not/AZone", None),
    ],
)
def test_normalize_tz_validates_and_maps_aliases(
    name: str,
    expected: str | None,
) -> None:
    assert timezone_config.normalize_tz(name) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Asia/Jakarta", True),
        ("UTC", False),
        ("", False),
        (None, False),
    ],
)
def test_is_iana_requires_slash(name: str | None, expected: bool) -> None:
    assert timezone_config._is_iana(name) is expected


def test_probe_env_returns_only_iana_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TZ", "Asia/Jakarta")
    assert timezone_config._probe_env() == "Asia/Jakarta"

    monkeypatch.setenv("TZ", "UTC")
    assert timezone_config._probe_env() is None

    monkeypatch.delenv("TZ", raising=False)
    assert timezone_config._probe_env() is None


def test_probe_localtime_link_extracts_zoneinfo_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        timezone_config.os,
        "readlink",
        lambda _path: "/usr/share/zoneinfo/Asia/Jakarta",
    )

    assert timezone_config._probe_localtime_link() == "Asia/Jakarta"


def test_probe_localtime_link_ignores_plain_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        timezone_config.os,
        "readlink",
        lambda _path: "/etc/localtime",
    )

    assert timezone_config._probe_localtime_link() is None


def test_detect_system_timezone_inner_uses_first_normalized_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(timezone_config, "_probe_python", lambda: "Not/AZone")
    monkeypatch.setattr(timezone_config, "_probe_env", lambda: "PRC")
    monkeypatch.setattr(
        timezone_config,
        "_probe_windows_registry",
        lambda: "America/New_York",
    )
    monkeypatch.setattr(
        timezone_config,
        "_probe_etc_timezone",
        lambda: "Europe/London",
    )
    monkeypatch.setattr(timezone_config.os, "name", "nt")

    assert timezone_config._detect_system_timezone_inner() == "Asia/Shanghai"


def test_detect_system_timezone_inner_falls_back_to_utc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(timezone_config, "_probe_python", lambda: None)
    monkeypatch.setattr(timezone_config, "_probe_env", lambda: "Invalid/Zone")
    monkeypatch.setattr(
        timezone_config, "_probe_windows_registry", lambda: None
    )
    monkeypatch.setattr(timezone_config.os, "name", "nt")

    assert timezone_config._detect_system_timezone_inner() == "UTC"


def test_detect_system_timezone_never_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail() -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(timezone_config, "_detect_system_timezone_inner", fail)

    assert timezone_config.detect_system_timezone() == "UTC"
