# -*- coding: utf-8 -*-
"""Agent status API."""

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...config import load_config
from ..agent_context import get_agent_for_request

router = APIRouter(prefix="/agent-status", tags=["agent-status"])


class AgentStatus(BaseModel):
    """Agent runtime status."""

    status: Literal["idle", "running", "disabled"] = Field(
        ...,
        description=(
            "Agent status: "
            "'disabled' = agent is disabled in config, "
            "'idle' = agent enabled but no running tasks, "
            "'running' = agent enabled and has active tasks"
        ),
    )
    running_task_count: int = Field(
        ...,
        ge=0,
        description="Number of currently running tasks",
    )
    last_run_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the last task started (UTC)",
    )
    last_finish_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the last task finished (UTC)",
    )


@router.get(
    "",
    response_model=AgentStatus,
    summary="Get agent status",
    description="Get the current runtime status of the agent",
)
async def get_agent_status(
    request: Request,
) -> AgentStatus:
    """Get agent runtime status including task count and timestamps.

    Returns:
        AgentStatus with current status, running tasks, and timestamps

    Raises:
        HTTPException: If agent not found (404)
    """
    # Extract agent_id from request path
    agent_id = request.path_params.get("agentId")
    if not agent_id:
        config = load_config()
        agent_id = config.agents.active_agent or "default"

    # Load config to check enabled status
    config = load_config()
    if agent_id not in config.agents.profiles:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found",
        )

    agent_ref = config.agents.profiles[agent_id]
    is_enabled = getattr(agent_ref, "enabled", True)

    # If disabled, return disabled status immediately
    if not is_enabled:
        return AgentStatus(
            status="disabled",
            running_task_count=0,
            last_run_at=None,
            last_finish_at=None,
        )

    # If enabled, get workspace and task tracker status
    workspace = await get_agent_for_request(request)
    status_dict = await workspace.task_tracker.get_global_status()
    return AgentStatus(**status_dict)
