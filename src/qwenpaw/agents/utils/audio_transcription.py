# -*- coding: utf-8 -*-
"""Audio transcription utility.

Transcribes audio files to text using either:
- An OpenAI-compatible ``/v1/audio/transcriptions`` endpoint (Whisper API), or
- The locally installed ``openai-whisper`` Python library (Local Whisper).

Transcription is only attempted when explicitly enabled via the
``transcription_provider_type`` config setting.  The default is ``"disabled"``.
"""

import asyncio
import logging
import os
import shutil
import threading
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_LOCAL_WHISPER_MODEL_ENV = "QWENPAW_LOCAL_WHISPER_MODEL"
_LOCAL_WHISPER_DOWNLOAD_ROOT_ENV = "QWENPAW_LOCAL_WHISPER_DOWNLOAD_ROOT"
_DEFAULT_LOCAL_WHISPER_MODEL = "base"


class AudioTranscriptionError(RuntimeError):
    """Raised when transcription cannot run and the caller needs details."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ------------------------------------------------------------------
# Cached local-whisper model (lazy singleton)
# ------------------------------------------------------------------
_local_whisper_model = None
_local_whisper_model_key: Tuple[str, Optional[str]] | None = None
_local_whisper_lock = threading.Lock()


def _local_whisper_model_settings() -> Tuple[str, Optional[str]]:
    """Return the configured local Whisper model and optional cache root."""
    model = (
        os.environ.get(_LOCAL_WHISPER_MODEL_ENV, "").strip()
        or _DEFAULT_LOCAL_WHISPER_MODEL
    )
    download_root = (
        os.environ.get(_LOCAL_WHISPER_DOWNLOAD_ROOT_ENV, "").strip() or None
    )
    return model, download_root


def _default_whisper_download_root() -> Path:
    """Return openai-whisper's default model cache directory."""
    return Path(os.path.expanduser("~")) / ".cache" / "whisper"


def _whisper_model_cache_path(
    whisper_module,
    model_name: str,
    download_root: Optional[str],
) -> Optional[Path]:
    """Return the expected local checkpoint path for a named Whisper model."""
    if Path(model_name).is_file():
        return Path(model_name)

    model_urls = getattr(whisper_module, "_MODELS", {})
    url = model_urls.get(model_name) if isinstance(model_urls, dict) else None
    if not url:
        return None

    filename = Path(urlparse(url).path).name or f"{model_name}.pt"
    root = (
        Path(download_root)
        if download_root
        else _default_whisper_download_root()
    )
    return root / filename


def _local_whisper_model_status(whisper_module) -> tuple[bool, Optional[str]]:
    """Return whether the configured local Whisper model is already cached."""
    model_name, download_root = _local_whisper_model_settings()
    path = _whisper_model_cache_path(whisper_module, model_name, download_root)
    if path is None:
        return False, None
    return path.is_file(), str(path)


def _local_whisper_unavailable_message(status: dict) -> str:
    """Build a user-actionable local Whisper availability message."""
    if (
        status.get("ffmpeg_installed")
        and status.get("whisper_installed")
        and not status.get("model_available")
    ):
        model = status.get("model") or _DEFAULT_LOCAL_WHISPER_MODEL
        path = status.get("model_path") or "the Whisper cache directory"
        return (
            "Local Whisper dependencies are installed, but Whisper model "
            f"'{model}' is not cached at {path}. "
            "For offline use, pre-download the model on an online machine or "
            f"set {_LOCAL_WHISPER_MODEL_ENV} to an existing model file and "
            f"{_LOCAL_WHISPER_DOWNLOAD_ROOT_ENV} to an existing cache "
            "directory."
        )

    missing = []
    if not status["ffmpeg_installed"]:
        missing.append("ffmpeg")
    if not status["whisper_installed"]:
        missing.append("openai-whisper")

    if not missing:
        return "Local Whisper is unavailable."

    return (
        "Local Whisper is unavailable. Missing: "
        f"{', '.join(missing)}. "
        "Install the missing dependencies to use local transcription."
    )


