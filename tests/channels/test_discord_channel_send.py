# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import types
from enum import Enum

import pytest


def _ensure_agentscope_runtime_stub() -> None:
    """Provide a tiny stub for local test envs missing agentscope_runtime."""
    try:
        __import__("agentscope_runtime.engine.schemas.agent_schemas")

        return
    except (ImportError, ModuleNotFoundError):
        pass

    agent_schemas = types.ModuleType(
        "agentscope_runtime.engine.schemas.agent_schemas",
    )

    class ContentType(str, Enum):
        TEXT = "text"
        IMAGE = "image"
        VIDEO = "video"
        AUDIO = "audio"
        FILE = "file"
        REFUSAL = "refusal"

    class MessageType(str, Enum):
        MESSAGE = "message"

    class RunStatus(str, Enum):
        COMPLETED = "completed"
        Completed = COMPLETED

    class _Base:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    for name in (
        "TextContent",
        "ImageContent",
        "VideoContent",
        "AudioContent",
        "FileContent",
        "RefusalContent",
    ):
        setattr(agent_schemas, name, _Base)
    setattr(agent_schemas, "ContentType", ContentType)
    setattr(agent_schemas, "MessageType", MessageType)
    setattr(agent_schemas, "RunStatus", RunStatus)

    sys.modules["agentscope_runtime"] = types.ModuleType("agentscope_runtime")
    sys.modules["agentscope_runtime.engine"] = types.ModuleType(
        "agentscope_runtime.engine",
    )
    sys.modules["agentscope_runtime.engine.schemas"] = types.ModuleType(
        "agentscope_runtime.engine.schemas",
    )
    sys.modules[
        "agentscope_runtime.engine.schemas.agent_schemas"
    ] = agent_schemas


_ensure_agentscope_runtime_stub()


async def _dummy_process(_):
    return None


class _DummyDM:
    def __init__(self, sink: list[str]):
        self._sink = sink

    async def send(self, text: str) -> None:
        self._sink.append(text)


class _DummyUser:
    def __init__(self, sink: list[str]):
        self.dm_channel = None
        self._sink = sink

    async def create_dm(self):
        self.dm_channel = _DummyDM(self._sink)
        return self.dm_channel


class _DummyTextChannel:
    def __init__(self, sink: list[str]):
        self._sink = sink

    async def send(self, text: str) -> None:
        self._sink.append(text)


class _DummyDiscordClient:
    def __init__(self):
        self.user_ids: list[int] = []
        self.channel_ids: list[int] = []
        self.dm_messages: list[str] = []
        self.channel_messages: list[str] = []

    def is_ready(self) -> bool:
        return True

    def get_user(self, user_id: int):
        self.user_ids.append(user_id)

    async def fetch_user(self, user_id: int):
        self.user_ids.append(user_id)
        return _DummyUser(self.dm_messages)

    def get_channel(self, channel_id: int):
        self.channel_ids.append(channel_id)

    async def fetch_channel(self, channel_id: int):
        self.channel_ids.append(channel_id)
        return _DummyTextChannel(self.channel_messages)


def _build_channel(client: _DummyDiscordClient):
    from copaw.app.channels.discord_.channel import DiscordChannel

    channel = DiscordChannel(
        process=_dummy_process,
        enabled=False,
        token="",
        http_proxy="",
        http_proxy_auth="",
        bot_prefix="[BOT] ",
    )
    channel.enabled = True
    setattr(channel, "_client", client)
    return channel


@pytest.mark.asyncio
async def test_send_accepts_prefixed_dm_user_id():
    client = _DummyDiscordClient()
    channel = _build_channel(client)
    to_handle = "discord:dm:1477691394096107665"

    await channel.send(
        to_handle,
        "hello",
        {
            "session_id": to_handle,
            "user_id": to_handle,
        },
    )

    assert client.user_ids == [1477691394096107665, 1477691394096107665]
    assert client.dm_messages == ["hello"]


@pytest.mark.asyncio
async def test_send_accepts_prefixed_channel_id():
    client = _DummyDiscordClient()
    channel = _build_channel(client)
    channel_handle = "discord:ch:123456789012345678"

    await channel.send(
        channel_handle,
        "channel hello",
        {
            "channel_id": channel_handle,
        },
    )

    assert client.channel_ids == [123456789012345678, 123456789012345678]
    assert client.channel_messages == ["channel hello"]
