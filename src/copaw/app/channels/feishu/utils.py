# -*- coding: utf-8 -*-
"""Feishu channel pure helpers (session id, sender display, markdown)."""

import json
import re
from typing import Optional

from .constants import FEISHU_SESSION_ID_SUFFIX_LEN


def short_session_id_from_full_id(full_id: str) -> str:
    """Use last N chars of full_id (chat_id or open_id) as session_id."""
    n = FEISHU_SESSION_ID_SUFFIX_LEN
    return full_id[-n:] if len(full_id) >= n else full_id


def sender_display_string(
    nickname: Optional[str],
    sender_id: str,
) -> str:
    """Build sender display as nickname#last4(sender_id), like DingTalk."""
    nick = (nickname or "").strip() if isinstance(nickname, str) else ""
    sid = (sender_id or "").strip()
    suffix = sid[-4:] if len(sid) >= 4 else (sid or "????")
    return f"{(nick or 'unknown')}#{suffix}"


def extract_json_key(content: Optional[str], *keys: str) -> Optional[str]:
    """Parse JSON content and return first present key."""
    if not content:
        return None
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    for k in keys:
        v = data.get(k) or data.get(k.replace("_", "").lower())
        if v:
            return str(v).strip()
    return None


def extract_post_text(content: Optional[str]) -> Optional[str]:
    # pylint: disable=too-many-branches
    """Extract plain text from Feishu post message content."""
    if not content:
        return None
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    parts: list[str] = []

    # Extract title if present
    title = data.get("title")
    if title and isinstance(title, str) and title.strip():
        parts.append(title.strip())

    # Extract text from content blocks
    content_blocks = data.get("content") or []
    if isinstance(content_blocks, list):
        for block in content_blocks:
            if not isinstance(block, list):
                continue
            for item in block:
                if not isinstance(item, dict):
                    continue
                tag = item.get("tag")
                # text, code_block, md tags have text field
                if tag in {"text", "code_block", "md"}:
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
                # a tag: text + href as markdown link
                elif tag == "a":
                    text = item.get("text", "")
                    href = item.get("href", "")
                    if href:
                        parts.append(f"[{text}]({href})" if text else href)
                    elif text:
                        parts.append(text.strip())
                # at tag uses user_name
                elif tag == "at":
                    user_name = item.get("user_name") or item.get("user_id")
                    if isinstance(user_name, str) and user_name.strip():
                        parts.append(f"@{user_name.strip()}")

    return " ".join(parts) if parts else None


def extract_post_image_keys(content: Optional[str]) -> list[str]:
    """Extract image_key list from Feishu post message content."""
    if not content:
        return []
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, dict):
        return []

    keys: list[str] = []
    content_blocks = data.get("content") or []
    if isinstance(content_blocks, list):
        for block in content_blocks:
            if not isinstance(block, list):
                continue
            for item in block:
                if not isinstance(item, dict):
                    continue
                if item.get("tag") == "img":
                    key = item.get("image_key")
                    if isinstance(key, str) and key.strip():
                        keys.append(key.strip())

    return keys


def normalize_feishu_md(text: str) -> str:
    """
    Light markdown normalization for Feishu post (avoid broken rendering).
    """
    if not text or not text.strip():
        return text
    # Ensure newline before code fence so Feishu parses it
    text = re.sub(r"([^\n])(```)", r"\1\n\2", text)
    return text
