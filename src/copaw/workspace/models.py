# -*- coding: utf-8 -*-
"""Data models for workspace management."""
from __future__ import annotations

import time
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkspaceInfo(BaseModel):
    """A single workspace entry in workspaces.json."""

    id: str = Field(default_factory=lambda: "ws_" + uuid.uuid4().hex[:12])
    name: str = "default"
    path: str = ""  # Relative to WORKING_DIR/workspaces/
    created_at: float = Field(default_factory=time.time)
    is_active: bool = False


class WorkspacesFile(BaseModel):
    """Root structure of workspaces.json."""

    workspaces: List[WorkspaceInfo] = Field(default_factory=list)
    active_id: Optional[str] = None
