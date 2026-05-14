# -*- coding: utf-8 -*-
"""Regression tests for chat history pagination."""
from __future__ import annotations

from pathlib import Path

from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from qwenpaw.app.runner.api import (
    get_chat_manager,
    get_session,
    get_workspace,
    router,
)
from qwenpaw.app.runner.manager import ChatManager
from qwenpaw.app.runner.models import ChatSpec
from qwenpaw.app.runner.repo.json_repo import JsonChatRepository
from qwenpaw.app.runner.session import SafeJSONSession


class FakeTaskTracker:
    """Minimal task tracker dependency for chat API tests."""

    async def get_status(self, _chat_id: str) -> str:
        return "idle"


class FakeWorkspace:
    """Minimal workspace dependency for chat API tests."""

    task_tracker = FakeTaskTracker()


class FakeAgentState:
    """Minimal session module carrying an agent memory state."""

    def __init__(self, memory_state: dict):
        self._memory_state = memory_state

    def state_dict(self) -> dict:
        return {"memory": self._memory_state}


async def _client_with_chat(tmp_path: Path) -> tuple[AsyncClient, str]:
    chat_manager = ChatManager(
        repo=JsonChatRepository(tmp_path / "chats.json"),
    )
    session = SafeJSONSession(save_dir=str(tmp_path / "sessions"))
    chat = await chat_manager.create_chat(
        ChatSpec(
            id="chat-1",
            name="Long Chat",
            session_id="console:alice",
            user_id="alice",
            channel="console",
        ),
    )

    memory = InMemoryMemory()
    for idx in range(5):
        await memory.add(
            Msg(
                name="user",
                role="user",
                content=f"message-{idx}",
            ),
        )
    await session.save_session_state(
        chat.session_id,
        user_id=chat.user_id,
        channel=chat.channel,
        agent=FakeAgentState(memory.state_dict()),
    )

    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_chat_manager] = lambda: chat_manager
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_workspace] = lambda: FakeWorkspace()
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    return client, chat.id


async def test_get_chat_supports_offset_and_limit(tmp_path: Path) -> None:
    """GET /chats/{id} should return a requested message window."""
    client, chat_id = await _client_with_chat(tmp_path)

    async with client:
        response = await client.get(
            f"/api/chats/{chat_id}",
            params={"offset": 1, "limit": 2},
        )

    assert response.status_code == 200
    body = response.json()
    assert [msg["content"][0]["text"] for msg in body["messages"]] == [
        "message-1",
        "message-2",
    ]


async def test_get_chat_without_pagination_returns_full_history(
    tmp_path: Path,
) -> None:
    """The default response should remain backwards compatible."""
    client, chat_id = await _client_with_chat(tmp_path)

    async with client:
        response = await client.get(f"/api/chats/{chat_id}")

    assert response.status_code == 200
    assert len(response.json()["messages"]) == 5
