# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from qwenpaw.utils import telemetry


def test_mark_telemetry_collected_migrates_single_version_marker(
    tmp_path: Path,
    monkeypatch,
) -> None:
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
    monkeypatch.setattr(telemetry, "_get_current_version", lambda: "1.2.0")

    telemetry.mark_telemetry_collected(tmp_path)

    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data["qwenpaw_version"] == "1.2.0"
    assert data["collected_versions"] == ["1.1.0", "1.2.0"]
    assert data["opted_out"] is True


def test_has_telemetry_been_collected_uses_version_history(
    tmp_path: Path,
    monkeypatch,
) -> None:
    marker = tmp_path / telemetry.TELEMETRY_MARKER_FILE
    marker.write_text(
        json.dumps({"collected_versions": ["1.0.0", "1.2.0"]}),
        encoding="utf-8",
    )

    monkeypatch.setattr(telemetry, "_get_current_version", lambda: "1.2.0")
    assert telemetry.has_telemetry_been_collected(tmp_path) is True

    monkeypatch.setattr(telemetry, "_get_current_version", lambda: "1.3.0")
    assert telemetry.has_telemetry_been_collected(tmp_path) is False


def test_is_telemetry_opted_out_ignores_invalid_marker(tmp_path: Path) -> None:
    marker = tmp_path / telemetry.TELEMETRY_MARKER_FILE
    marker.write_text("{not json", encoding="utf-8")

    assert telemetry.is_telemetry_opted_out(tmp_path) is False


def test_collect_and_upload_telemetry_marks_after_failed_upload(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(telemetry, "get_system_info", lambda: {"os": "Linux"})
    monkeypatch.setattr(
        telemetry,
        "_upload_telemetry_sync",
        lambda data: False,
    )
    monkeypatch.setattr(telemetry, "_get_current_version", lambda: "1.2.0")

    assert telemetry.collect_and_upload_telemetry(tmp_path) is False

    marker = tmp_path / telemetry.TELEMETRY_MARKER_FILE
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data["collected_versions"] == ["1.2.0"]


def test_detect_gpu_uses_linux_lspci_when_nvidia_smi_missing(
    monkeypatch,
) -> None:
    def fake_run(command, **kwargs):
        del kwargs
        if command == ["nvidia-smi"]:
            raise FileNotFoundError
        if command == ["lspci"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="3D controller: NVIDIA Corporation Device",
            )
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(telemetry.platform, "system", lambda: "Linux")
    monkeypatch.setattr(telemetry.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)

    assert telemetry._detect_gpu() is True


def test_detect_gpu_returns_false_when_linux_gpu_commands_missing(
    monkeypatch,
) -> None:
    def fake_run(command, **kwargs):
        del command, kwargs
        raise FileNotFoundError

    monkeypatch.setattr(telemetry.platform, "system", lambda: "Linux")
    monkeypatch.setattr(telemetry.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)

    assert telemetry._detect_gpu() is False


def test_detect_gpu_treats_apple_silicon_as_gpu_available(monkeypatch) -> None:
    def fake_run(command, **kwargs):
        del command, kwargs
        raise FileNotFoundError

    monkeypatch.setattr(telemetry.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(telemetry.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)

    assert telemetry._detect_gpu() is True


def test_detect_gpu_uses_windows_video_controller(monkeypatch) -> None:
    def fake_run(command, **kwargs):
        del kwargs
        if command == ["nvidia-smi"]:
            raise FileNotFoundError
        if command == ["wmic", "path", "win32_VideoController", "get", "name"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="Name\nNVIDIA GeForce RTX 4090\n",
            )
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(telemetry.platform, "system", lambda: "Windows")
    monkeypatch.setattr(telemetry.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(telemetry.subprocess, "run", fake_run)

    assert telemetry._detect_gpu() is True
