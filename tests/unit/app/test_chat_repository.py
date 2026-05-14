# -*- coding: utf-8 -*-
"""Tests for JSON chat repository recovery."""
from __future__ import annotations

import json

import pytest

from qwenpaw.app.runner.models import ChatSpec, ChatsFile
from qwenpaw.app.runner.repo.json_repo import JsonChatRepository


@pytest.mark.asyncio
async def test_load_repairs_invalid_chats_json_with_backup(tmp_path):
    chats_path = tmp_path / "chats.json"
    invalid_text = '{"version": 1, "chats": [{"id": "broken"},]}'
    chats_path.write_text(invalid_text, encoding="utf-8")

    repo = JsonChatRepository(chats_path)

    loaded = await repo.load()

    assert loaded == ChatsFile(version=1, chats=[])
    assert json.loads(chats_path.read_text(encoding="utf-8")) == {
        "version": 1,
        "chats": [],
    }
    backups = list(tmp_path.glob("chats.json.*.invalid.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == invalid_text


@pytest.mark.asyncio
async def test_save_writes_valid_chats_json(tmp_path):
    chats_path = tmp_path / "chats.json"
    repo = JsonChatRepository(chats_path)
    chats_file = ChatsFile(
        version=1,
        chats=[
            ChatSpec(
                id="chat-1",
                name="Chat",
                session_id="console:default",
                user_id="default",
                channel="console",
            ),
        ],
    )

    await repo.save(chats_file)

    loaded = json.loads(chats_path.read_text(encoding="utf-8"))
    assert loaded["version"] == 1
    assert loaded["chats"][0]["id"] == "chat-1"
