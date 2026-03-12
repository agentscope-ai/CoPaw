# -*- coding: utf-8 -*-
"""Agent-scoped router that wraps existing routers under /agents/{agentId}/

This provides agent isolation by injecting agentId into request.state,
allowing downstream APIs to access the correct agent context.
"""
from fastapi import APIRouter, Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response


class AgentContextMiddleware(BaseHTTPMiddleware):
    """Middleware to inject agentId into request.state."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Extract agentId from path and inject into request.state."""
        import logging

        logger = logging.getLogger(__name__)

        # Extract agentId from path: /agents/{agentId}/...
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 3 and path_parts[1] == "api":
            if len(path_parts) >= 4 and path_parts[2] == "agents":
                agent_id = path_parts[3]
                request.state.agent_id = agent_id
                logger.info(
                    f"AgentContextMiddleware: set agent_id={agent_id} "
                    f"for path={request.url.path}",
                )

        response = await call_next(request)
        return response


def create_agent_scoped_router() -> APIRouter:
    """Create router that wraps all existing routers under /{agentId}/

    Returns:
        APIRouter with all sub-routers mounted under /{agentId}/
    """
    from .agent import router as agent_router
    from .skills import router as skills_router
    from .tools import router as tools_router
    from .config import router as config_router
    from .mcp import router as mcp_router
    from .workspace import router as workspace_router
    from ..crons.api import router as cron_router
    from ..runner.api import router as chats_router

    # Create parent router with agentId parameter
    router = APIRouter(prefix="/agents/{agentId}", tags=["agent-scoped"])

    # Include all agent-specific sub-routers (they keep their own prefixes)
    # /agents/{agentId}/agent/* -> agent_router
    # /agents/{agentId}/chats/* -> chats_router
    # /agents/{agentId}/config/* -> config_router (channels, heartbeat)
    # /agents/{agentId}/cron/* -> cron_router
    # /agents/{agentId}/mcp/* -> mcp_router
    # /agents/{agentId}/skills/* -> skills_router
    # /agents/{agentId}/tools/* -> tools_router
    # /agents/{agentId}/workspace/* -> workspace_router
    router.include_router(agent_router)
    router.include_router(chats_router)
    router.include_router(config_router)
    router.include_router(cron_router)
    router.include_router(mcp_router)
    router.include_router(skills_router)
    router.include_router(tools_router)
    router.include_router(workspace_router)

    return router
