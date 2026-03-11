# -*- coding: utf-8 -*-
"""WeCom AI Bot Channel - Based on wecom-aibot-sdk.

Uses official wecom-aibot-sdk to implement WeCom AI Bot integration, supports:
- Text/Image/Mixed/Voice/File message receiving
- Streaming message replies (typewriter effect)
- Welcome message sending (enter_chat event)
- Connection status logging
- Automatic heartbeat keepalive and reconnection
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from wecom_aibot_sdk import WSClient, generate_req_id
from wecom_aibot_sdk.types import WsFrame
from agentscope_runtime.engine.schemas.agent_schemas import RunStatus

from ..base import (
    BaseChannel,
    ContentType,
    TextContent,
    ImageContent,
    OnReplySent,
    ProcessHandler,
)
from ....config.config import WecomConfig as WecomChannelConfig

if TYPE_CHECKING:
    from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest

logger = logging.getLogger(__name__)

# Streaming message processing timeout (seconds)
STREAM_TIMEOUT = 360
# Max content length per stream frame (bytes), per WeCom official docs
MAX_STREAM_CONTENT_LENGTH = 20480
# Placeholder message while agent is thinking
THINKING_MESSAGE = "Thinking..."
# Group chat type identifier
CHAT_TYPE_GROUP = "group"


class WecomChannel(BaseChannel):
    """WeCom AI Bot Channel."""

    channel = "wecom"

    def __init__(
        self,
        config: WecomChannelConfig,
        process: ProcessHandler,
        on_reply_sent: OnReplySent = None,
    ):
        """Initialize WeCom Channel.

        Args:
            config: WeCom configuration
            process: Message processing function
            on_reply_sent: Reply sent callback
        """
        super().__init__(
            process=process,
            on_reply_sent=on_reply_sent,
            show_tool_details=True,
            filter_tool_messages=config.filter_tool_messages,
            filter_thinking=config.filter_thinking,
            dm_policy=config.dm_policy,
            group_policy=config.group_policy,
            allow_from=config.allow_from,
            deny_message=config.deny_message,
        )
        self.config = config
        self.bot_id = config.bot_id
        self.secret = config.secret
        self.media_dir = Path(config.media_dir).expanduser()
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # SDK client (created on connect)
        self.client: Optional[WSClient] = None
        self.running = False
        self.active_tasks: set[asyncio.Task] = set()

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: WecomChannelConfig,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,  # noqa: ARG003
        filter_tool_messages: bool = False,  # noqa: ARG003
        filter_thinking: bool = False,  # noqa: ARG003
    ) -> "WecomChannel":
        """Create Channel instance from config."""
        return cls(config=config, process=process, on_reply_sent=on_reply_sent)

    @classmethod
    def from_env(
        cls,
        process: ProcessHandler,
        on_reply_sent: OnReplySent = None,
    ) -> "WecomChannel":
        """Create Channel instance from environment variables."""
        import os

        config = WecomChannelConfig(
            enabled=True,
            bot_id=os.getenv("WECOM_BOT_ID", ""),
            secret=os.getenv("WECOM_SECRET", ""),
            media_dir=os.getenv("WECOM_MEDIA_DIR", "~/.copaw/media"),
        )
        return cls(config=config, process=process, on_reply_sent=on_reply_sent)

    # -- Lifecycle -------------------------------------------------------

    async def start(self) -> None:
        """Start Channel and establish WebSocket connection."""
        if self.running:
            logger.warning("WecomChannel is already running")
            return

        if not self.bot_id or not self.secret:
            raise ValueError("WeCom config incomplete: bot_id and secret are required")

        if len(self.bot_id) < 10:
            logger.warning(
                "bot_id length looks suspicious (%d chars), check your config",
                len(self.bot_id),
            )
        if len(self.secret) < 20:
            logger.warning(
                "secret length looks suspicious (%d chars), check your config",
                len(self.secret),
            )

        self.running = True
        logger.info("Starting WeCom Channel, Bot ID: %s... (masked)", self.bot_id[:8])

        # Create SDK WSClient - handles WebSocket, heartbeat, and reconnection
        self.client = WSClient(bot_id=self.bot_id, secret=self.secret)

        # Register all event handlers via SDK .on()
        self._register_handlers()

        # Connect - SDK manages heartbeat and reconnection internally
        try:
            await self.client.connect()
        except Exception as exc:
            logger.error("Failed to start WebSocket client: %s", exc)
            self.running = False
            raise

    async def stop(self) -> None:
        """Stop Channel and close WebSocket connection."""
        if not self.running:
            return

        logger.info("Stopping WeCom Channel")
        self.running = False

        # Wait for all active tasks to finish
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)
            self.active_tasks.clear()

        if self.client:
            await self.client.disconnect()
            self.client = None

        logger.info("WeCom Channel stopped")

    # -- SDK Event Registration ------------------------------------------

    def _register_handlers(self) -> None:
        """Register all SDK event handlers via client.on()."""
        if not self.client:
            return

        # Connection status events
        self.client.on(
            "connected", lambda: logger.info("[WeCom] WebSocket connected"),
        )
        self.client.on(
            "authenticated", lambda: logger.info("[WeCom] Authenticated"),
        )
        self.client.on(
            "disconnected",
            lambda reason: logger.warning("[WeCom] Disconnected: %s", reason),
        )
        self.client.on(
            "reconnecting",
            lambda attempt: logger.info("[WeCom] Reconnecting, attempt %d", attempt),
        )
        self.client.on(
            "error",
            lambda err: logger.error("[WeCom] Error: %s", err),
        )

        # Message events (SDK passes raw WsFrame dict)
        self.client.on("message.text", self._on_text)
        self.client.on("message.image", self._on_image)
        self.client.on("message.mixed", self._on_mixed)
        self.client.on("message.voice", self._on_voice)
        self.client.on("message.file", self._on_file)

        # Event callbacks
        self.client.on("event.enter_chat", self._on_enter_chat)
        self.client.on(
            "event.template_card_event", self._on_template_card_event,
        )
        self.client.on("event.feedback_event", self._on_feedback_event)

    # -- Message Event Handlers ------------------------------------------

    def _on_text(self, frame: WsFrame) -> None:
        """Text message callback (SDK emit calls this synchronously)."""
        self._spawn(self._handle_text(frame))

    def _on_image(self, frame: WsFrame) -> None:
        """Image message callback."""
        self._spawn(self._handle_image(frame))

    def _on_mixed(self, frame: WsFrame) -> None:
        """Mixed message callback."""
        self._spawn(self._handle_mixed(frame))

    def _on_voice(self, frame: WsFrame) -> None:
        """Voice message callback."""
        self._spawn(self._handle_voice(frame))

    def _on_file(self, frame: WsFrame) -> None:
        """File message callback."""
        self._spawn(self._handle_file(frame))

    # -- Event Callback Handlers -----------------------------------------

    def _on_enter_chat(self, frame: WsFrame) -> None:
        """Enter chat event, send welcome message."""
        self._spawn(self._send_welcome(frame))

    def _on_template_card_event(self, frame: WsFrame) -> None:
        """Template card interaction event."""
        body = frame.get("body", {})
        event = body.get("event", {})
        logger.info("[WeCom] Template card event: %s", event.get("eventtype"))

    def _on_feedback_event(self, frame: WsFrame) -> None:
        """User feedback event."""
        body = frame.get("body", {})
        event = body.get("event", {})
        logger.info("[WeCom] User feedback event: %s", event.get("eventtype"))

    # -- Async Task Management -------------------------------------------

    def _spawn(self, coro: Any) -> None:
        """Create async task and track it (non-blocking)."""
        task = asyncio.create_task(coro)
        self.active_tasks.add(task)
        task.add_done_callback(self.active_tasks.discard)

        # -- Message Processing Logic ----------------------------------------

    async def _handle_text(self, frame: WsFrame) -> None:
        """Handle text message."""
        body = frame.get("body", {})
        text = body.get("text", {}).get("content", "")
        chattype = body.get("chattype", "")

        # Strip @bot mention in group chats
        if chattype == CHAT_TYPE_GROUP:
            text = re.sub(r"@\S+", "", text).strip()

        if not text:
            logger.info("[WeCom] Skipping empty text message")
            return

        content_parts = [TextContent(type=ContentType.TEXT, text=text)]
        await self._dispatch(frame, content_parts)

    async def _handle_image(self, frame: WsFrame) -> None:
        """Handle image message."""
        body = frame.get("body", {})
        image = body.get("image", {})
        url = image.get("url", "")
        aes_key = image.get("aeskey", "")

        if not url:
            logger.warning("[WeCom] Image message missing URL, skipping")
            return

        if not aes_key:
            logger.warning("[WeCom] Image message missing aeskey, skipping")
            return

        content_parts = []
        img = await self._download_image(url, aes_key)
        if img:
            content_parts.append(img)

        if not content_parts:
            logger.warning("[WeCom] Image processing failed, skipping message")
            return

        await self._dispatch(frame, content_parts)

    async def _handle_mixed(self, frame: WsFrame) -> None:
        """Handle mixed (text + image) message."""
        body = frame.get("body", {})
        text_parts: list[str] = []
        content_parts = []

        for item in body.get("mixed", {}).get("msg_item", []):
            item_type = item.get("msgtype")
            if item_type == "text":
                t = item.get("text", {}).get("content", "")
                if t:
                    text_parts.append(t)
            elif item_type == "image":
                url = item.get("image", {}).get("url", "")
                aes_key = item.get("image", {}).get("aeskey", "")
                if url and aes_key:
                    img = await self._download_image(url, aes_key)
                    if img:
                        content_parts.append(img)
                elif url and not aes_key:
                    logger.warning("[WeCom] Image in mixed message missing aeskey, skipping image")

        if text_parts:
            content_parts.insert(
                0,
                TextContent(
                    type=ContentType.TEXT,
                    text="\n".join(text_parts),
                ),
            )

        if not content_parts:
            logger.info("[WeCom] Mixed message has no valid content, skipping")
            return

        await self._dispatch(frame, content_parts)

    async def _handle_voice(self, frame: WsFrame) -> None:
        """Handle voice message (already transcribed to text)."""
        body = frame.get("body", {})
        text = body.get("voice", {}).get("content", "")
        if not text:
            logger.info("[WeCom] Voice message has no transcribed text, skipping")
            return

        content_parts = [TextContent(type=ContentType.TEXT, text=text)]
        await self._dispatch(frame, content_parts)

    async def _handle_file(self, frame: WsFrame) -> None:
        """Handle file message (log only, not yet processed)."""
        body = frame.get("body", {})
        file_info = body.get("file", {})
        logger.info(
            "[WeCom] Received file message, filename: %s (not yet handled)",
            file_info.get("name", "unknown"),
        )

        # -- Welcome Message -------------------------------------------------

    async def _send_welcome(self, frame: WsFrame) -> None:
        """Send welcome message (must be called within 5 seconds of enter_chat event)."""
        if not self.client:
            return
        try:
            await self.client.reply_welcome(
                frame,
                {
                    "msgtype": "text",
                    "text": {
                        "content": "Hello! I'm CoPaw AI Assistant. How can I help you?",
                    },
                },
            )
            logger.info("[WeCom] Welcome message sent")
        except Exception as exc:
            logger.error("[WeCom] Failed to send welcome message: %s", exc, exc_info=True)

        # -- Message Dispatch and Streaming Reply ---------------------------

    async def _dispatch(
        self,
        frame: WsFrame,
        content_parts: list,
    ) -> None:
        """Build AgentRequest and initiate streaming reply."""
        headers = frame.get("headers", {})
        req_id = headers.get("req_id", "")
        body = frame.get("body", {})

        from_user = body.get("from", {})
        user_id = from_user.get("userid", "")
        chatid = body.get("chatid") or user_id
        session_id = f"{self.channel}:{chatid}"

        request = self.build_agent_request_from_user_content(
            channel_id=self.channel,
            sender_id=user_id,
            session_id=session_id,
            content_parts=content_parts,
        )

        try:
            await asyncio.wait_for(
                self._stream_reply(request, frame, req_id),
                timeout=STREAM_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.error("[WeCom] Request timeout (req_id=%s)", req_id)
            stream_id = generate_req_id("stream")
            await self._send_stream(
                frame, req_id, stream_id, "Sorry, request timed out. Please try again.", finish=True,
            )

    async def _stream_reply(
        self,
        request: "AgentRequest",
        frame: WsFrame,
        req_id: str,
    ) -> None:
        """Call Agent and reply to user with streaming."""
        if not self.client:
            return

        stream_id = generate_req_id("stream")

        # Send thinking placeholder frame
        await self._send_stream(
            frame, req_id, stream_id, THINKING_MESSAGE, finish=False,
        )

        accumulated = ""
        has_final = False
        event_count = 0

        try:
            async for event in self._process(request):
                event_count += 1
                obj = getattr(event, "object", None)
                status = getattr(event, "status", None)
                ev_type = getattr(event, "type", None)

                logger.debug(
                    "[WeCom] Event #%d: object=%s status=%s type=%s",
                    event_count, obj, status, ev_type,
                )

                if obj == "message" and status == RunStatus.Completed:
                    parts = self._message_to_content_parts(event)
                    logger.debug(
                        "[WeCom] Message completed: parts_count=%d",
                        len(parts),
                    )
                    for part in parts:
                        if part.type == ContentType.TEXT and part.text:
                            accumulated += part.text
                            # Push intermediate frames in real-time
                            await self._send_stream(
                                frame,
                                req_id,
                                stream_id,
                                accumulated,
                                finish=False,
                            )

            # Send final frame
            logger.info(
                "[WeCom] Stream complete: event_count=%d accumulated_len=%d",
                event_count, len(accumulated),
            )
            final_text = accumulated or "Message received."
            await self._send_stream(
                frame, req_id, stream_id, final_text, finish=True,
            )
            has_final = True

        except Exception as exc:
            logger.error("[WeCom] Streaming reply error: %s", exc, exc_info=True)
            if not has_final:
                await self._send_stream(
                    frame,
                    req_id,
                    stream_id,
                    "Sorry, an error occurred while processing your request.",
                    finish=True,
                )

    async def _send_stream(
        self,
        frame: WsFrame,
        req_id: str,
        stream_id: str,
        content: str,
        finish: bool,
    ) -> None:
        """Send one streaming message frame via SDK reply_stream."""
        if not self.client:
            return

        # Truncate content per official docs limit
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > MAX_STREAM_CONTENT_LENGTH:
            content = content_bytes[:MAX_STREAM_CONTENT_LENGTH].decode(
                "utf-8", errors="ignore",
            )
            logger.warning(
                "[WeCom] Stream content exceeds limit, truncated (req_id=%s)", req_id,
            )

        try:
            await self.client.reply_stream(frame, stream_id, content, finish)
            logger.debug(
                "[WeCom] Sent stream frame: finish=%s, len=%d", finish, len(content),
            )
        except Exception as exc:
            logger.error("[WeCom] Failed to send stream frame: %s", exc, exc_info=True)

        # -- Proactive Message Sending ---------------------------------------

    async def send(
        self,
        to_handle: str,
        text: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Proactively send Markdown message to specified session.

        Args:
            to_handle: Session identifier (userid or chatid)
            text: Message text (supports Markdown)
            meta: Metadata (not yet used)
        """
        if not self.client:
            logger.warning("[WeCom] Client not initialized, cannot send proactive message")
            return

        try:
            await self.client.send_message(
                to_handle,
                {"msgtype": "markdown", "markdown": {"content": text}},
            )
            logger.info("[WeCom] Proactive message sent to %s", to_handle)
        except Exception as exc:
            logger.error("[WeCom] Failed to send proactive message: %s", exc, exc_info=True)

        # -- Utility Methods -------------------------------------------------

    async def _download_image(
        self,
        url: str,
        aes_key: str,
    ) -> Optional[ImageContent]:
        """Download and decrypt image using SDK download_file, save locally and return ImageContent."""
        if not self.client:
            logger.error("[WeCom] Client not initialized, cannot download image")
            return None

        try:
            # SDK handles download + AES-256-CBC decryption (with padding fix)
            result = await self.client.download_file(url, aes_key)
            data: bytes = result["buffer"]

            # Detect image format from file header
            suffix = _detect_image_suffix(data) or ".jpg"

            # Generate unique filename and save to media_dir (suffix required by agentscope formatter)
            file_hash = hashlib.md5(data).hexdigest()[:12]
            ts = int(time.time() * 1000)
            filename = f"wecom_img_{ts}_{file_hash}{suffix}"
            save_path = self.media_dir / filename
            save_path.write_bytes(data)

            logger.info("[WeCom] Image downloaded and saved: %s", save_path)
            return ImageContent(
                type=ContentType.IMAGE, image_url=str(save_path),
            )
        except Exception as exc:
            logger.error("[WeCom] Image download/decrypt failed: %s", exc, exc_info=True)
            return None

    async def consume_one(self, payload: Any) -> None:  # noqa: ARG002
        """Consume one message (BaseChannel abstract method, not used in WebSocket mode)."""


def _detect_image_suffix(data: bytes) -> Optional[str]:
    """Detect image format from file magic number, return suffix (with dot)."""
    if len(data) < 12:
        return None

    checks = [
        (data[:8] == b"\x89PNG\r\n\x1a\n", ".png"),
        (data[:3] == b"\xff\xd8\xff", ".jpg"),
        (data[:4] in (b"GIF8", b"GIF9"), ".gif"),
        (data[:4] == b"RIFF" and data[8:12] == b"WEBP", ".webp"),
        (data[:2] == b"BM", ".bmp"),
    ]
    for match, suffix in checks:
        if match:
            return suffix
    return None
