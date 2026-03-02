# -*- coding: utf-8 -*-

from collections.abc import AsyncIterator
from typing import Any

import pytest

from copaw.app.channels.feishu.channel import FeishuChannel


async def _dummy_process(_request: Any) -> AsyncIterator[Any]:
    if False:
        yield None


@pytest.mark.asyncio
async def test_get_receive_for_send_matches_suffix_against_receive_id() -> None:
    channel = FeishuChannel(
        process=_dummy_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="",
    )
    channel._receive_id_store["k1"] = ("open_id", "ou_abc123xyz9876")

    recv = await channel._get_receive_for_send(
        "feishu:sw:nickname#9876",
        meta={},
    )

    assert recv == ("open_id", "ou_abc123xyz9876")


@pytest.mark.asyncio
async def test_get_receive_for_send_fallbacks_to_meta_user_open_id() -> None:
    channel = FeishuChannel(
        process=_dummy_process,
        enabled=True,
        app_id="app_id",
        app_secret="app_secret",
        bot_prefix="",
    )

    recv = await channel._get_receive_for_send(
        "feishu:sw:missing_session_key",
        meta={"user_id": "ou_meta_open_id"},
    )

    assert recv == ("open_id", "ou_meta_open_id")
