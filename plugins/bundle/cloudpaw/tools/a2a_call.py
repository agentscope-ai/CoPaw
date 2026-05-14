# -*- coding: utf-8 -*-
"""A2A call tool: send a message to a remote A2A Agent.

Supports resolution by alias (reading from per-agent a2a_config.json)
or by direct URL.  When using alias, auth config is automatically
applied from the stored registration.

Streaming mode: yields ToolResponse chunks progressively as events
arrive from the remote A2A agent, enabling real-time frontend updates.
"""

import json
import logging
import time
from collections.abc import AsyncGenerator

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

logger = logging.getLogger(__name__)


async def a2a_call(  # pylint: disable=too-many-branches,too-many-statements
    message: str,
    agent_alias: str = "",
    agent_url: str = "",
    context_id: str = "",
) -> AsyncGenerator[ToolResponse, None]:
    """向远程 A2A Agent 发送消息并流式获取响应。

    通过 ``agent_alias``（已注册的别名）或 ``agent_url``（URL）指定目标 Agent。
    使用别名时自动应用已注册的认证配置。

    每次收到远程 Agent 的流式事件时，yield 一个累积的 ToolResponse，
    使前端能够实时显示进度。

    Args:
        message:     发送给远程 Agent 的文本消息
        agent_alias: 已注册的远程 Agent 别名（优先使用，通过 a2a_list 查看可用别名）
        agent_url:   远程 A2A Agent 的基础 URL（alias 为空时使用）
        context_id:  可选，会话上下文 ID（多轮对话时传入上次返回的 contextId）

    Yields:
        ToolResponse: 渐进式的响应，包含：
        - response_text: 累积的文本内容
        - task_state: 当前状态（working/completed/error）
        - event_count: 已接收的事件数
    """
    from modules.a2a.client_manager import get_a2a_manager

    manager = get_a2a_manager()
    resolved_url = agent_url
    auth_type = ""
    auth_token = ""

    if agent_alias:
        from .a2a_config_helper import resolve_agent_by_alias

        reg = resolve_agent_by_alias(agent_alias)
        if not reg:
            yield ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=json.dumps(
                            {
                                "error": (
                                    f"未找到别名为 '{agent_alias}' "
                                    f"的已注册 A2A Agent。"
                                    f"请先通过 a2a_list "
                                    f"查看可用的 Agent。"
                                ),
                                "task_state": "error",
                            },
                            ensure_ascii=False,
                        ),
                    ),
                ],
                is_last=True,
            )
            return
        resolved_url = reg["url"]
        auth_type = reg.get("auth_type", "")
        auth_token = reg.get("auth_token", "")
        gateway_config = reg.get("gateway_config")

        card_info = await manager.get_card_info(resolved_url)
        if not card_info or card_info.get("status") != "connected":
            try:
                await manager.connect(
                    agent_url=resolved_url,
                    auth_type=auth_type,
                    auth_token=auth_token,
                    gateway_config=gateway_config,
                )
            except Exception as e:
                yield ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=json.dumps(
                                {
                                    "error": (
                                        f"连接 '{agent_alias}' "
                                        f"({resolved_url}) 失败: {e}"
                                    ),
                                    "task_state": "error",
                                },
                                ensure_ascii=False,
                            ),
                        ),
                    ],
                    is_last=True,
                )
                return

    if not resolved_url:
        yield ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=json.dumps(
                        {
                            "error": "必须提供 agent_alias 或 agent_url 之一。",
                            "task_state": "error",
                        },
                        ensure_ascii=False,
                    ),
                ),
            ],
            is_last=True,
        )
        return

    accumulated_text = ""
    events_count = 0
    final_task_id = ""
    final_context_id = context_id
    final_state = ""
    last_yield_time = 0.0
    MIN_YIELD_INTERVAL = 0.15
    prev_text = ""

    try:
        async for event in manager.send_message(
            agent_url=resolved_url,
            message=message,
            context_id=context_id,
            streaming=True,
        ):
            events_count += 1
            event_text = _extract_text_from_event(event)
            if event_text:
                accumulated_text += event_text

            # 更新元数据
            ev_type = event.get("type", "")
            if ev_type == "task":
                task_data = event.get("task", {})
                if "id" in task_data:
                    final_task_id = task_data["id"]
                if "contextId" in task_data:
                    final_context_id = task_data["contextId"]
                status = task_data.get("status", {})
                if "state" in status:
                    final_state = status["state"]
            elif ev_type == "status_update":
                su = event.get("statusUpdate", {})
                if "taskId" in su:
                    final_task_id = su["taskId"]
                if "contextId" in su:
                    final_context_id = su["contextId"]
                status = su.get("status", {})
                if "state" in status:
                    final_state = status["state"]

            # Yield 累积文本（非最终）— 节流：仅在文本有实质增长或间隔足够时 yield
            now = time.time()
            text_len_delta = len(accumulated_text) - len(prev_text)
            should_yield = (
                text_len_delta >= 20
                or (
                    text_len_delta > 0
                    and now - last_yield_time >= MIN_YIELD_INTERVAL
                )
                or final_state in ("completed", "failed", "canceled")
            )
            if should_yield:
                logger.debug(
                    "a2a_call yield #%d: text_len=%d, delta=%d, state=%s",
                    events_count,
                    len(accumulated_text),
                    text_len_delta,
                    final_state or "working",
                )
                yield ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=json.dumps(
                                {
                                    "response_text": accumulated_text,
                                    "task_id": final_task_id,
                                    "context_id": final_context_id,
                                    "task_state": final_state or "working",
                                    "event_count": events_count,
                                },
                                ensure_ascii=False,
                            ),
                        ),
                    ],
                    is_last=False,
                )
                last_yield_time = now
                prev_text = accumulated_text

        logger.info(
            "a2a_call success: %s (%s), events=%d, state=%s",
            agent_alias or resolved_url,
            resolved_url,
            events_count,
            final_state,
        )

    except Exception as e:
        logger.error("a2a_call failed for %s: %s", resolved_url, e)
        yield ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=json.dumps(
                        {
                            "response_text": accumulated_text,
                            "error": str(e),
                            "task_id": final_task_id,
                            "context_id": final_context_id,
                            "task_state": "error",
                            "event_count": events_count,
                        },
                        ensure_ascii=False,
                    ),
                ),
            ],
            is_last=True,
        )
        return

    # 最终结果
    logger.debug(
        "a2a_call FINAL: events=%d, text_len=%d, state=%s",
        events_count,
        len(accumulated_text),
        final_state or "completed",
    )
    yield ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=json.dumps(
                    {
                        "response_text": accumulated_text,
                        "task_id": final_task_id,
                        "context_id": final_context_id,
                        "task_state": final_state or "completed",
                        "event_count": events_count,
                    },
                    ensure_ascii=False,
                ),
            ),
        ],
        is_last=True,
    )


def _extract_text_from_event(event: dict) -> str:
    """Extract text content from an A2A event dict."""
    texts = []
    ev_type = event.get("type", "")

    def extract_parts(parts: list) -> None:
        for part in parts or []:
            if isinstance(part, dict) and "text" in part:
                texts.append(part["text"])

    if ev_type == "task":
        task_data = event.get("task", {})
        status = task_data.get("status", {})
        msg = status.get("message", {})
        extract_parts(msg.get("parts", []))
        for artifact in task_data.get("artifacts", []):
            extract_parts(artifact.get("parts", []))
    elif ev_type == "status_update":
        su = event.get("statusUpdate", {})
        status = su.get("status", {})
        msg = status.get("message", {})
        extract_parts(msg.get("parts", []))
    elif ev_type == "artifact_update":
        au = event.get("artifactUpdate", {})
        artifact = au.get("artifact", {})
        extract_parts(artifact.get("parts", []))
    elif ev_type == "message":
        msg = event.get("message", {})
        extract_parts(msg.get("parts", []))

    return "".join(texts)
