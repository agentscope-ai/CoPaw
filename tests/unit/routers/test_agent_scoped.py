# -*- coding: utf-8 -*-
# pylint: disable=protected-access,redefined-outer-name
from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from qwenpaw.app import agent_context
from qwenpaw.app.agent_context import (
    get_current_agent_id,
    get_current_root_session_id,
)
from qwenpaw.app.routers.agent_scoped import (
    AgentContextMiddleware,
    create_agent_scoped_router,
)


@pytest.fixture(autouse=True)
def _reset_agent_context():
    agent_context._current_agent_id.set(None)
    agent_context._current_root_session_id.set(None)
    yield
    agent_context._current_agent_id.set(None)
    agent_context._current_root_session_id.set(None)


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AgentContextMiddleware)

    @app.get("/api/agents/{agent_id}/echo")
    async def echo_agent_context(
        request: Request,
        agent_id: str,
    ) -> dict[str, str | None]:
        del agent_id
        request_context = getattr(request.state, "request_context", {})
        return {
            "path_agent_id": getattr(request.state, "agent_id", None),
            "current_agent_id": get_current_agent_id(),
            "root_session_id": request_context.get("root_session_id"),
            "current_root_session_id": get_current_root_session_id(),
        }

    @app.get("/api/header-only")
    async def echo_header_context() -> dict[str, str]:
        return {"current_agent_id": get_current_agent_id()}

    return app


async def test_middleware_prefers_agent_id_from_api_path() -> None:
    app = build_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/agents/path-agent/echo",
            headers={
                "X-Agent-Id": "header-agent",
                "X-Root-Session-Id": "root-session-1",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "path_agent_id": "path-agent",
        "current_agent_id": "path-agent",
        "root_session_id": "root-session-1",
        "current_root_session_id": "root-session-1",
    }


async def test_middleware_uses_agent_id_header_without_agent_path() -> None:
    app = build_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/header-only",
            headers={"X-Agent-Id": "header-agent"},
        )

    assert response.status_code == 200
    assert response.json() == {"current_agent_id": "header-agent"}


def test_create_agent_scoped_router_mounts_expected_agent_routes() -> None:
    router = create_agent_scoped_router()
    paths = {getattr(route, "path", "") for route in router.routes}

    assert "/agents/{agentId}/agent-status" in paths
    assert "/agents/{agentId}/chats" in paths
    assert "/agents/{agentId}/workspace/files" in paths
    assert "/agents/{agentId}/tools" in paths
