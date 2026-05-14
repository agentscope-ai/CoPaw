# -*- coding: utf-8 -*-
"""Pure business logic for sedimenting a session into a workspace skill."""

from __future__ import annotations

import logging
from pathlib import Path

import frontmatter

from ..store import (
    get_workspace_skills_dir,
    suggest_conflict_name,
)
from ..workspace_service import SkillService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Synchronous name-conflict check
# ---------------------------------------------------------------------------


def name_conflict(
    workspace_dir: Path,
    normalized_name: str,
) -> tuple[str, str] | None:
    """Return ``(conflicting_name, suggested_rename)`` if the name is
    taken, else ``None``.
    """
    skill_root = get_workspace_skills_dir(workspace_dir)
    if not (skill_root / normalized_name).exists():
        return None
    existing = (
        {p.name for p in skill_root.iterdir() if p.is_dir()}
        if skill_root.exists()
        else set()
    )
    return normalized_name, suggest_conflict_name(
        normalized_name,
        existing,
    )


# ---------------------------------------------------------------------------
# Rendering + materialization
# ---------------------------------------------------------------------------


def render_skill_md(
    *,
    proposed_name: str,
    description: str,
    body: str,
) -> str:
    """Render a full ``SKILL.md`` (frontmatter + body)."""
    post = frontmatter.Post(body or "")
    post["name"] = proposed_name
    post["description"] = description
    return frontmatter.dumps(post)


def materialize_workspace_skill(
    workspace_dir: Path,
    *,
    proposed_name: str,
    skill_md: str,
) -> str:
    """Persist *skill_md* under ``{workspace}/skills/{proposed_name}``."""
    service = SkillService(workspace_dir)
    skill_name = service.create_skill(
        name=proposed_name,
        content=skill_md,
        enable=True,
        source="agent",
    )
    if not skill_name:
        raise RuntimeError(
            f"Skill '{proposed_name}' was created concurrently. "
            "Re-run /make-skill with a different focus.",
        )
    return skill_name
