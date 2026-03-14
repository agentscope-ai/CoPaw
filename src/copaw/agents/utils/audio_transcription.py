# -*- coding: utf-8 -*-
"""Audio transcription utility.

Transcribes audio files to text using an OpenAI-compatible
``/v1/audio/transcriptions`` endpoint.  The endpoint accepts ``.ogg``
natively, so no format conversion is required for Discord voice messages.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def _find_transcription_provider() -> Optional[Tuple[str, str]]:
    """Find an OpenAI-compatible provider that can serve transcription.

    Returns ``(base_url, api_key)`` or ``None``.
    Checks the active provider first, then scans all providers.
    """
    try:
        from ...providers.provider_manager import ProviderManager
        from ...providers.openai_provider import OpenAIProvider
        from ...providers.ollama_provider import OllamaProvider
    except Exception:
        logger.debug("Could not import provider modules")
        return None

    try:
        manager = ProviderManager.get_instance()
    except Exception:
        logger.debug("ProviderManager not initialised yet")
        return None

    def _url_for_provider(provider) -> Optional[Tuple[str, str]]:
        if isinstance(provider, OpenAIProvider):
            return (provider.base_url, provider.api_key or "")
        if isinstance(provider, OllamaProvider):
            base = provider.base_url.rstrip("/")
            return (base + "/v1", provider.api_key or "ollama")
        return None

    # 1. Try active provider first.
    active = manager.get_active_model()
    if active:
        provider = manager.get_provider(active.provider_id)
        if provider:
            result = _url_for_provider(provider)
            if result:
                return result

    # 2. Scan all providers for any OpenAI-compatible one.
    all_providers = {
        **getattr(manager, "builtin_providers", {}),
        **getattr(manager, "custom_providers", {}),
    }
    for provider in all_providers.values():
        result = _url_for_provider(provider)
        if result:
            return result

    return None


async def transcribe_audio(file_path: str) -> Optional[str]:
    """Transcribe an audio file to text.

    Uses the OpenAI-compatible ``/v1/audio/transcriptions`` endpoint,
    which accepts ogg, mp3, wav, flac, m4a, and other common formats.

    Returns the transcribed text, or ``None`` on failure.
    """
    creds = _find_transcription_provider()
    if creds is None:
        logger.warning(
            "No OpenAI-compatible provider found for audio transcription. "
            "Audio block will be kept as-is.",
        )
        return None

    base_url, api_key = creds

    try:
        from openai import AsyncOpenAI
    except ImportError:
        logger.warning("openai package not installed; cannot transcribe audio")
        return None

    client = AsyncOpenAI(base_url=base_url, api_key=api_key, timeout=60)

    try:
        with open(file_path, "rb") as f:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
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
