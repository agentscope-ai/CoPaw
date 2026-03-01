# -*- coding: utf-8 -*-
"""Multi-workspace management for CoPaw.

Each workspace has its own config, jobs, chats, memory, and skills.
Global resources (providers, tokens, models) are shared across workspaces.
"""

from .models import WorkspaceInfo
from .manager import WorkspaceManager

__all__ = [
    "WorkspaceInfo",
    "WorkspaceManager",
]