def _get_local_whisper_model():
    """Return a cached whisper model, loading it on first call."""
    global _local_whisper_model, _local_whisper_model_key  # noqa: PLW0603
    model_name, download_root = _local_whisper_model_settings()
    model_key = (model_name, download_root)

    if (
        _local_whisper_model is not None
        and _local_whisper_model_key == model_key
    ):
        return _local_whisper_model
    with _local_whisper_lock:
        if (
            _local_whisper_model is not None
            and _local_whisper_model_key == model_key
        ):
            return _local_whisper_model
        import whisper

        kwargs = {}
        if download_root:
            kwargs["download_root"] = download_root

        logger.info(
            "Loading local Whisper model '%s'%s",
            model_name,
            (f" from cache root '{download_root}'" if download_root else ""),
        )
        _local_whisper_model = whisper.load_model(model_name, **kwargs)
        _local_whisper_model_key = model_key
        return _local_whisper_model


# ------------------------------------------------------------------
# Provider helpers
# ------------------------------------------------------------------


def _url_for_provider(provider) -> Optional[Tuple[str, str]]:
    """Return ``(base_url, api_key)`` if *provider* can serve transcription.

    Supports providers that do not require an API key (e.g. local Ollama).
    """
    from ...providers.openai_provider import OpenAIProvider
    from ...providers.ollama_provider import OllamaProvider

    if isinstance(provider, OpenAIProvider):
        requires_key = getattr(provider, "require_api_key", True)
        key = provider.api_key or ""
        if requires_key and not key:
            return None
        base = provider.base_url.rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        return (base, key or "")
    if isinstance(provider, OllamaProvider):
        base = provider.base_url.rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        return (base, provider.api_key or "")
    return None


def _get_manager():
    """Return ProviderManager singleton or None."""
    try:
        from ...providers.provider_manager import ProviderManager

        return ProviderManager.get_instance()
    except Exception:
        logger.debug("ProviderManager not initialised yet")
        return None


# ------------------------------------------------------------------
# Public helpers for API / Console UI
# ------------------------------------------------------------------


def list_transcription_providers() -> List[dict]:
    """Return providers capable of audio transcription.

    Each entry is ``{"id": ..., "name": ..., "available": bool}``.
    Availability is based on whether the provider has usable credentials.
    """
    manager = _get_manager()
    if manager is None:
        return []

    results: list[dict] = []
    all_providers = {
        **getattr(manager, "builtin_providers", {}),
        **getattr(manager, "custom_providers", {}),
    }
    for provider in all_providers.values():
        creds = _url_for_provider(provider)
        if creds is not None:
            results.append(
                {
                    "id": provider.id,
                    "name": provider.name,
                    "available": True,
                },
            )
    return results


def get_configured_transcription_provider_id() -> str:
    """Return the explicitly configured provider ID (raw config value)."""
    from ...config import load_config

    return load_config().agents.transcription_provider_id


def check_local_whisper_available() -> dict:
    """Check whether the local whisper provider can be used.

    Returns a dict with::

        {
            "available": bool,
            "ffmpeg_installed": bool,
            "whisper_installed": bool,
            "offline_available": bool,
            "model_available": bool,
        }
    """
    ffmpeg_ok = shutil.which("ffmpeg") is not None

    whisper_ok = False
    whisper_module = None
    try:
        import whisper as _whisper

        whisper_ok = True
        whisper_module = _whisper
    except ImportError:
        pass

    model_name, download_root = _local_whisper_model_settings()
    model_available = False
    model_path = None
    if whisper_module is not None:
        model_available, model_path = _local_whisper_model_status(
            whisper_module,
        )

    status = {
        "available": ffmpeg_ok and whisper_ok,
        "offline_available": ffmpeg_ok and whisper_ok and model_available,
        "ffmpeg_installed": ffmpeg_ok,
        "whisper_installed": whisper_ok,
        "model_available": model_available,
        "model": model_name,
        "model_path": model_path,
        "download_root": (
            download_root or str(_default_whisper_download_root())
        ),
    }
    if status["offline_available"]:
        status["message"] = "Local Whisper is ready for offline use."
    else:
        status["message"] = _local_whisper_unavailable_message(status)

    return status


# ------------------------------------------------------------------
# Transcription backends
# ------------------------------------------------------------------


