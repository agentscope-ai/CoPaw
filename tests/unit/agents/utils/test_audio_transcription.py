# -*- coding: utf-8 -*-
# pylint: disable=protected-access
import sys
from types import SimpleNamespace

import pytest

from qwenpaw.agents.utils import audio_transcription


@pytest.fixture(autouse=True)
def reset_local_whisper_cache(monkeypatch):
    monkeypatch.setattr(audio_transcription, "_local_whisper_model", None)
    monkeypatch.setattr(audio_transcription, "_local_whisper_model_key", None)
    monkeypatch.delenv("QWENPAW_LOCAL_WHISPER_MODEL", raising=False)
    monkeypatch.delenv("QWENPAW_LOCAL_WHISPER_DOWNLOAD_ROOT", raising=False)


def test_local_whisper_loads_default_model(monkeypatch):
    calls = []
    fake_model = object()

    monkeypatch.setitem(
        sys.modules,
        "whisper",
        SimpleNamespace(
            load_model=lambda model, **kwargs: calls.append(
                (model, kwargs),
            )
            or fake_model,
        ),
    )

    assert audio_transcription._get_local_whisper_model() is fake_model
    assert audio_transcription._get_local_whisper_model() is fake_model
    assert calls == [("base", {})]


def test_local_whisper_loads_configured_model_and_cache(monkeypatch):
    calls = []
    fake_model = object()

    monkeypatch.setenv(
        "QWENPAW_LOCAL_WHISPER_MODEL",
        " C:/models/whisper/base.pt ",
    )
    monkeypatch.setenv(
        "QWENPAW_LOCAL_WHISPER_DOWNLOAD_ROOT",
        " C:/models/whisper-cache ",
    )
    monkeypatch.setitem(
        sys.modules,
        "whisper",
        SimpleNamespace(
            load_model=lambda model, **kwargs: calls.append(
                (model, kwargs),
            )
            or fake_model,
        ),
    )

    assert audio_transcription._get_local_whisper_model() is fake_model
    assert calls == [
        (
            "C:/models/whisper/base.pt",
            {"download_root": "C:/models/whisper-cache"},
        ),
    ]


def test_local_whisper_cache_respects_env_changes(monkeypatch):
    calls = []

    def fake_load_model(model, **kwargs):
        loaded = {"model": model, "kwargs": kwargs}
        calls.append(loaded)
        return loaded

    monkeypatch.setitem(
        sys.modules,
        "whisper",
        SimpleNamespace(load_model=fake_load_model),
    )

    first = audio_transcription._get_local_whisper_model()
    monkeypatch.setenv("QWENPAW_LOCAL_WHISPER_MODEL", "small")
    second = audio_transcription._get_local_whisper_model()

    assert first is not second
    assert calls == [
        {"model": "base", "kwargs": {}},
        {"model": "small", "kwargs": {}},
    ]


def test_local_whisper_status_reports_model_settings(monkeypatch, tmp_path):
    cache_dir = tmp_path / "whisper-cache"
    cache_dir.mkdir()
    model_path = cache_dir / "small.pt"
    model_path.write_bytes(b"cached model")

    monkeypatch.setenv("QWENPAW_LOCAL_WHISPER_MODEL", "small")
    monkeypatch.setenv(
        "QWENPAW_LOCAL_WHISPER_DOWNLOAD_ROOT",
        str(cache_dir),
    )
    monkeypatch.setattr(
        audio_transcription.shutil,
        "which",
        lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None,
    )
    monkeypatch.setitem(
        sys.modules,
        "whisper",
        SimpleNamespace(
            _MODELS={"small": "https://example.invalid/models/small.pt"},
            load_model=lambda *args, **kwargs: object(),
        ),
    )

    assert audio_transcription.check_local_whisper_available() == {
        "available": True,
        "offline_available": True,
        "ffmpeg_installed": True,
        "whisper_installed": True,
        "model_available": True,
        "model": "small",
        "model_path": str(model_path),
        "download_root": str(cache_dir),
        "message": "Local Whisper is ready for offline use.",
    }


def test_local_whisper_status_reports_missing_cached_model(
    monkeypatch,
    tmp_path,
):
    cache_dir = tmp_path / "whisper-cache"
    cache_dir.mkdir()

    monkeypatch.setenv(
        "QWENPAW_LOCAL_WHISPER_DOWNLOAD_ROOT",
        str(cache_dir),
    )
    monkeypatch.setattr(
        audio_transcription.shutil,
        "which",
        lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None,
    )
    monkeypatch.setitem(
        sys.modules,
        "whisper",
        SimpleNamespace(
            _MODELS={"base": "https://example.invalid/models/base.pt"},
            load_model=lambda *args, **kwargs: object(),
        ),
    )

    status = audio_transcription.check_local_whisper_available()

    assert status["available"] is True
    assert status["offline_available"] is False
    assert status["ffmpeg_installed"] is True
    assert status["whisper_installed"] is True
    assert status["model_available"] is False
    assert status["model"] == "base"
    assert status["model_path"] == str(cache_dir / "base.pt")
    assert "Whisper model 'base'" in status["message"]


async def test_local_whisper_transcription_raises_when_model_missing(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv(
        "QWENPAW_LOCAL_WHISPER_DOWNLOAD_ROOT",
        str(tmp_path),
    )
    monkeypatch.setattr(
        audio_transcription.shutil,
        "which",
        lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None,
    )
    monkeypatch.setitem(
        sys.modules,
        "whisper",
        SimpleNamespace(
            _MODELS={"base": "https://example.invalid/models/base.pt"},
            load_model=lambda *args, **kwargs: (_ for _ in ()).throw(
                RuntimeError("network unreachable"),
            ),
        ),
    )

    with pytest.raises(audio_transcription.AudioTranscriptionError) as exc:
        await audio_transcription._transcribe_local_whisper(
            str(tmp_path / "audio.wav"),
        )

    assert exc.value.code == "LOCAL_WHISPER_MODEL_UNAVAILABLE"
    assert "For offline use" in exc.value.message
