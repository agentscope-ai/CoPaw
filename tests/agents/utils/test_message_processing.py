# -*- coding: utf-8 -*-
import base64

from copaw.agents.utils.message_processing import (
    _update_block_with_local_path,
)


def test_update_image_block_uses_base64_source(tmp_path):
    image_path = tmp_path / "sample.png"
    image_bytes = b"\x89PNG\r\n\x1a\nfake_png_content"
    image_path.write_bytes(image_bytes)

    block = {"type": "image", "source": {"type": "url", "url": "mock://old"}}
    updated = _update_block_with_local_path(block, "image", str(image_path))

    source = updated["source"]
    assert source["type"] == "base64"
    assert source["media_type"] == "image/png"
    assert base64.b64decode(source["data"]) == image_bytes


def test_update_audio_block_keeps_url_source_with_media_type(tmp_path):
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"RIFFxxxxWAVE")

    block = {"type": "audio", "source": {"type": "url", "url": "mock://old"}}
    updated = _update_block_with_local_path(block, "audio", str(audio_path))

    source = updated["source"]
    assert source["type"] == "url"
    assert source["url"].startswith("file://")
    assert source["media_type"] == "audio/wav"
