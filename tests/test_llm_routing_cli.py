# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from click.testing import CliRunner

import copaw.cli.providers_cmd as providers_cmd
from copaw.config.config import Config
from copaw.providers.provider import ModelInfo
from copaw.providers.provider_manager import ModelSlotConfig


@dataclass
class FakeProvider:
    id: str
    name: str
    base_url: str = ""
    api_key: str = ""
    api_key_prefix: str = ""
    is_custom: bool = False
    is_local: bool = False
    require_api_key: bool = True
    models: list[ModelInfo] = field(default_factory=list)
    extra_models: list[ModelInfo] = field(default_factory=list)


class FakeManager:
    def __init__(
        self,
        providers: list[FakeProvider],
        *,
        active_model: ModelSlotConfig | None = None,
    ) -> None:
        self._providers = {provider.id: provider for provider in providers}
        self._active = active_model

    async def list_provider_info(self):
        return [type("Info", (), {"id": provider_id}) for provider_id in self._providers]

    def get_provider(self, provider_id: str):
        return self._providers.get(provider_id)

    def get_active_model(self):
        return self._active


def _runner() -> CliRunner:
    return CliRunner()


def _local_provider() -> FakeProvider:
    return FakeProvider(
        id="llamacpp",
        name="llama.cpp (Local)",
        is_local=True,
        require_api_key=False,
        models=[ModelInfo(id="local-1", name="Local 1")],
    )


def _remote_provider() -> FakeProvider:
    return FakeProvider(
        id="openai",
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_key="sk-test",
        api_key_prefix="sk-",
        models=[ModelInfo(id="gpt-5", name="GPT-5")],
    )


def test_routing_show_reports_active_llm_fallback(monkeypatch) -> None:
    cfg = Config()
    cfg.agents.llm_routing.enabled = True
    cfg.agents.llm_routing.mode = "local_first"
    cfg.agents.llm_routing.local = ModelSlotConfig(
        provider_id="llamacpp",
        model="local-1",
    )
    fake = FakeManager(
        [_local_provider(), _remote_provider()],
        active_model=ModelSlotConfig(provider_id="openai", model="gpt-5"),
    )

    monkeypatch.setattr(providers_cmd, "_manager", lambda: fake)
    monkeypatch.setattr(providers_cmd, "load_config", lambda *_: cfg)
    monkeypatch.setattr(
        providers_cmd,
        "get_config_path",
        lambda: Path("/tmp/copaw-test-config.json"),
    )

    result = _runner().invoke(providers_cmd.models_group, ["routing", "show"])

    assert result.exit_code == 0
    assert "cloud(active_llm): openai / gpt-5" in result.output
    assert "openai / gpt-5" in result.output


def test_routing_config_saves_local_slot_and_fallback(monkeypatch) -> None:
    saved: dict[str, Config] = {}
    config_path = Path("/tmp/copaw-routing-config.json")
    fake = FakeManager(
        [_local_provider(), _remote_provider()],
        active_model=ModelSlotConfig(provider_id="openai", model="gpt-5"),
    )
    confirm_answers = iter([True])
    choice_answers = iter(["Local first"])

    monkeypatch.setattr(providers_cmd, "_manager", lambda: fake)
    monkeypatch.setattr(
        providers_cmd,
        "_load_app_config",
        lambda: (Config(), config_path),
    )
    monkeypatch.setattr(
        providers_cmd,
        "prompt_confirm",
        lambda *_args, **_kwargs: next(confirm_answers),
    )
    monkeypatch.setattr(
        providers_cmd,
        "prompt_choice",
        lambda *_args, **_kwargs: next(choice_answers),
    )
    monkeypatch.setattr(
        providers_cmd,
        "save_config",
        lambda config, *_args, **_kwargs: saved.setdefault("config", config),
    )

    result = _runner().invoke(providers_cmd.models_group, ["routing", "config"])

    assert result.exit_code == 0
    routing_cfg = saved["config"].agents.llm_routing
    assert routing_cfg.enabled is True
    assert routing_cfg.mode == "local_first"
    assert routing_cfg.local.provider_id == "llamacpp"
    assert routing_cfg.local.model == "local-1"
    assert routing_cfg.cloud is None


def test_routing_disable_preserves_slots(monkeypatch) -> None:
    saved: dict[str, Config] = {}
    config_path = Path("/tmp/copaw-routing-disable.json")
    cfg = Config()
    cfg.agents.llm_routing.enabled = True
    cfg.agents.llm_routing.mode = "cloud_first"
    cfg.agents.llm_routing.local = ModelSlotConfig(
        provider_id="llamacpp",
        model="local-1",
    )
    cfg.agents.llm_routing.cloud = ModelSlotConfig(
        provider_id="openai",
        model="gpt-5",
    )

    monkeypatch.setattr(
        providers_cmd,
        "_load_app_config",
        lambda: (cfg, config_path),
    )
    monkeypatch.setattr(
        providers_cmd,
        "save_config",
        lambda config, *_args, **_kwargs: saved.setdefault("config", config),
    )

    result = _runner().invoke(providers_cmd.models_group, ["routing", "disable"])

    assert result.exit_code == 0
    routing_cfg = saved["config"].agents.llm_routing
    assert routing_cfg.enabled is False
    assert routing_cfg.local.provider_id == "llamacpp"
    assert routing_cfg.local.model == "local-1"
    assert routing_cfg.cloud is not None
    assert routing_cfg.cloud.provider_id == "openai"
