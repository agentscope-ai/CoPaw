# -*- coding: utf-8 -*-
"""DingTalk content parsing and session helpers."""

from __future__ import annotations

import base64
import binascii
import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from agentscope_runtime.engine.schemas.agent_schemas import (
    # AudioContent,
    FileContent,
    ImageContent,
    VideoContent,
)

from ..base import ContentType

from .constants import (
    DINGTALK_SESSION_ID_SUFFIX_LEN,
    DINGTALK_TYPE_MAPPING,
)

logger = logging.getLogger(__name__)


_DATA_URL_RE = re.compile(
    r"^data:(?P<mime>[^;]+);base64,(?P<b64>.*)$",
    re.I | re.S,
)


def dingtalk_content_from_type(mapped: str, url: str) -> Any:
    """Build runtime Content from DingTalk type and download URL."""
    if mapped == "image":
        return ImageContent(type=ContentType.IMAGE, image_url=url)
    if mapped == "video":
        return VideoContent(type=ContentType.VIDEO, video_url=url)
    if mapped == "audio":
        # Use subtype only: runtime prefixes with "audio/" -> "audio/amr".
        # TODO: change to audio block when as support amr
        return FileContent(
            type=ContentType.FILE,
            file_url=url,
            # data=url,
            # format="amr",
        )
    return FileContent(type=ContentType.FILE, file_url=url)


def parse_data_url(data_url: str) -> tuple[bytes, Optional[str]]:
    """Return (bytes, mime or None)."""
    m = _DATA_URL_RE.match(data_url.strip())
    if not m:
        return base64.b64decode(data_url, validate=False), None

    mime = (m.group("mime") or "").strip().lower()
    b64 = m.group("b64").strip()
    try:
        data = base64.b64decode(b64, validate=False)
    except (binascii.Error, ValueError):
        data = base64.b64decode(b64 + "==", validate=False)
    return data, mime or None


def sender_from_chatbot_message(incoming_message: Any) -> tuple[str, bool]:
    """Build sender as nickname#last4(sender_id).
    Return (sender, should_skip).
    """
    nickname = (
        getattr(incoming_message, "sender_nick", None)
        or getattr(incoming_message, "senderNick", None)
        or ""
    )
    nickname = nickname.strip() if isinstance(nickname, str) else ""
    sender_id = (
        getattr(incoming_message, "sender_id", None)
        or getattr(incoming_message, "senderId", None)
        or ""
    )
    sender_id = str(sender_id).strip() if sender_id else ""
    suffix = sender_id[-4:] if len(sender_id) >= 4 else (sender_id or "????")
    sender = f"{(nickname or 'unknown')}#{suffix}"
    skip = not suffix and not nickname
    return sender, skip


def conversation_id_from_chatbot_message(incoming_message: Any) -> str:
    """Extract conversation_id from DingTalk ChatbotMessage."""
    cid = getattr(incoming_message, "conversationId", None) or getattr(
        incoming_message,
        "conversation_id",
        None,
    )
    return str(cid).strip() if cid else ""


def short_session_id_from_conversation_id(conversation_id: str) -> str:
    """Use last N chars of conversation_id as session_id."""
    n = DINGTALK_SESSION_ID_SUFFIX_LEN
    return (
        conversation_id[-n:] if len(conversation_id) >= n else conversation_id
    )


def session_param_from_webhook_url(url: str) -> Optional[str]:
    """Extract session= param from sendBySession URL for debug logging."""
    if not url or "?" not in url:
        return None
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    vals = qs.get("session", [])
    return (
        vals[0][:24] + "..."
        if vals and len(vals[0]) > 24
        else (vals[0] if vals else None)
    )


def get_type_mapping() -> dict:
    """Return DingTalk type mapping (for handler use)."""
    return dict(DINGTALK_TYPE_MAPPING)


def get_user_id_from_meta(meta: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract user_id from meta for DingTalk OpenAPI sending.

    For DingTalk OpenAPI, we need senderStaffId (not senderId).
    senderStaffId is the actual staff ID like 'maabnr2134'.

    The value is retrieved from meta['sender_staff_id'], which is set by
    the handler from the incoming message's callback data.

    Returns:
        The senderStaffId string if available, None otherwise.
    """
    logger.debug(
        "dingtalk get_user_id_from_meta: meta keys=%s",
        list(meta.keys()) if meta else [],
    )
    if not meta:
        return None
    staff_id = meta.get("sender_staff_id")
    if staff_id:
        logger.debug(
            "dingtalk get_user_id_from_meta: using sender_staff_id from meta",
        )
        return str(staff_id).strip()
    return None


def get_chat_type_from_meta(
    meta: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Determine chat type (direct/group) from meta for OpenAPI sending.

    Returns 'direct' for single chat, 'group' for group chat, None if unknown.

    The conversation type is retrieved from meta['conversation_type'],
    which is set by the handler from the incoming message's callback data.
    ConversationType '2' means group chat, anything else means direct chat.

    Returns:
        'direct' for single chat, 'group' for group chat, None if unknown.
    """
    logger.debug(
        "dingtalk get_chat_type_from_meta: meta keys=%s",
        list(meta.keys()) if meta else [],
    )
    if not meta:
        return None
    conv_type = meta.get("conversation_type")
    if conv_type is not None:
        logger.debug(
            "dingtalk: using conversation_type from meta",
        )
        if str(conv_type) == "2":
            return "group"
        else:
            return "direct"
    return None


def get_msg_key_for_media_type(media_type: str) -> str:
    """Get msgKey for DingTalk OpenAPI based on media type."""
    logger.debug(
        "dingtalk get_msg_key_for_media_type: media_type=%s",
        media_type,
    )
    mapping = {
        "image": "sampleImageMsg",
        "voice": "sampleAudio",
        "video": "sampleVideo",
        "file": "sampleFile",
    }
    return mapping.get(media_type, "sampleFile")
