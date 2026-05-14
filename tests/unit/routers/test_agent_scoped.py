# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
from __future__ import annotations

from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from qwenpaw.app.agent_context import (
    get_current_agent_id,
    get_current_root_session_id,
)
from qwenpaw.app.routers.agent_scoped import (
    AgentContextMiddleware,
    create_agent_scoped_router,
)


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AgentContextMiddleware)

    @app.get("/api/agents/{agent_id}/echo")
    async def echo_agent_context(request: Request) -> dict[str, str | None]:
        request_context = getattr(request.state, "request_context", {})
        return {
            "path_agent_id": getattr(request.state, "agent_id", None),
            "current_agent_id": get_current_agent_id(),
            "state_root_session_id": request_context.get("root_session_id"),
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
        "state_root_session_id": "root-session-1",
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
