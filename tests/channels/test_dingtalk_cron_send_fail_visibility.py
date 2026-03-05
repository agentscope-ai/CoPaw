# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from agentscope_runtime.engine.schemas.agent_schemas import (
    ContentType,
    TextContent,
)

from copaw.app.channels.dingtalk.channel import DingTalkChannel


async def _dummy_process(_request):
    if False:  # pragma: no cover
        yield None


def _build_channel() -> DingTalkChannel:
    return DingTalkChannel(
        process=_dummy_process,
        enabled=True,
        client_id="",
        client_secret="",
        bot_prefix="[BOT] ",
    )


@pytest.mark.asyncio
async def test_proactive_send_raises_when_no_session_webhook() -> None:
    ch = _build_channel()
    ch._get_session_webhook_for_send = AsyncMock(return_value=None)  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError, match="no sessionWebhook found"):
        await ch.send_content_parts(
            "dingtalk:sw:missing",
            [TextContent(type=ContentType.TEXT, text="hello")],
            {"session_id": "missing", "user_id": "u1"},
        )


@pytest.mark.asyncio
async def test_proactive_send_raises_when_webhook_api_fails() -> None:
    ch = _build_channel()
    ch._get_session_webhook_for_send = AsyncMock(  # type: ignore[attr-defined]
        return_value="https://oapi.dingtalk.com/robot/sendBySession?session=x",
    )
    ch._send_via_session_webhook = AsyncMock(return_value=False)  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError, match="text sendBySession failed"):
        await ch.send_content_parts(
            "dingtalk:sw:exists",
            [TextContent(type=ContentType.TEXT, text="hello")],
            {"session_id": "exists", "user_id": "u2"},
        )


@pytest.mark.asyncio
async def test_reply_context_without_webhook_does_not_raise() -> None:
    ch = _build_channel()
    ch._get_session_webhook_for_send = AsyncMock(return_value=None)  # type: ignore[attr-defined]

    loop = asyncio.get_running_loop()
    future: asyncio.Future[str] = loop.create_future()
    await ch.send_content_parts(
        "dingtalk:sw:reply",
        [TextContent(type=ContentType.TEXT, text="hello")],
        {"reply_loop": loop, "reply_future": future},
    )
    await asyncio.sleep(0)

    assert future.done()
    assert future.result() == "hello"
