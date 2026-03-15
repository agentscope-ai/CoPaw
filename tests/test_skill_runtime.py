# -*- coding: utf-8 -*-
import os

import pytest
from fastapi import HTTPException

from copaw.agents import skills_manager as skills_manager_module
from copaw.agents.skill_metadata import parse_skill_metadata_from_content
from copaw.agents.skill_runtime import (
    apply_skill_env_overrides,
    compute_skill_eligibility,
    has_skill_env_overrides,
)
from copaw.agents.skills_manager import SkillInfo, SkillService
from copaw.app.routers.skills import (
    MASKED_ENV_VALUE,
    _build_skill_config_view,
    _merge_skill_env_payload,
    _validate_skill_env_payload,
)
from copaw.config.config import Config, SkillEntryConfig, SkillsConfig


class DummySkill:
    def __init__(self, name, metadata):
        self.name = name
        self.metadata = metadata


def test_skill_metadata_enables_api_key_backed_eligibility(
    monkeypatch,
) -> None:
    monkeypatch.delenv("DEMO_API_KEY", raising=False)

    content = """---
name: demo_skill
description: demo
metadata:
  {
    "copaw":
      {
        "skillKey": "demo_alias",
        "primaryEnv": "DEMO_API_KEY",
        "requires": { "env": ["DEMO_API_KEY"] }
      }
  }
---
demo
"""

    metadata = parse_skill_metadata_from_content(content)
    assert metadata is not None
    assert metadata.primary_env == "DEMO_API_KEY"

    empty_config = Config()
    missing = compute_skill_eligibility(
        config=empty_config,
        skill_name="demo_skill",
        metadata=metadata,
    )
    assert missing.eligible is False
    assert missing.missing_env == ["DEMO_API_KEY"]

    configured = Config(
        skills=SkillsConfig(
            entries={
                "demo_alias": SkillEntryConfig(apiKey="secret-token"),
            },
        ),
    )
    eligible = compute_skill_eligibility(
        config=configured,
        skill_name="demo_skill",
        metadata=metadata,
    )
    assert eligible.eligible is True
    assert eligible.missing_env == []


