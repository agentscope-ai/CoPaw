# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import json
import subprocess

import pytest

from qwenpaw.utils import telemetry


def test_has_telemetry_been_collected_uses_collected_versions(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(telemetry, "_get_current_version", lambda: "1.2.0")
    marker = tmp_path / telemetry.TELEMETRY_MARKER_FILE
    marker.write_text(
        json.dumps(
            {
                "qwenpaw_version": "1.1.0",
                "collected_versions": ["1.1.0", "1.2.0"],
            },
        ),
        encoding="utf-8",
    )

    assert telemetry.has_telemetry_been_collected(tmp_path) is True


def test_has_telemetry_been_collected_migrates_v1_marker(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(telemetry, "_get_current_version", lambda: "1.1.5")
    marker = tmp_path / telemetry.TELEMETRY_MARKER_FILE
    marker.write_text(
        json.dumps({"qwenpaw_version": "1.1.5"}),
        encoding="utf-8",
    )

    assert telemetry.has_telemetry_been_collected(tmp_path) is True


def test_has_telemetry_been_collected_handles_missing_or_invalid_marker(
    tmp_path,
) -> None:
    assert telemetry.has_telemetry_been_collected(tmp_path) is False

    marker = tmp_path / telemetry.TELEMETRY_MARKER_FILE
    marker.write_text("{not-json", encoding="utf-8")

    assert telemetry.has_telemetry_been_collected(tmp_path) is False


def test_is_telemetry_opted_out_only_for_explicit_true(tmp_path) -> None:
    marker = tmp_path / telemetry.TELEMETRY_MARKER_FILE
    marker.write_text(
        json.dumps({"opted_out": "true"}),
        encoding="utf-8",
    )

    assert telemetry.is_telemetry_opted_out(tmp_path) is False

    marker.write_text(
        json.dumps({"opted_out": True}),
        encoding="utf-8",
    )

    assert telemetry.is_telemetry_opted_out(tmp_path) is True


def test_mark_telemetry_collected_migrates_old_version_and_preserves_opt_out(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(telemetry, "_get_current_version", lambda: "1.2.0")
    marker = tmp_path / telemetry.TELEMETRY_MARKER_FILE
    marker.write_text(
        json.dumps(
            {
                "qwenpaw_version": "1.1.0",
                "opted_out": True,
            },
        ),
        encoding="utf-8",
    )

    telemetry.mark_telemetry_collected(tmp_path)

    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data["qwenpaw_version"] == "1.2.0"
    assert data["collected_versions"] == ["1.1.0", "1.2.0"]
    assert data["opted_out"] is True
    assert data["version"] == "1.3"


def test_mark_telemetry_collected_sets_opt_out_on_new_marker(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(telemetry, "_get_current_version", lambda: "1.2.0")

    telemetry.mark_telemetry_collected(tmp_path, opted_out=True)

    data = json.loads(
        (tmp_path / telemetry.TELEMETRY_MARKER_FILE).read_text(
            encoding="utf-8",
        ),
    )
    assert data["collected_versions"] == ["1.2.0"]
    assert data["opted_out"] is True


def test_detect_gpu_returns_true_for_nvidia_smi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(args=["nvidia-smi"], returncode=0)

    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)

    assert telemetry._detect_gpu() is True


def test_detect_gpu_returns_true_for_apple_silicon(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)
    monkeypatch.setattr(telemetry.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(telemetry.platform, "machine", lambda: "arm64")

    assert telemetry._detect_gpu() is True


def test_detect_gpu_uses_linux_lspci(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command, **_kwargs):
        if command == ["nvidia-smi"]:
            raise FileNotFoundError
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Intel Corporation UHD Graphics VGA compatible controller",
        )

    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)
    monkeypatch.setattr(telemetry.platform, "system", lambda: "Linux")
    monkeypatch.setattr(telemetry.platform, "machine", lambda: "x86_64")

    assert telemetry._detect_gpu() is True


def test_detect_gpu_uses_windows_wmic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command, **_kwargs):
        if command == ["nvidia-smi"]:
            raise FileNotFoundError
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Name\r\nNVIDIA GeForce RTX 4090\r\n",
        )

    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)
    monkeypatch.setattr(telemetry.platform, "system", lambda: "Windows")
    monkeypatch.setattr(telemetry.platform, "machine", lambda: "AMD64")

    assert telemetry._detect_gpu() is True


def test_detect_gpu_returns_false_when_no_detector_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)
    monkeypatch.setattr(telemetry.platform, "system", lambda: "FreeBSD")
    monkeypatch.setattr(telemetry.platform, "machine", lambda: "x86_64")

    assert telemetry._detect_gpu() is False


def test_detect_gpu_returns_unknown_for_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*_args, **_kwargs):
        raise RuntimeError("subprocess failed")

    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)

    assert telemetry._detect_gpu() == "unknown"
