# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from pathlib import Path
from types import SimpleNamespace

import pytest

from copaw.app.channels.base import ContentType
from copaw.app.channels.feishu.channel import FeishuChannel
from copaw.app.channels.feishu.constants import FEISHU_FILE_MAX_BYTES


async def _empty_process(_request):
    return None


def _build_text_event(message_id: str, sender_type: str) -> SimpleNamespace:
    return SimpleNamespace(
        event=SimpleNamespace(
            message=SimpleNamespace(
                message_id=message_id,
                chat_id="oc_test_chat",
                chat_type="group",
                message_type="text",
                content='{"text":"hello"}',
            ),
            sender=SimpleNamespace(
                sender_type=sender_type,
                sender_id=SimpleNamespace(open_id="ou_test_sender"),
                name="tester",
            ),
        ),
    )


@pytest.mark.asyncio
async def test_on_message_skip_app_sender() -> None:
    channel = FeishuChannel(
        process=_empty_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="[BOT] ",
    )
    enqueued: list[dict] = []
    channel._enqueue = enqueued.append

    await channel._on_message(_build_text_event("m-app", "app"))

    assert not enqueued


@pytest.mark.asyncio
async def test_send_content_parts_stop_after_file_failure() -> None:
    channel = FeishuChannel(
        process=_empty_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="[BOT] ",
    )

    send_file_calls: list[tuple[str, str]] = []
    send_text_calls: list[str] = []

    async def fake_send_file(receive_id_type, receive_id, part):
        send_file_calls.append((receive_id_type, receive_id))
        del part
        return (False, "file_too_large")

    async def fake_send_text(receive_id_type, receive_id, body):
        send_text_calls.append(body)
        del receive_id_type
        del receive_id
        return True

    channel._send_file = fake_send_file  # type: ignore[method-assign]
    channel._send_text = fake_send_text  # type: ignore[method-assign]

    parts = [
        SimpleNamespace(
            type=ContentType.FILE,
            file_url="file:///tmp/a.bin",
            filename="a.bin",
        ),
        SimpleNamespace(
            type=ContentType.FILE,
            file_url="file:///tmp/b.bin",
            filename="b.bin",
        ),
    ]
    await channel.send_content_parts(
        "feishu:sw:demo",
        parts,
        {"feishu_receive_id_type": "chat_id", "feishu_receive_id": "oc_demo"},
    )

    assert len(send_file_calls) == 1
    assert len(send_text_calls) == 1
    expected_limit_mb = FEISHU_FILE_MAX_BYTES // (1024 * 1024)
    assert f"{expected_limit_mb}MB" in send_text_calls[0]


@pytest.mark.asyncio
async def test_part_to_file_path_or_url_base64_decode_failed() -> None:
    channel = FeishuChannel(
        process=_empty_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="[BOT] ",
    )
    part = SimpleNamespace(
        type=ContentType.FILE,
        data="data:application/octet-stream;base64,not-base64-@@@",
        filename="broken.bin",
    )

    path_or_url, reason = await channel._part_to_file_path_or_url(part)

    assert path_or_url is None
    assert reason == "file_decode_failed"


@pytest.mark.asyncio
async def test_part_to_file_path_or_url_write_failed(monkeypatch) -> None:
    channel = FeishuChannel(
        process=_empty_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="[BOT] ",
    )
    part = SimpleNamespace(
        type=ContentType.FILE,
        data="data:application/octet-stream;base64,YQ==",
        filename="ok.bin",
    )

    def _raise_oserror(*args, **kwargs):
        del args
        del kwargs
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_bytes", _raise_oserror)

    path_or_url, reason = await channel._part_to_file_path_or_url(part)

    assert path_or_url is None
    assert reason == "file_write_failed"


@pytest.mark.asyncio
async def test_part_to_file_path_or_url_block_disallowed_local_file(
    tmp_path,
) -> None:
    channel = FeishuChannel(
        process=_empty_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="[BOT] ",
    )
    p = tmp_path / "secret.bin"
    p.write_bytes(b"secret")
    part = SimpleNamespace(
        type=ContentType.FILE,
        file_url=p.as_uri(),
        filename="secret.bin",
    )

    path_or_url, reason = await channel._part_to_file_path_or_url(part)

    assert path_or_url is None
    assert reason == "file_not_allowed"


@pytest.mark.asyncio
async def test_part_to_file_path_or_url_allow_env_dir(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("FEISHU_ALLOWED_FILE_DIRS", str(tmp_path))
    channel = FeishuChannel(
        process=_empty_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="[BOT] ",
    )
    p = tmp_path / "allowed.bin"
    p.write_bytes(b"ok")
    part = SimpleNamespace(
        type=ContentType.FILE,
        file_url=p.as_uri(),
        filename="allowed.bin",
    )

    path_or_url, reason = await channel._part_to_file_path_or_url(part)

    assert path_or_url == str(p)
    assert reason == ""


@pytest.mark.asyncio
async def test_fetch_bytes_from_url_block_loopback() -> None:
    channel = FeishuChannel(
        process=_empty_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="[BOT] ",
    )

    data = await channel._fetch_bytes_from_url("http://127.0.0.1/internal")

    assert data is None