def test_apply_skill_env_overrides_injects_and_restores(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_API_KEY", "existing-token")
    monkeypatch.setenv("DEMO_REGION", "us")

    metadata = parse_skill_metadata_from_content(
        """---
name: demo_skill
description: demo
metadata:
  {
        "copaw":
      {
        "skillKey": "demo_alias",
        "primaryEnv": "DEMO_API_KEY",
        "requires": { "env": ["DEMO_API_KEY", "DEMO_REGION"] }
      }
  }
---
demo
""",
    )
    assert metadata is not None

    config = Config(
        skills=SkillsConfig(
            entries={
                "demo_alias": SkillEntryConfig(
                    apiKey="secret-token",
                    env={"DEMO_REGION": "cn"},
                ),
            },
        ),
    )

    skill = DummySkill(name="demo_skill", metadata=metadata)
    assert has_skill_env_overrides([skill], config) is True

    with apply_skill_env_overrides([skill], config):
        assert os.environ["DEMO_API_KEY"] == "secret-token"
        assert os.environ["DEMO_REGION"] == "cn"

    assert os.environ["DEMO_API_KEY"] == "existing-token"
    assert os.environ["DEMO_REGION"] == "us"


def test_apply_skill_env_overrides_rejects_conflicting_values(
    monkeypatch,
) -> None:
    monkeypatch.delenv("DEMO_API_KEY", raising=False)

    metadata = parse_skill_metadata_from_content(
        """---
name: demo_skill
description: demo
metadata:
  {
    "copaw":
      {
        "primaryEnv": "DEMO_API_KEY",
        "requires": { "env": ["DEMO_API_KEY"] }
      }
  }
---
demo
""",
    )
    assert metadata is not None

    config = Config(
        skills=SkillsConfig(
            entries={
                "skill_a": SkillEntryConfig(apiKey="first-token"),
                "skill_b": SkillEntryConfig(apiKey="second-token"),
            },
        ),
    )

    skill_a = DummySkill(name="skill_a", metadata=metadata)
    skill_b = DummySkill(name="skill_b", metadata=metadata)

    with pytest.raises(ValueError) as exc:
        with apply_skill_env_overrides([skill_a, skill_b], config):
            pass

    assert "DEMO_API_KEY" in str(exc.value)


def test_apply_skill_env_overrides_filters_undeclared_env(monkeypatch) -> None:
    monkeypatch.delenv("UNDECLARED_ENV", raising=False)
    monkeypatch.delenv("DEMO_REGION", raising=False)

    metadata = parse_skill_metadata_from_content(
        """---
name: demo_skill
description: demo
metadata:
  {
    "copaw":
      {
        "requires": { "env": ["DEMO_REGION"] }
      }
  }
---
demo
""",
    )
    assert metadata is not None

    config = Config(
        skills=SkillsConfig(
            entries={
                "demo_skill": SkillEntryConfig(
                    env={
                        "DEMO_REGION": "cn",
                        "UNDECLARED_ENV": "should-not-be-injected",
                    },
                ),
            },
        ),
    )

    skill = DummySkill(name="demo_skill", metadata=metadata)
    with apply_skill_env_overrides([skill], config):
        assert os.environ["DEMO_REGION"] == "cn"
        assert "UNDECLARED_ENV" not in os.environ


def test_validate_skill_env_payload_rejects_undeclared_keys() -> None:
    metadata = parse_skill_metadata_from_content(
        """---
name: demo_skill
description: demo
metadata:
  {
    "copaw":
      {
        "skillKey": "demo_alias",
        "primaryEnv": "DEMO_API_KEY",
        "requires": { "env": ["DEMO_API_KEY", "DEMO_REGION"] }
      }
  }
---
demo
""",
    )
    assert metadata is not None

    skill = SkillInfo(
        name="demo_skill",
        content="demo",
        source="builtin",
        path="/tmp/demo_skill",
        metadata=metadata,
        resolved_skill_key="demo_alias",
    )

    _validate_skill_env_payload(
        skill,
        {"DEMO_REGION": "cn", "DEMO_API_KEY": "secret-token"},
    )

    with pytest.raises(HTTPException) as exc:
        _validate_skill_env_payload(
            skill,
            {"OPENAI_API_KEY": "should-not-be-allowed"},
        )

    assert exc.value.status_code == 400
    assert "OPENAI_API_KEY" in str(exc.value.detail)


def test_build_skill_config_view_masks_env_values() -> None:
    view = _build_skill_config_view(
        "demo_skill",
        SkillEntryConfig(
            enabled=True,
            env={"DEMO_REGION": "cn", "EMPTY_VALUE": ""},
            config={"endpoint": "https://example.com"},
        ),
    )

    assert view.env["DEMO_REGION"] == MASKED_ENV_VALUE
    assert view.env["EMPTY_VALUE"] == ""
    assert view.env_keys == ["DEMO_REGION", "EMPTY_VALUE"]


def test_merge_skill_env_payload_preserves_masked_values() -> None:
    existing = SkillEntryConfig(
        env={"DEMO_REGION": "cn", "OTHER_ENV": "kept"},
    )

    merged = _merge_skill_env_payload(
        existing,
        {
            "DEMO_REGION": MASKED_ENV_VALUE,
            "OTHER_ENV": "updated",
        },
    )

    assert merged["DEMO_REGION"] == "cn"
    assert merged["OTHER_ENV"] == "updated"


def test_merge_skill_env_payload_rejects_mask_for_new_key() -> None:
    existing = SkillEntryConfig(env={"DEMO_REGION": "cn"})

    with pytest.raises(HTTPException) as exc:
        _merge_skill_env_payload(
            existing,
            {
                "NEW_SECRET": MASKED_ENV_VALUE,
            },
        )

    assert exc.value.status_code == 400
    assert "NEW_SECRET" in str(exc.value.detail)


def test_skill_entry_config_normalizes_null_api_key() -> None:
    entry = SkillEntryConfig.model_validate({"apiKey": None})
    assert entry.api_key == ""


def test_get_skill_reads_requested_directory_only(
    tmp_path,
    monkeypatch,
) -> None:
    builtin_dir = tmp_path / "builtin"
    customized_dir = tmp_path / "customized"
    active_dir = tmp_path / "active"
    builtin_dir.mkdir()
    customized_dir.mkdir()
    active_dir.mkdir()

    skill_dir = customized_dir / "demo_skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: demo_skill
description: demo
---
demo
""",
        encoding="utf-8",
    )

    def _builtin_dir():
        return builtin_dir

    def _customized_dir():
        return customized_dir

    def _active_dir():
        return active_dir

    def _config():
        return Config()

    monkeypatch.setattr(
        skills_manager_module,
        "get_builtin_skills_dir",
        _builtin_dir,
    )
    monkeypatch.setattr(
        skills_manager_module,
        "get_customized_skills_dir",
        _customized_dir,
    )
    monkeypatch.setattr(
        skills_manager_module,
        "get_active_skills_dir",
        _active_dir,
    )
    monkeypatch.setattr(
        skills_manager_module,
        "load_config",
        _config,
    )

    def _should_not_scan(*args, **kwargs):
        raise AssertionError("get_skill should not scan all skills")

    monkeypatch.setattr(
        skills_manager_module,
        "_read_skills_from_dir",
        _should_not_scan,
    )

    skill = SkillService.get_skill("demo_skill")
    assert skill is not None
    assert skill.name == "demo_skill"
    assert skill.source == "customized"
