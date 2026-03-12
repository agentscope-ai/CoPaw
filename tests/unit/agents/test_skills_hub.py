# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from copaw.agents import skills_hub


def test_install_skill_from_hub_rejects_unsafe_bundle_name(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        skills_hub,
        "_fetch_bundle_from_skills_sh_url",
        lambda *_args, **_kwargs: (
            {
                "name": "../../etc/passwd",
                "files": {
                    "SKILL.md": (
                        "---\n"
                        "name: ../../etc/passwd\n"
                        "description: unsafe\n"
                        "---\n"
                    ),
                },
            },
            "https://github.com/example/repo",
        ),
    )

    with pytest.raises(
        ValueError,
        match="Hub bundle skill name must be a safe directory name",
    ):
        skills_hub.install_skill_from_hub(
            bundle_url="https://skills.sh/example/repo/unsafe-skill",
            overwrite=False,
        )
