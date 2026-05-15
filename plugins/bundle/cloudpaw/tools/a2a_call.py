# -*- coding: utf-8 -*-
"""A2A call tool: send a message to a remote A2A Agent.

Supports resolution by alias (reading from per-agent a2a_config.json)
or by direct URL.  When using alias, auth config is automatically
applied from the stored registration.

Streaming display: while the call runs, incremental text is pushed to
modules.a2a.call_stream so the frontend SSE endpoint can relay it to
the browser in real time.  The tool itself returns a single final
ToolResponse (no async-generator), keeping the LLM result path simple.
"""

import json
import logging

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

logger = logging.getLogger(__name__)


async def a2a_call(
    message: str,
    agent_alias: str = "",
    agent_url: str = "",
    context_id: str = "",
) -> ToolResponse:
    """向远程 A2A Agent 发送消息并获取响应。

    通过 ``agent_alias``（已注册的别名）或 ``agent_url``（URL）指定目标 Agent。
    使用别名时自动应用已注册的认证配置。

    Args:
        message:     发送给远程 Agent 的文本消息
        agent_alias: 已注册的远程 Agent 别名（优先使用，通过 a2a_list 查看可用别名）
        agent_url:   远程 A2A Agent 的基础 URL（alias 为空时使用）
        context_id:  可选，会话上下文 ID（多轮对话时传入上次返回的 contextId）

    Returns:
        ToolResponse: 远程 Agent 的响应，包含：
        - response_text: Agent 回复的文本内容
        - task_id: 任务 ID（如有）
        - context_id: 会话上下文 ID（用于多轮对话）
        - task_state: 任务最终状态
        - event_count: 收到的事件总数
    """
    from modules.a2a.call_stream import finish_stream, get_stream, start_stream
    from modules.a2a.client_manager import get_a2a_manager

    # Reuse existing queue if one was pre-created (e.g. by /a2a command
    # handler) to avoid the race where the SSE endpoint reads from a
    # stale queue that gets overwritten here.
    stream_queue = get_stream()
    if stream_queue is None:
        stream_queue = start_stream()

    manager = get_a2a_manager()
    resolved_url = agent_url
    auth_type = ""
    auth_token = ""

    if agent_alias:
        from .a2a_config_helper import resolve_agent_by_alias

        reg = resolve_agent_by_alias(agent_alias)
        if not reg:
            finish_stream()
            return ToolResponse(
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
            )
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
                finish_stream()
                return ToolResponse(
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
                )

    if not resolved_url:
        finish_stream()
        return ToolResponse(
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
        )

    try:
        events: list[dict] = []
        accumulated_text = ""

        print(f"[A2A] >>> 开始调用远程 Agent: alias={agent_alias or '(direct)'}, url={resolved_url}", flush=True)
        print(f"[A2A] >>> 发送消息: {message[:100]}", flush=True)

        async for event in manager.send_message(
            agent_url=resolved_url,
            message=message,
            context_id=context_id,
            streaming=True,
        ):
            events.append(event)
            ev_type = event.get("type", "unknown")
            new_text = _build_incremental_text(events)
            if new_text != accumulated_text:
                accumulated_text = new_text
                print(
                    f"[A2A] ◉ Event #{len(events)} type={ev_type} | "
                    f"text_len={len(accumulated_text)} | state=working",
                    flush=True,
                )
                _push(stream_queue, {
                    "response_text": accumulated_text,
                    "task_state": "working",
                    "event_count": len(events),
                })
            else:
                print(
                    f"[A2A] ◉ Event #{len(events)} type={ev_type} | no new text",
                    flush=True,
                )

        result = _build_result(events, context_id)
        print(
            f"[A2A] ✓ 调用完成: events={len(events)}, state={result.get('task_state')}, "
            f"text_len={len(result.get('response_text', ''))}",
            flush=True,
        )
        if result.get("response_text"):
            print(f"[A2A] 响应预览: {result['response_text'][:100]}", flush=True)

        _push(stream_queue, {**result, "final": True})

    except Exception as e:
        import traceback
        print(f"[A2A] ✗ 调用失败: {resolved_url} — {e}", flush=True)
        traceback.print_exc()
        result = {
            "response_text": "",
            "error": str(e),
            "task_id": "",
            "context_id": context_id,
            "task_state": "error",
            "event_count": len(events) if "events" in dir() else 0,
        }
        _push(stream_queue, {**result, "final": True})

    finally:
        finish_stream()

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=json.dumps(result, ensure_ascii=False),
            ),
        ],
    )


