# -*- coding: utf-8 -*-
"""Tests for file I/O tools."""

import pytest

from qwenpaw.agents.tools.file_io import read_file


def _response_text(response) -> str:
    return response.content[0].get("text", "")


@pytest.mark.asyncio
async def test_read_file_rejects_image_extension(tmp_path):
    image_path = tmp_path / "photo.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")

    response = await read_file(str(image_path))

    text = _response_text(response)
    assert "is an image file" in text
    assert "will not decode image bytes as text" in text


@pytest.mark.asyncio
async def test_read_file_rejects_image_magic_without_extension(tmp_path):
    image_path = tmp_path / "upload"
    image_path.write_bytes(b"\xff\xd8\xff\xe0binary image bytes")

    response = await read_file(str(image_path))

    assert "is an image file" in _response_text(response)


@pytest.mark.asyncio
async def test_read_file_still_reads_text_files(tmp_path):
    text_path = tmp_path / "notes.txt"
    text_path.write_text("hello\nworld", encoding="utf-8")

    response = await read_file(str(text_path))

    assert _response_text(response) == "hello\nworld"
