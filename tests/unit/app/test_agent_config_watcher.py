# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import os
import time
from types import SimpleNamespace
from typing import Any

import qwenpaw.app.agent_config_watcher as watcher_module
from qwenpaw.app.agent_config_watcher import (
    AgentConfigWatcher,
    _mcp_hash,
    _skill_manifest_hash,
)


class Dumpable:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        assert mode == "json"
        return self._payload


def test_mcp_hash_tracks_client_config_changes() -> None:
    mcp = SimpleNamespace(
        clients={
            "search": Dumpable(
                {
                    "name": "search",
                    "enabled": True,
                    "command": "npx",
                },
            ),
        },
    )
    original_hash = _mcp_hash(mcp)

    mcp.clients["search"] = Dumpable(
        {
            "name": "search",
            "enabled": False,
            "command": "npx",
        },
    )

    assert _mcp_hash(mcp) != original_hash


def test_skill_manifest_hash_ignores_json_whitespace(tmp_path) -> None:
    manifest_path = tmp_path / "skill.json"
    manifest_path.write_text(
        '{"skills":{"news":{"enabled":true}}}',
        encoding="utf-8",
    )
    original_hash = _skill_manifest_hash(manifest_path)

    manifest_path.write_text(
        '{\n  "skills": {\n    "news": {\n      "enabled": true\n    }\n  }\n}',
        encoding="utf-8",
    )
    assert _skill_manifest_hash(manifest_path) == original_hash

    manifest_path.write_text(
        '{"skills":{"news":{"enabled":false}}}',
        encoding="utf-8",
    )
    assert _skill_manifest_hash(manifest_path) != original_hash


def test_read_mtime_tracks_agent_and_skill_files(tmp_path) -> None:
    watcher = AgentConfigWatcher(
        agent_id="default",
        workspace_dir=tmp_path,
        workspace=SimpleNamespace(),
    )

    assert watcher._read_mtime() == (0.0, 0.0)

    (tmp_path / "agent.json").write_text("{}", encoding="utf-8")
    (tmp_path / "skill.json").write_text("{}", encoding="utf-8")

    config_mtime, skill_mtime = watcher._read_mtime()
    assert config_mtime > 0.0
    assert skill_mtime > 0.0


async def test_check_reloads_when_skill_manifest_changes(
    monkeypatch,
    tmp_path,
) -> None:
    class Manager:
        def __init__(self) -> None:
            self.reloaded_agents: list[str] = []

        async def reload_agent(self, agent_id: str) -> None:
            self.reloaded_agents.append(agent_id)

    monkeypatch.setattr(
        watcher_module,
        "load_agent_config",
        lambda _agent_id: SimpleNamespace(
            channels=None,
            heartbeat=None,
            mcp=None,
        ),
    )

    (tmp_path / "agent.json").write_text("{}", encoding="utf-8")
    (tmp_path / "skill.json").write_text('{"skills":{}}', encoding="utf-8")

    manager = Manager()
    watcher = AgentConfigWatcher(
        agent_id="default",
        workspace_dir=tmp_path,
        workspace=SimpleNamespace(_manager=manager),
    )
    watcher._snapshot()

    (tmp_path / "skill.json").write_text(
        '{"skills":{"news":{"enabled":true}}}',
        encoding="utf-8",
    )
    next_mtime = time.time() + 5
    os.utime(tmp_path / "skill.json", (next_mtime, next_mtime))

    await watcher._check()

    assert manager.reloaded_agents == ["default"]
    assert watcher._disabled is True