def _push(queue, data: dict) -> None:
    """Push data to the stream queue (non-blocking)."""
    try:
        queue.put_nowait(data)
    except Exception:
        pass


def _build_incremental_text(events: list[dict]) -> str:
    """Build cumulative display text from all events so far.

    Prioritises artifact text (the actual answer), falls back to
    status_update text (progress messages).
    """
    artifact_texts: list[str] = []
    status_texts: list[str] = []

    for ev in events:
        ev_type = ev.get("type", "")

        if ev_type == "task":
            task_data = ev.get("task", {})
            msg = task_data.get("status", {}).get("message", {})
            text = _extract_text_from_parts(msg.get("parts", []))
            if text:
                status_texts.append(text)
            for artifact in task_data.get("artifacts", []):
                text = _extract_text_from_parts(artifact.get("parts", []))
                if text:
                    artifact_texts.append(text)

        elif ev_type == "status_update":
            su = ev.get("statusUpdate", {})
            msg = su.get("status", {}).get("message", {})
            text = _extract_text_from_parts(msg.get("parts", []))
            if text:
                status_texts.append(text)

        elif ev_type == "artifact_update":
            artifact = ev.get("artifactUpdate", {}).get("artifact", {})
            text = _extract_text_from_parts(artifact.get("parts", []))
            if text:
                artifact_texts.append(text)

        elif ev_type == "message":
            text = _extract_text_from_parts(
                ev.get("message", {}).get("parts", []),
            )
            if text:
                artifact_texts.append(text)

    result = "".join(artifact_texts)
    if not result and status_texts:
        result = "\n".join(status_texts)
    return result


def _build_result(events: list[dict], initial_context_id: str) -> dict:
    """Build final result dict from all collected events."""
    artifact_texts: list[str] = []
    status_texts: list[str] = []
    final_task_id = ""
    final_context_id = initial_context_id
    final_state = ""

    for ev in events:
        ev_type = ev.get("type", "")

        if ev_type == "task":
            task_data = ev.get("task", {})
            if "id" in task_data:
                final_task_id = task_data["id"]
            if "contextId" in task_data:
                final_context_id = task_data["contextId"]
            status = task_data.get("status", {})
            if "state" in status:
                final_state = status["state"]
            msg = status.get("message", {})
            text = _extract_text_from_parts(msg.get("parts", []))
            if text:
                status_texts.append(text)
            for artifact in task_data.get("artifacts", []):
                text = _extract_text_from_parts(artifact.get("parts", []))
                if text:
                    artifact_texts.append(text)

        elif ev_type == "status_update":
            su = ev.get("statusUpdate", {})
            if "taskId" in su:
                final_task_id = su["taskId"]
            if "contextId" in su:
                final_context_id = su["contextId"]
            status = su.get("status", {})
            if "state" in status:
                final_state = status["state"]
            msg = status.get("message", {})
            text = _extract_text_from_parts(msg.get("parts", []))
            if text:
                status_texts.append(text)

        elif ev_type == "artifact_update":
            au = ev.get("artifactUpdate", {})
            if "taskId" in au:
                final_task_id = au["taskId"]
            if "contextId" in au:
                final_context_id = au["contextId"]
            artifact = au.get("artifact", {})
            text = _extract_text_from_parts(artifact.get("parts", []))
            if text:
                artifact_texts.append(text)

        elif ev_type == "message":
            msg = ev.get("message", {})
            text = _extract_text_from_parts(msg.get("parts", []))
            if text:
                artifact_texts.append(text)

    response_text = "".join(artifact_texts)
    if not response_text and status_texts:
        response_text = "\n".join(status_texts)
    if not response_text and final_state:
        response_text = f"[任务状态: {final_state}]"

    return {
        "response_text": response_text,
        "task_id": final_task_id,
        "context_id": final_context_id,
        "task_state": final_state,
        "event_count": len(events),
    }


def _extract_text_from_parts(parts: list) -> str:
    """Extract concatenated text from a list of A2A message parts."""
    texts = []
    for part in parts or []:
        if isinstance(part, dict) and "text" in part:
            texts.append(part["text"])
    return "".join(texts)
