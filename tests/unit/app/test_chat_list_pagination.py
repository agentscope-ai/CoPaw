# -*- coding: utf-8 -*-
"""Regression tests for chat list pagination."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from qwenpaw.app.runner.api import get_chat_manager, get_workspace, router
from qwenpaw.app.runner.manager import ChatManager
from qwenpaw.app.runner.models import ChatSpec
from qwenpaw.app.runner.repo.json_repo import JsonChatRepository


class FakeTaskTracker:
    """Minimal task tracker dependency for chat API tests."""

    async def get_status(self, _chat_id: str) -> str:
        return "idle"


class FakeWorkspace:
    """Minimal workspace dependency for chat API tests."""

    task_tracker = FakeTaskTracker()


async def _client_with_chats(tmp_path: Path) -> AsyncClient:
    chat_manager = ChatManager(
        repo=JsonChatRepository(tmp_path / "chats.json"),
    )
    for idx in range(5):
        await chat_manager.create_chat(
            ChatSpec(
                id=f"chat-{idx}",
                name=f"Chat {idx}",
                session_id=f"console:user-{idx}",
                user_id=f"user-{idx}",
                channel="console",
            ),
        )

    app = FastAPI()
    app.include_router(router, prefix="/api")

    def get_test_chat_manager() -> ChatManager:
        return chat_manager

    def get_test_workspace() -> FakeWorkspace:
        return FakeWorkspace()

    app.dependency_overrides[get_chat_manager] = get_test_chat_manager
    app.dependency_overrides[get_workspace] = get_test_workspace
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_list_chats_supports_offset_and_limit(tmp_path: Path) -> None:
    """GET /chats should return a requested chat window."""
    client = await _client_with_chats(tmp_path)

    async with client:
        response = await client.get(
            "/api/chats",
            params={"offset": 1, "limit": 2},
        )

    assert response.status_code == 200
    assert [chat["id"] for chat in response.json()] == ["chat-1", "chat-2"]


async def test_list_chats_without_pagination_returns_full_list(
    tmp_path: Path,
) -> None:
    """The default chat list response should remain backwards compatible."""
    client = await _client_with_chats(tmp_path)

    async with client:
        response = await client.get("/api/chats")

    assert response.status_code == 200
    assert len(response.json()) == 5
