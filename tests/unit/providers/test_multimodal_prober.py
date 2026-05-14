# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import base64
import time

import pytest

from qwenpaw.providers import multimodal_prober


@pytest.mark.parametrize(
    ("supports_image", "supports_video", "expected"),
    [
        (False, False, False),
        (True, False, True),
        (False, True, True),
        (True, True, True),
    ],
)
def test_probe_result_supports_multimodal_reflects_media_flags(
    supports_image: bool,
    supports_video: bool,
    expected: bool,
) -> None:
    result = multimodal_prober.ProbeResult(
        supports_image=supports_image,
        supports_video=supports_video,
    )

    assert result.supports_multimodal is expected


@pytest.mark.parametrize(
    "message",
    [
        "image input is not supported",
        "VIDEO_URL field is invalid",
        "vision models only",
        "multimodal request failed",
        "this model does not support media",
    ],
)
def test_is_media_keyword_error_detects_media_failures(message: str) -> None:
    assert multimodal_prober._is_media_keyword_error(RuntimeError(message))


def test_is_media_keyword_error_ignores_unrelated_errors() -> None:
    assert (
        multimodal_prober._is_media_keyword_error(
            RuntimeError("rate limit exceeded"),
        )
        is False
    )


def test_probe_payload_constants_are_valid_base64() -> None:
    image = base64.b64decode(multimodal_prober._PROBE_IMAGE_B64)
    video = base64.b64decode(multimodal_prober._PROBE_VIDEO_B64)

    assert image.startswith(b"\x89PNG\r\n\x1a\n")
    assert b"ftyp" in video[:16]
    assert multimodal_prober._PROBE_VIDEO_URL.startswith("https://")


def test_evaluate_image_probe_answer_accepts_red_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(time, "monotonic", lambda: 12.5)

    supported, message = multimodal_prober.evaluate_image_probe_answer(
        "  Crimson  ",
        model_id="vision-model",
        start_time=10.0,
    )

    assert supported is True
    assert message == "Image supported (answer='crimson')"


def test_evaluate_image_probe_answer_accepts_red_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(time, "monotonic", lambda: 20.0)

    supported, message = multimodal_prober.evaluate_image_probe_answer(
        "unknown",
        model_id="reasoning-model",
        start_time=15.0,
        reasoning="The image appears red.",
    )

    assert supported is True
    assert message == "Image supported (reasoning, answer='unknown')"


def test_evaluate_image_probe_answer_rejects_non_red_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(time, "monotonic", lambda: 30.0)

    supported, message = multimodal_prober.evaluate_image_probe_answer(
        "blue",
        model_id="text-model",
        start_time=25.0,
    )

    assert supported is False
    assert message == "Model did not recognise image (answer='blue')"
