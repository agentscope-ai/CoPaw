# -*- coding: utf-8 -*-
from pathlib import Path

from agentscope.message import Msg

from copaw.agents.utils.message_processing import (
    process_file_and_media_blocks_in_message,
)


async def test_process_image_block_does_not_append_local_path_text(
    monkeypatch,
    tmp_path,
) -> None:
    image_path = tmp_path / "example.jpg"
    image_path.write_bytes(b"fake-image")

    async def _fake_download_file_from_url(url: str, filename: str) -> str:
        del url, filename
        return str(image_path)

    monkeypatch.setattr(
        "copaw.agents.utils.message_processing.download_file_from_url",
        _fake_download_file_from_url,
    )
    monkeypatch.setattr(
        "copaw.agents.utils.message_processing._is_allowed_media_path",
        lambda path: Path(path) == image_path,
    )

    message = Msg(
        name="user",
        role="user",
        content=[
            {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": image_path.as_uri(),
                },
            },
        ],
    )

    await process_file_and_media_blocks_in_message(message)

    assert message.content == [
        {
            "type": "image",
            "source": {
                "type": "url",
                "url": image_path.as_uri(),
            },
        },
    ]


async def test_process_file_block_still_appends_local_path_text(
    monkeypatch,
    tmp_path,
) -> None:
    file_path = tmp_path / "example.txt"
    file_path.write_text("example", encoding="utf-8")

    async def _fake_download_file_from_url(url: str, filename: str) -> str:
        del url, filename
        return str(file_path)

    monkeypatch.setattr(
        "copaw.agents.utils.message_processing.download_file_from_url",
        _fake_download_file_from_url,
    )
    monkeypatch.setattr(
        "copaw.agents.utils.message_processing._is_allowed_media_path",
        lambda path: Path(path) == file_path,
    )

    message = Msg(
        name="user",
        role="user",
        content=[
            {
                "type": "file",
                "filename": "example.txt",
                "source": {
                    "type": "url",
                    "url": file_path.as_uri(),
                },
            },
        ],
    )

    await process_file_and_media_blocks_in_message(message)

    assert message.content == [
        {
            "type": "file",
            "filename": "example.txt",
            "source": str(file_path),
        },
        {
            "type": "text",
            "text": f"用户上传文件，已经下载到 {file_path}",
        },
    ]
