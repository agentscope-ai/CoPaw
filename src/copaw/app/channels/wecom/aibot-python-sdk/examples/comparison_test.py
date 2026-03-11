"""
SDK 功能对比测试脚本 — Python 端

用于与 Node.js 端 comparison-test.ts 生成格式一致的日志，
方便逐条对比两端的行为差异。
"""

import asyncio
import hashlib
import json
import os
import platform
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# 将上级目录添加到 sys.path，以便直接运行示例
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aibot import WSClient, WSClientOptions, generate_req_id

# ======================== 结构化日志 ========================


def log_event(category: str, event_type: str, data: dict) -> None:
    """
    统一的日志输出函数，输出格式：
    [ISO时间戳] [CATEGORY] [EVENT_TYPE] JSON数据
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"
    json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    print(f"[{timestamp}] [{category}] [{event_type}] {json_str}", flush=True)


# ======================== 凭证与初始化 ========================

ws_client = WSClient(
    WSClientOptions(
        bot_id="aibxt0pqaD44nP-iIW3xe3p6XPl-KCjdvxX",
        secret="Gi1YaQs9Y0rVKPqXIbIEv7F5eYX1lkUUuMCdEkPdGdA",
    )
)

# 确保下载目录存在
download_dir = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(download_dir, exist_ok=True)

# 模板卡片示例数据
template_card = {
    "card_type": "multiple_interaction",
    "source": {
        "icon_url": "https://wework.qpic.cn/wwpic/252813_jOfDHtcISzuodLa_1629280209/0",
        "desc": "企业微信",
    },
    "main_title": {
        "title": "欢迎使用企业微信",
        "desc": "您的好友正在邀请您加入企业微信",
    },
    "select_list": [
        {
            "question_key": "question_key_one",
            "title": "选择标签1",
            "disable": False,
            "selected_id": "id_one",
            "option_list": [
                {"id": "id_one", "text": "选择器选项1"},
                {"id": "id_two", "text": "选择器选项2"},
            ],
        },
        {
            "question_key": "question_key_two",
            "title": "选择标签2",
            "selected_id": "id_three",
            "option_list": [
                {"id": "id_three", "text": "选择器选项3"},
                {"id": "id_four", "text": "选择器选项4"},
            ],
        },
    ],
    "submit_button": {"text": "提交", "key": "submit_key"},
    "task_id": f"task_id_{int(time.time() * 1000)}",
}


# ======================== 工具函数 ========================


def sha256_hash(data: bytes) -> str:
    """计算 bytes 数据的 SHA-256 哈希值"""
    return hashlib.sha256(data).hexdigest()


def hex_digest(data: bytes, n: int = 32) -> str:
    """获取 bytes 前 N 字节的十六进制摘要"""
    return data[:n].hex()


# ======================== 连接生命周期事件 ========================


@ws_client.on("connected")
def on_connected():
    log_event("CONNECTION", "CONNECTED", {"status": "connected"})


@ws_client.on("authenticated")
def on_authenticated():
    log_event("CONNECTION", "AUTHENTICATED", {"status": "authenticated"})


@ws_client.on("disconnected")
def on_disconnected(reason):
    log_event("CONNECTION", "DISCONNECTED", {"reason": reason})


@ws_client.on("reconnecting")
def on_reconnecting(attempt):
    log_event("CONNECTION", "RECONNECTING", {"attempt": attempt})


@ws_client.on("error")
def on_error(error):
    log_event("CONNECTION", "ERROR", {"message": str(error)})


# ======================== 消息事件 ========================

# 监听所有消息（用于记录原始帧）
@ws_client.on("message")
def on_message(frame):
    body_str = json.dumps(frame.get("body", {}), ensure_ascii=False)[:500]
    log_event("MESSAGE", "RAW", {
        "headers": frame.get("headers", {}),
        "body_preview": body_str,
    })


# 文本消息：根据关键词触发不同的回复逻辑
@ws_client.on("message.text")
async def on_text_message(frame):
    body = frame.get("body", {})
    text_content = body.get("text", {}).get("content", "")

    log_event("MESSAGE", "TEXT", {"content": text_content})

    # -------- 关键词：「卡片」→ 回复模板卡片 --------
    if text_content == "卡片":
        try:
            reply_body = {
                "msgtype": "template_card",
                "template_card": template_card,
            }
            log_event("REPLY", "TEMPLATE_CARD_SEND", {"body": reply_body})
            await ws_client.reply_template_card(frame, template_card)
            log_event("REPLY", "TEMPLATE_CARD_DONE", {"success": True})
        except Exception as err:
            log_event("REPLY", "TEMPLATE_CARD_ERROR", {"error": str(err)})
        return

    # -------- 关键词：「流式卡片」→ 流式 + 模板卡片组合回复 --------
    if text_content == "流式卡片":
        stream_id = generate_req_id("stream")
        try:
            # 第一阶段：流式内容 + 模板卡片
            first_body = {
                "msgtype": "stream_with_template_card",
                "stream": {"id": stream_id, "content": "正在生成卡片内容...", "finish": False},
                "template_card": template_card,
            }
            log_event("REPLY", "STREAM_WITH_CARD_SEND", {"phase": 1, "body": first_body})
            await ws_client.reply_stream_with_card(
                frame, stream_id, "正在生成卡片内容...", False,
                template_card=template_card,
            )

            # 第二阶段：结束流式
            await asyncio.sleep(1)
            second_body = {
                "msgtype": "stream_with_template_card",
                "stream": {"id": stream_id, "content": "卡片内容已生成完毕！", "finish": True},
            }
            log_event("REPLY", "STREAM_WITH_CARD_SEND", {"phase": 2, "body": second_body})
            await ws_client.reply_stream_with_card(
                frame, stream_id, "卡片内容已生成完毕！", True,
            )

            log_event("REPLY", "STREAM_WITH_CARD_DONE", {"success": True})
        except Exception as err:
            log_event("REPLY", "STREAM_WITH_CARD_ERROR", {"error": str(err)})
        return

    # -------- 关键词：「主动发送」→ 主动发送消息 --------
    if text_content == "主动发送":
        chatid = body.get("from", {}).get("userid", "")
        send_body = {
            "msgtype": "markdown",
            "markdown": {"content": "这是一条**主动推送**的消息"},
        }
        log_event("SEND", "SEND_MESSAGE_SEND", {"chatid": chatid, "body": send_body})
        try:
            await ws_client.send_message(chatid, send_body)
            log_event("SEND", "SEND_MESSAGE_DONE", {"success": True})
        except Exception as err:
            log_event("SEND", "SEND_MESSAGE_ERROR", {"error": str(err)})
        return

    # -------- 默认：流式回复（三阶段） --------
    stream_id = generate_req_id("stream")

    try:
        # 第一阶段：中间内容
        phase1_body = {
            "msgtype": "stream",
            "stream": {"id": stream_id, "content": "正在思考中...", "finish": False},
        }
        log_event("REPLY", "STREAM_SEND", {"phase": 1, "body": phase1_body})
        await ws_client.reply_stream(frame, stream_id, "正在思考中...", False)

        # 第二阶段：追加内容
        await asyncio.sleep(1)
        phase2_body = {
            "msgtype": "stream",
            "stream": {"id": stream_id, "content": f'你好！你说的是: "{text_content}"', "finish": False},
        }
        log_event("REPLY", "STREAM_SEND", {"phase": 2, "body": phase2_body})
        await ws_client.reply_stream(frame, stream_id, f'你好！你说的是: "{text_content}"', False)

        # 第三阶段：完成 (finish=True)，附带 msg_item
        await asyncio.sleep(1)
        msg_item = [
            {
                "msgtype": "text",
                "text": {"content": "这是附加的图文混排内容"},
            },
        ]
        phase3_body = {
            "msgtype": "stream",
            "stream": {
                "id": stream_id,
                "content": f'你好！你说的是: "{text_content}"（回复完毕）',
                "finish": True,
                "msg_item": msg_item,
            },
        }
        log_event("REPLY", "STREAM_SEND", {"phase": 3, "body": phase3_body})
        await ws_client.reply_stream(
            frame,
            stream_id,
            f'你好！你说的是: "{text_content}"（回复完毕）',
            True,
            msg_item=msg_item,
        )

        log_event("REPLY", "STREAM_DONE", {"success": True, "stream_id": stream_id})
    except Exception as err:
        log_event("REPLY", "STREAM_ERROR", {"error": str(err), "stream_id": stream_id})


# ======================== 图片消息 ========================


@ws_client.on("message.image")
async def on_image_message(frame):
    body = frame.get("body", {})
    image_url = body.get("image", {}).get("url")
    aes_key = body.get("image", {}).get("aeskey")

    log_event("MESSAGE", "IMAGE", {"url": image_url, "has_aeskey": bool(aes_key)})

    if not image_url:
        return

    try:
        buffer, filename = await ws_client.download_file(image_url, aes_key)
        file_hash = sha256_hash(buffer)
        digest = hex_digest(buffer, 32)

        log_event("DOWNLOAD", "IMAGE_SUCCESS", {
            "buffer_length": len(buffer),
            "filename": filename,
            "sha256": file_hash,
            "hex_digest_32": digest,
        })

        # 保存文件
        url_path = urlparse(image_url).path
        file_name = filename or os.path.basename(url_path) or f"image_{int(time.time() * 1000)}"
        save_path = os.path.join(download_dir, file_name)
        with open(save_path, "wb") as f:
            f.write(buffer)

        log_event("DOWNLOAD", "IMAGE_SAVED", {"path": save_path})
    except Exception as err:
        log_event("DOWNLOAD", "IMAGE_ERROR", {"error": str(err)})


# ======================== 文件消息 ========================


@ws_client.on("message.file")
async def on_file_message(frame):
    body = frame.get("body", {})
    file_url = body.get("file", {}).get("url")
    aes_key = body.get("file", {}).get("aeskey")

    log_event("MESSAGE", "FILE", {"url": file_url, "has_aeskey": bool(aes_key)})

    if not file_url:
        return

    try:
        buffer, filename = await ws_client.download_file(file_url, aes_key)
        file_hash = sha256_hash(buffer)
        digest = hex_digest(buffer, 32)

        log_event("DOWNLOAD", "FILE_SUCCESS", {
            "buffer_length": len(buffer),
            "filename": filename,
            "sha256": file_hash,
            "hex_digest_32": digest,
        })

        # 保存文件
        url_path = urlparse(file_url).path
        file_name = filename or os.path.basename(url_path) or f"file_{int(time.time() * 1000)}"
        save_path = os.path.join(download_dir, file_name)
        with open(save_path, "wb") as f:
            f.write(buffer)

        log_event("DOWNLOAD", "FILE_SAVED", {"path": save_path})
    except Exception as err:
        log_event("DOWNLOAD", "FILE_ERROR", {"error": str(err)})


# ======================== 图文混排消息 ========================


@ws_client.on("message.mixed")
def on_mixed_message(frame):
    body = frame.get("body", {})
    items = body.get("mixed", {}).get("msg_item", [])

    item_summary = [
        {
            "index": index,
            "msgtype": item.get("msgtype"),
            "text_content": item.get("text", {}).get("content") if item.get("msgtype") == "text" else None,
            "image_url": item.get("image", {}).get("url") if item.get("msgtype") == "image" else None,
        }
        for index, item in enumerate(items)
    ]

    log_event("MESSAGE", "MIXED", {
        "item_count": len(items),
        "items": item_summary,
    })


# ======================== 语音消息 ========================


@ws_client.on("message.voice")
def on_voice_message(frame):
    body = frame.get("body", {})
    voice_content = body.get("voice", {}).get("content", "")

    log_event("MESSAGE", "VOICE", {"content": voice_content})


# ======================== 事件处理 ========================

# 进入会话 → 发送欢迎语
@ws_client.on("event.enter_chat")
async def on_enter_chat(frame):
    welcome_body = {
        "msgtype": "text",
        "text": {"content": "您好！我是智能助手，有什么可以帮您的吗？"},
    }

    log_event("EVENT", "ENTER_CHAT", {"frame_headers": frame.get("headers", {})})
    log_event("REPLY", "WELCOME_SEND", {"body": welcome_body})

    try:
        await ws_client.reply_welcome(frame, welcome_body)
        log_event("REPLY", "WELCOME_DONE", {"success": True})
    except Exception as err:
        log_event("REPLY", "WELCOME_ERROR", {"error": str(err)})


# 模板卡片事件 → 更新模板卡片
@ws_client.on("event.template_card_event")
async def on_template_card_event(frame):
    body = frame.get("body", {})
    event = body.get("event", {})

    log_event("EVENT", "TEMPLATE_CARD_EVENT", {"event": event})

    # 构建更新后的卡片（与原始卡片保持一致，只更新 task_id）
    updated_card = {
        **template_card,
        "task_id": event.get("task_id", template_card["task_id"]),
    }

    update_body = {
        "response_type": "update_template_card",
        "template_card": updated_card,
    }

    log_event("REPLY", "UPDATE_TEMPLATE_CARD_SEND", {"body": update_body})

    try:
        await ws_client.update_template_card(frame, updated_card)
        log_event("REPLY", "UPDATE_TEMPLATE_CARD_DONE", {"success": True})
    except Exception as err:
        log_event("REPLY", "UPDATE_TEMPLATE_CARD_ERROR", {"error": str(err)})


# 用户反馈事件
@ws_client.on("event.feedback_event")
def on_feedback_event(frame):
    body = frame.get("body", {})
    event = body.get("event", {})

    log_event("EVENT", "FEEDBACK_EVENT", {"event": event})


# ======================== 启动 ========================


def main():
    """启动机器人"""
    log_event("SYSTEM", "STARTING", {"sdk": "python", "version": "1.0.0"})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 注册优雅退出（Windows 不支持 add_signal_handler）
    if platform.system() != "Windows":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: _shutdown(loop))

    try:
        loop.run_until_complete(ws_client.connect())
        loop.run_forever()
    except KeyboardInterrupt:
        _shutdown(loop)
    finally:
        log_event("SYSTEM", "STOPPING", {"reason": "shutdown"})
        ws_client.disconnect()
        loop.close()


def _shutdown(loop: asyncio.AbstractEventLoop):
    log_event("SYSTEM", "STOPPING", {"reason": "signal"})
    ws_client.disconnect()
    loop.stop()


if __name__ == "__main__":
    main()
