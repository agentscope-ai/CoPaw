# -*- coding: utf-8 -*-
"""Shared helpers used by individual card kinds.

These functions deal with WeCom-specific message plumbing (extracting
metadata / body text from runtime ``Msg`` objects, building routing
context for stateless callbacks, gracefully draining the active
"🤔 Thinking..." stream before sending a card).

They take ``channel`` as an explicit argument instead of being attached
to :class:`~.dispatcher.WecomCardHandler`, so each card module can use
them without reaching into dispatcher internals.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..channel import WecomChannel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Event / message extraction
# ---------------------------------------------------------------------


def extract_meta(event: Any) -> Optional[Dict[str, Any]]:
    """Return the original ``Msg.metadata`` dict or ``None``.

    Tolerates the ``metadata.metadata`` nesting introduced by the
    runtime when re-wrapping events.
    """
    metadata = getattr(event, "metadata", None) or {}
    if not isinstance(metadata, dict):
        return None
    inner = metadata.get("metadata")
    meta = inner if isinstance(inner, dict) else metadata
    return meta if isinstance(meta, dict) else None


def extract_body_text(content: Any) -> str:
    """Flatten a runtime ``Message.content`` into a plain text string.

    ``content`` may be a string, a list of ``TextContent`` objects, or
    a list of ``{"type": "text", "text": "..."}`` dicts.
    """
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for item in content:
        if hasattr(item, "text") and item.text:
            parts.append(item.text)
        elif isinstance(item, dict) and item.get("type") == "text":
            parts.append(item.get("text") or "")
    return "".join(parts)


# ---------------------------------------------------------------------
# Routing context
# ---------------------------------------------------------------------


def build_session_ctx(
    to_handle: str,
    send_meta: Dict[str, Any],
) -> Dict[str, Any]:
    """Collect the routing info needed to re-inject a card callback.

    The returned dict is encoded into the button's ``key`` so the
    inbound handler can recover the original session/sender/chat.
    """
    session_id = ""
    handle = (to_handle or "").strip()
    if handle.startswith("wecom:"):
        session_id = handle

    return {
        "session_id": session_id,
        "sender_id": str(send_meta.get("wecom_sender_id") or ""),
        "chatid": str(send_meta.get("wecom_chatid") or ""),
        "chat_type": str(send_meta.get("wecom_chat_type") or "single"),
    }


# ---------------------------------------------------------------------
# Stream lifecycle
# ---------------------------------------------------------------------


async def send_stream_detail(
    channel: "WecomChannel",
    frame: Any,
    send_meta: Dict[str, Any],
    body_text: str,
) -> None:
    """Stream ``body_text`` to the user, gracefully reusing the active
    "🤔 Thinking..." processing stream when present (so we don't leave
    an empty bubble behind in the chat).

    If the channel attached a ``wecom_processing_stream_id`` to
    ``send_meta``, we cancel its keepalive task and reuse that
    ``stream_id`` to write the final content; otherwise we generate a
    fresh one.
    """
    processing_sid = send_meta.pop(
        "wecom_processing_stream_id", "",
    )
    if processing_sid:
        # Cancel keepalive first so it doesn't race our finish frame.
        keepalive = channel._keepalive_tasks.pop(  # noqa: SLF001
            processing_sid, None,
        )
        if keepalive and not keepalive.done():
            keepalive.cancel()
            try:
                await keepalive
            except (asyncio.CancelledError, Exception):
                pass

    from aibot import generate_req_id

    stream_id = processing_sid or generate_req_id("stream")
    try:
        await channel._client.reply_stream(  # noqa: SLF001
            frame,
            stream_id=stream_id,
            content=body_text,
            finish=True,
        )
    except Exception:
        logger.debug("wecom card: stream detail send failed")


__all__ = [
    "extract_meta",
    "extract_body_text",
    "build_session_ctx",
    "send_stream_detail",
]
