# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
from pathlib import Path

from qwenpaw.app.runner.control_commands.base import (
    BaseControlCommandHandler,
    ControlContext,
)

logger = logging.getLogger(__name__)

_A2A_CONFIG_FILENAME = "a2a_config.json"


def _load_a2a_agents(workspace_dir: Path) -> dict[str, dict]:
    """Load per-agent A2A config from workspace."""
    path = workspace_dir / _A2A_CONFIG_FILENAME
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("agents", {})
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return {}


class A2AListCommandHandler(BaseControlCommandHandler):
    command_name = "/a2a"

    async def handle(self, context: ControlContext) -> str:
        from modules.a2a.client_manager import get_a2a_manager

        workspace_dir = context.workspace.workspace_dir
        agents_cfg = _load_a2a_agents(workspace_dir)

        if not agents_cfg:
            return (
                "暂无已注册的远程 A2A Agent。\n\n"
                "使用 POST /a2a/agents 注册新的 Agent，"
                "或在 A2A 管理页面添加。"
            )

        manager = get_a2a_manager()

        lines = ["**已注册的远程 A2A Agent：**\n"]
        for alias, reg in agents_cfg.items():
            card_info = await manager.get_card_info(reg["url"])
            status = (
                card_info.get("status", "disconnected")
                if card_info
                else "disconnected"
            )
            name = card_info.get("name", "") if card_info else ""
            desc = card_info.get("description", "") if card_info else ""
            status_icon = "🟢" if status == "connected" else "⚪"

            line = f"\n{status_icon} **/{alias}**"
            if name:
                line += f" — {name}"
            if desc:
                line += f"\n   {desc[:80]}"
            if status != "connected":
                line += f"\n   状态: {status}"
            lines.append(line)

        lines.append("\n---\n使用 `/{alias} 你的问题` 直接向远程 Agent 发送消息，例如：")
        for alias in agents_cfg:
            lines.append(f"  `/{alias} 如何部署 ECS？`")

        return "\n".join(lines)
