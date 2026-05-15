# -*- coding: utf-8 -*-
"""In-memory context usage snapshots for active chat streams."""

from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Optional, Tuple

_UsageKey = Tuple[str, str]

_lock = Lock()
_usage_by_session: Dict[_UsageKey, Dict[str, Any]] = {}


def set_context_usage(
    *,
    agent_id: str,
    session_id: str,
    total_tokens: int,
    max_input_length: int,
) -> None:
    """Store the latest context usage for a running agent session."""
    if not agent_id or not session_id:
        return

    pct = (
        (total_tokens / max_input_length * 100)
        if max_input_length > 0
        else 0.0
    )
    snapshot = {
        "total_tokens": int(total_tokens),
        "max_input_length": int(max_input_length),
        "pct": pct,
    }
    with _lock:
        _usage_by_session[(agent_id, session_id)] = snapshot


def get_context_usage(
    *,
    agent_id: str,
    session_id: str,
) -> Optional[Dict[str, Any]]:
    """Return a copy of the latest context usage snapshot if available."""
    if not agent_id or not session_id:
        return None

    with _lock:
        snapshot = _usage_by_session.get((agent_id, session_id))
        return dict(snapshot) if snapshot else None
