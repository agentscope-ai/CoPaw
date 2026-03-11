"""
消息处理器

对标 Node.js SDK src/message-handler.ts
负责解析 WebSocket 帧并分发为具体的消息事件和事件回调。
"""

import json
from typing import Any

from .types import MessageType, WsCmd, WsFrame


class MessageHandler:
    """
    消息处理器

    负责解析 WebSocket 帧并分发为具体的消息事件和事件回调。
    """

    def __init__(self, logger: Any):
        self._logger = logger

    def handle_frame(self, frame: WsFrame, emitter: Any) -> None:
        """
        处理收到的 WebSocket 帧，解析并触发对应的消息/事件

        :param frame: WebSocket 接收帧
        :param emitter: WSClient 实例，用于触发事件
        """
        try:
            body = frame.get("body")

            if not body or not body.get("msgtype"):
                self._logger.warn(
                    f"Received invalid message format: {json.dumps(frame)[:200]}"
                )
                return

            # 事件推送回调处理
            if frame.get("cmd") == WsCmd.EVENT_CALLBACK:
                self._handle_event_callback(frame, emitter)
                return

            # 消息推送回调处理
            self._handle_message_callback(frame, emitter)
        except Exception as e:
            self._logger.error(f"Failed to handle message: {e}")

    def _handle_message_callback(self, frame: WsFrame, emitter: Any) -> None:
        """处理消息推送回调 (aibot_msg_callback)"""
        body = frame.get("body", {})

        # 触发通用消息事件
        emitter.emit("message", frame)

        # 根据 body 中的消息类型触发特定事件
        msgtype = body.get("msgtype", "")

        if msgtype == MessageType.Text:
            emitter.emit("message.text", frame)
        elif msgtype == MessageType.Image:
            emitter.emit("message.image", frame)
        elif msgtype == MessageType.Mixed:
            emitter.emit("message.mixed", frame)
        elif msgtype == MessageType.Voice:
            emitter.emit("message.voice", frame)
        elif msgtype == MessageType.File:
            emitter.emit("message.file", frame)
        else:
            self._logger.debug(f"Received unhandled message type: {msgtype}")

    def _handle_event_callback(self, frame: WsFrame, emitter: Any) -> None:
        """处理事件推送回调 (aibot_event_callback)"""
        body = frame.get("body", {})

        # 触发通用事件
        emitter.emit("event", frame)

        # 根据事件类型触发特定事件
        event = body.get("event", {})
        event_type = event.get("eventtype") if isinstance(event, dict) else None

        if event_type:
            emitter.emit(f"event.{event_type}", frame)
        else:
            self._logger.debug(
                f"Received event callback without eventtype: {json.dumps(body)[:200]}"
            )
