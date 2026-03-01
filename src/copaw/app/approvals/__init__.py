# -*- coding: utf-8 -*-
"""Approval system for gating high-risk agent operations.

Provides an ApprovalService that can operate in two modes:
- ``auto``: all requests are approved immediately (development/trusted).
- ``manual``: requests wait for an explicit human decision via API.
"""

from .models import ApprovalMode, ApprovalRequest, ApprovalStatus
from .service import ApprovalService

__all__ = [
    "ApprovalMode",
    "ApprovalRequest",
    "ApprovalStatus",
    "ApprovalService",
]