async def _transcribe_local_whisper(file_path: str) -> Optional[str]:
    """Transcribe using the locally installed ``openai-whisper`` library.

    Requires both ``ffmpeg`` and ``openai-whisper`` to be installed.
    Returns the transcribed text, or ``None`` on failure.
    """
    status = check_local_whisper_available()
    if not status["available"]:
        message = status["message"]
        logger.warning(message)
        raise AudioTranscriptionError(
            "LOCAL_WHISPER_UNAVAILABLE",
            message,
        )

    def _run():
        model = _get_local_whisper_model()
        result = model.transcribe(file_path)
        return (result.get("text") or "").strip()

    try:
        text = await asyncio.to_thread(_run)
        if text:
            logger.debug(
                "Local Whisper transcribed %s: %s",
                file_path,
                text[:80],
            )
            return text
        logger.warning(
            "Local Whisper returned empty text for %s",
            file_path,
        )
        return None
    except AudioTranscriptionError:
        raise
    except Exception as exc:
        status = check_local_whisper_available()
        if status["available"] and not status.get("model_available"):
            message = f"{status['message']} Original error: {exc}"
            logger.warning(message, exc_info=True)
            raise AudioTranscriptionError(
                "LOCAL_WHISPER_MODEL_UNAVAILABLE",
                message,
            ) from exc

        message = f"Local Whisper transcription failed for {file_path}: {exc}"
        logger.warning(
            message,
            exc_info=True,
        )
        raise AudioTranscriptionError(
            "LOCAL_WHISPER_TRANSCRIPTION_FAILED",
            message,
        ) from exc


def _get_configured_provider_creds() -> Optional[Tuple[str, str]]:
    """Return ``(base_url, api_key)`` for the explicitly configured provider.

    Returns ``None`` when no provider is configured or the configured
    provider is not found / has no usable credentials.
    """
    from ...config import load_config

    configured_id = load_config().agents.transcription_provider_id
    if not configured_id:
        return None

    manager = _get_manager()
    if manager is None:
        return None

    provider = manager.get_provider(configured_id)
    if provider is None:
        logger.warning(
            "Configured transcription provider '%s' not found",
            configured_id,
        )
        return None

    creds = _url_for_provider(provider)
    if creds is None:
        logger.warning(
            "Configured transcription provider '%s' has no usable credentials",
            configured_id,
        )
    return creds


async def _transcribe_whisper_api(file_path: str) -> Optional[str]:
    """Transcribe using the OpenAI-compatible Whisper API endpoint.

    Only uses the explicitly configured provider — no auto-detection.
    Returns the transcribed text, or ``None`` on failure.
    """
    creds = _get_configured_provider_creds()
    if creds is None:
        logger.warning(
            "No transcription provider configured; skipping transcription",
        )
        return None

    base_url, api_key = creds

    try:
        from openai import AsyncOpenAI
    except ImportError:
        logger.warning(
            "openai package not installed; cannot transcribe audio",
        )
        return None

    from ...config import load_config

    model_name = load_config().agents.transcription_model or "whisper-1"

    client = AsyncOpenAI(
        base_url=base_url,
        api_key=api_key or "none",
        timeout=60,
    )

    try:
        with open(file_path, "rb") as f:
            transcript = await client.audio.transcriptions.create(
                model=model_name,
                file=f,
            )
        text = transcript.text.strip()
        if text:
            logger.debug("Transcribed audio %s: %s", file_path, text[:80])
            return text
        logger.warning("Transcription returned empty text for %s", file_path)
        return None
    except Exception:
        logger.warning(
            "Audio transcription failed for %s",
            file_path,
            exc_info=True,
        )
        return None


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------


async def transcribe_audio(
    file_path: str,
    *,
    raise_errors: bool = False,
) -> Optional[str]:
    """Transcribe an audio file to text.

    Dispatches to either the Whisper API or local Whisper based on the
    ``transcription_provider_type`` config setting.  When the setting is
    ``"disabled"`` (the default), returns ``None`` immediately.

    Returns the transcribed text, or ``None`` on failure.  When
    ``raise_errors`` is true, local Whisper setup/runtime failures are raised
    as :class:`AudioTranscriptionError` so API callers can surface actionable
    messages instead of a generic transcription failure.
    """
    from ...config import load_config

    provider_type = load_config().agents.transcription_provider_type

    if provider_type == "disabled":
        logger.debug("Transcription is disabled; skipping")
        return None
    if provider_type == "local_whisper":
        try:
            return await _transcribe_local_whisper(file_path)
        except AudioTranscriptionError:
            if raise_errors:
                raise
            return None
    if provider_type == "whisper_api":
        return await _transcribe_whisper_api(file_path)

    logger.warning("Unknown transcription_provider_type: %s", provider_type)
    return None
