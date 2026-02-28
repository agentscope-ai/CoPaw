# -*- coding: utf-8 -*-
"""DingTalk Stream callback handler: message -> native dict -> reply."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import dingtalk_stream
from dingtalk_stream import CallbackMessage, ChatbotMessage
from agentscope_runtime.engine.schemas.agent_schemas import (
    TextContent,
)

from ..base import ContentType

from .constants import SENT_VIA_WEBHOOK
from .content_utils import (
    conversation_id_from_chatbot_message,
    dingtalk_content_from_type,
    get_type_mapping,
    sender_from_chatbot_message,
    session_param_from_webhook_url,
)

logger = logging.getLogger(__name__)


class DingTalkChannelHandler(dingtalk_stream.ChatbotHandler):
    """Internal handler: convert DingTalk message to native dict, enqueue via
    manager (thread-safe), await reply_future, then reply."""

    def __init__(
        self,
        main_loop: asyncio.AbstractEventLoop,
        enqueue_callback: Optional[Callable[[Any], None]],
        bot_prefix: str,
        download_url_fetcher,
    ):
        super().__init__()
        self._main_loop = main_loop
        self._enqueue_callback = enqueue_callback
        self._bot_prefix = bot_prefix
        self._download_url_fetcher = download_url_fetcher

    def _emit_native_threadsafe(self, native: dict) -> None:
        if self._enqueue_callback:
            self._main_loop.call_soon_threadsafe(
                self._enqueue_callback,
                native,
            )

    def _parse_rich_content(
        self,
        incoming_message: Any,
    ) -> List[Any]:
        """Parse richText from incoming_message into runtime Content list."""
        content: List[Any] = []
        type_mapping = get_type_mapping()
        try:
            robot_code = getattr(
                incoming_message,
                "robot_code",
                None,
            ) or getattr(incoming_message, "robotCode", None)
            msg_dict = incoming_message.to_dict()
            c = msg_dict.get("content") or {}
            raw = c.get("richText")
            raw = raw or c.get("rich_text")
            rich_list = raw if isinstance(raw, list) else []
            for item in rich_list:
                if not isinstance(item, dict):
                    continue
                if item.get("text") is not None:
                    content.append(
                        TextContent(
                            type=ContentType.TEXT,
                            text=item.get("text") or "",
                        ),
                    )
                dl_code = item.get("downloadCode")
                if not dl_code or not robot_code:
                    continue
                fut = asyncio.run_coroutine_threadsafe(
                    self._download_url_fetcher(
                        download_code=dl_code,
                        robot_code=robot_code,
                    ),
                    self._main_loop,
                )
                download_url = fut.result(timeout=15)
                mapped = type_mapping.get(
                    item.get("type", "file"),
                    item.get("type", "file"),
                )
                content.append(
                    dingtalk_content_from_type(mapped, download_url),
                )

            # -------- 2) single downloadCode (pure picture/file) --------
            if not content:
                dl_code = c.get("downloadCode") or c.get("download_code")
                if dl_code and robot_code:
                    fut = asyncio.run_coroutine_threadsafe(
                        self._download_url_fetcher(
                            download_code=dl_code,
                            robot_code=robot_code,
                        ),
                        self._main_loop,
                    )
                    download_url = fut.result(timeout=15)

                    msgtype = (
                        (
                            msg_dict.get(
                                "msgtype",
                            )
                            or ""
                        )
                        .lower()
                        .strip()
                    )
                    mapped = type_mapping.get(
                        msgtype,
                        msgtype or "file",
                    )
                    if mapped not in ("image", "file", "video", "audio"):
                        mapped = "file"

                    content.append(
                        dingtalk_content_from_type(mapped, download_url),
                    )

        except Exception:
            logger.exception("failed to fetch richText download url(s)")
        return content

    def _message_preview(
        self,
        text: str,
        content: List[Any],
    ) -> str:
        """Build a short preview of user message (max 20 chars) for ack."""
        if text:
            return (text[:20] + ("…" if len(text) > 20 else "")).strip()
        if not content:
            return ""
        parts: List[str] = []
        for item in content:
            if getattr(item, "text", None):
                t = str(item.text or "").strip()
                if t:
                    parts.append(t)
            else:
                t = getattr(item, "type", "file") or "file"
                label = {"image": "[图片]", "file": "[文件]", "video": "[视频]", "audio": "[音频]"}.get(
                    str(t).lower(), "[附件]"
                )
                parts.append(label)
        combined = "".join(parts)[:20]
        return (combined + ("…" if len("".join(parts)) > 20 else "")).strip() or "[消息]"

    async def _send_ack_async(
        self,
        ack_msg: str,
        incoming_message: ChatbotMessage,
    ) -> None:
        """Send ack message asynchronously, prefer sessionWebhook to avoid
        blocking subsequent processing."""
        try:
            session_webhook = getattr(incoming_message, "sessionWebhook", None) or getattr(
                incoming_message, "session_webhook", None
            )
            if session_webhook:
                payload = {"msgtype": "text", "text": {"content": ack_msg}}
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            session_webhook,
                            json=payload,
                            headers={"Content-Type": "application/json; charset=utf-8"},
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as resp:
                            if resp.status >= 400:
                                body_text = await resp.text()
                                logger.warning(
                                    "dingtalk ack via sessionWebhook failed: "
                                    "status=%s body=%s",
                                    resp.status,
                                    body_text[:200],
                                )
                            else:
                                logger.debug("dingtalk ack sent via sessionWebhook")
                except asyncio.TimeoutError:
                    logger.warning("dingtalk ack via sessionWebhook timeout")
                except Exception:
                    logger.exception("dingtalk ack via sessionWebhook error")
                return

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self.reply_text(ack_msg, incoming_message),
            )
        except Exception:
            logger.exception("failed to send ack reply")

    async def process(self, callback: CallbackMessage) -> tuple[int, str]:
        try:
            incoming_message = ChatbotMessage.from_dict(callback.data)

            logger.debug(
                "Dingtalk message received: %s",
                incoming_message.to_dict(),
            )
            content_parts: List[Any] = []
            text = ""
            if incoming_message.text:
                text = (incoming_message.text.content or "").strip()
            if text:
                content_parts.append(
                    TextContent(type=ContentType.TEXT, text=text),
                )
            # Always parse rich content so images/files are not dropped
            # when the message also contains text.
            content = self._parse_rich_content(incoming_message)
            # If text was extracted separately and rich content has no
            # text items, prepend the text so both text and media are
            # preserved in the content list.
            if (
                text
                and content
                and not any(
                    item.type == "text" and item.text for item in content
                )
            ):
                content.insert(
                    0,
                    TextContent(type=ContentType.TEXT, text=text),
                )
            # Use rich content (text + media with local paths) when present.
            parts_to_send = content if content else content_parts

            sender, skip = sender_from_chatbot_message(incoming_message)
            if skip:
                return dingtalk_stream.AckMessage.STATUS_OK, "ok"

            preview = self._message_preview(text, parts_to_send) or "[消息]"
            ack_msg = f'✅ 收到\n"{preview}"\n🌀正在处理中……\n\nTips:如果新任务和历史消息无关，请发送 /new 给我新开会话，放在上下文窗口超限或者出现提示词污染😄'
            asyncio.create_task(self._send_ack_async(ack_msg, incoming_message))

            conversation_id = conversation_id_from_chatbot_message(
                incoming_message,
            )
            loop = asyncio.get_running_loop()
            reply_future: asyncio.Future[str] = loop.create_future()
            meta: Dict[str, Any] = {
                "incoming_message": incoming_message,
                "reply_future": reply_future,
                "reply_loop": loop,
            }
            if conversation_id:
                meta["conversation_id"] = conversation_id
            sw = getattr(incoming_message, "sessionWebhook", None) or getattr(
                incoming_message,
                "session_webhook",
                None,
            )
            if sw:
                meta["session_webhook"] = sw
                sw_exp = getattr(
                    incoming_message,
                    "sessionWebhookExpiredTime",
                    None,
                ) or getattr(
                    incoming_message,
                    "session_webhook_expired_time",
                    None,
                )
                logger.info(
                    "dingtalk recv: session_webhook present "
                    "session_from_url=%s "
                    "expired_time=%s",
                    session_param_from_webhook_url(sw),
                    sw_exp,
                )
            else:
                logger.debug(
                    "dingtalk recv: no sessionWebhook on incoming_message",
                )

            native = {
                "channel_id": "dingtalk",
                "sender_id": sender,
                "content_parts": parts_to_send,
                "meta": meta,
            }
            if sw:
                native["session_webhook"] = sw
            logger.info(
                "dingtalk emit: native has_sw=%s meta_sw=%s",
                bool(native.get("session_webhook")),
                bool((native.get("meta") or {}).get("session_webhook")),
            )
            logger.info("recv from=%s text=%s", sender, text[:100])
            self._emit_native_threadsafe(native)

            response_text = await reply_future
            if response_text == SENT_VIA_WEBHOOK:
                logger.info(
                    "sent to=%s via sessionWebhook (multi-message)",
                    sender,
                )
            else:
                out = self._bot_prefix + response_text
                self.reply_text(out, incoming_message)
                logger.info("sent to=%s text=%r", sender, out[:100])
            return dingtalk_stream.AckMessage.STATUS_OK, "ok"

        except Exception:
            logger.exception("process failed")
            return dingtalk_stream.AckMessage.STATUS_SYSTEM_EXCEPTION, "error"
