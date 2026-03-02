# -*- coding: utf-8 -*-
"""Message processing utilities for agent communication.

This module handles:
- File and media block processing
- Message content manipulation
- Message validation
"""
import base64
import logging
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from agentscope.message import Msg

from ...constant import MAX_BASE64_FILE_SIZE, WORKING_DIR
from ...providers import get_active_llm_config
from .file_handling import download_file_from_base64, download_file_from_url

logger = logging.getLogger(__name__)

# Only allow local paths under this dir (channels save media here).
_ALLOWED_MEDIA_ROOT = WORKING_DIR / "media"


def _local_path_to_data_url(local_path: str) -> Optional[str]:
    """Convert local file path to data URL with base64 encoding.

    Returns None if the file doesn't exist, is too large, or can't be read.
    """
    try:
        if not os.path.isfile(local_path):
            return None

        # Check file size before reading
        file_size = os.path.getsize(local_path)
        if file_size > MAX_BASE64_FILE_SIZE:
            logger.warning(
                "File %s exceeds max size for base64 conversion: %s > %s",
                local_path,
                file_size,
                MAX_BASE64_FILE_SIZE,
            )
            return None

        with open(local_path, "rb") as f:
            data = f.read()

        # Determine media type from extension
        ext = os.path.splitext(local_path)[1].lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        media_type = mime_types.get(ext, "application/octet-stream")

        return (
            f"data:{media_type};base64,"
            f"{base64.b64encode(data).decode('utf-8')}"
        )
    except Exception as e:
        logger.warning(
            "Failed to convert local file to data URL: %s: %s",
            local_path,
            e,
        )
        return None


def _is_allowed_media_path(path: str) -> bool:
    """True if path is a file under _ALLOWED_MEDIA_ROOT."""
    try:
        resolved = Path(path).expanduser().resolve()
        root = _ALLOWED_MEDIA_ROOT.resolve()
        return resolved.is_file() and str(resolved).startswith(str(root))
    except Exception:
        return False


async def _process_single_file_block(
    source: dict,
    filename: Optional[str],
) -> Optional[str]:
    """
    Process a single file block and download the file.

    Args:
        source: The source dict containing file information.
        filename: The filename to save.

    Returns:
        The local file path if successful, None otherwise.
    """
    if not isinstance(source, dict):
        return None

    result = None
    source_type = source.get("type")

    if source_type == "base64":
        if "data" not in source:
            return None
        base64_data = source.get("data", "")
        result = await download_file_from_base64(
            base64_data,
            filename,
        )
        logger.debug(
            "Processed base64 file block: %s -> %s",
            filename or "unnamed",
            result,
        )

    elif source_type == "url":
        url = source.get("url", "")
        if not url:
            return None

        parsed = urllib.parse.urlparse(url)
        if parsed.scheme == "file":
            result = _process_file_url(parsed)
            logger.debug(
                "Processed URL file block: %s -> %s",
                url,
                result,
            )
        else:
            result = await download_file_from_url(
                url,
                filename,
            )
            logger.debug(
                "Processed URL file block: %s -> %s",
                url,
                result,
            )

    return result


def _process_file_url(parsed: urllib.parse.ParseResult) -> Optional[str]:
    try:
        # On Windows, file URLs with drive letters have the path in netloc
        # For Unix-style URLs, use parsed.path directly.
        if parsed.netloc in ("", "localhost"):
            file_path = parsed.path
        else:
            # Convert Windows drive letter format
            file_path = parsed.netloc + parsed.path
            if "|" in file_path:
                file_path = file_path.replace("|", ":", 1)
        # Use urllib to properly decode URL-encoded characters
        # but don't use url2pathname as it converts / to \
        local_path = urllib.parse.unquote(file_path)
        if not _is_allowed_media_path(local_path):
            logger.warning(
                "Rejected file:// URL outside allowed media dir",
            )
            return None
        return local_path
    except Exception:
        return None


def _extract_source_and_filename(block: dict, block_type: str):
    """Extract source and filename from a block."""
    if block_type == "file":
        return block.get("source", {}), block.get("filename")

    source = block.get("source", {})
    if not isinstance(source, dict):
        return None, None

    filename = None
    if source.get("type") == "url":
        url = source.get("url", "")
        if url:
            parsed = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed.path) or None

    return source, filename


def _media_type_from_path(path: str) -> str:
    """Infer media type from file path suffix."""
    ext = (os.path.splitext(path)[1] or "").lower()

    # Image types
    image_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    if ext in image_types:
        return image_types[ext]

    # Video types
    video_types = {
        ".mp4": "video/mp4",
        ".avi": "video/avi",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
    }
    if ext in video_types:
        return video_types[ext]

    # Audio types
    audio_types = {
        ".amr": "audio/amr",
        ".wav": "audio/wav",
        ".mp3": "audio/mp3",
        ".opus": "audio/opus",
    }
    if ext in audio_types:
        return audio_types[ext]

    return "application/octet-stream"


def _update_block_with_local_path(
    block: dict,
    block_type: str,
    local_path: str,
) -> dict:
    """Update block with downloaded local path.

    For images and videos: if vision_supported is True in config, convert to
    base64 data URL; otherwise keep as file:// URL.
    """
    if block_type == "file":
        block["source"] = local_path
        if not block.get("filename"):
            block["filename"] = os.path.basename(local_path)
    elif block_type in ("image", "video"):
        # Check if vision is supported by the active model
        model_config = get_active_llm_config()
        vision_supported = (
            model_config.vision_supported if model_config else True
        )

        if vision_supported:
            # Convert to base64 for vision models
            data_url = _local_path_to_data_url(local_path)
            if data_url:
                block["source"] = {
                    "type": "base64",
                    "data": data_url.split(",", 1)[1],
                    "media_type": _media_type_from_path(local_path),
                }
            else:
                logger.warning(
                    "Failed to convert %s to base64: %s",
                    block_type,
                    local_path,
                )
                # Fallback to file:// URL
                block["source"] = {
                    "type": "url",
                    "url": Path(local_path).as_uri(),
                }
        else:
            # Keep as file:// URL for non-vision models
            block["source"] = {
                "type": "url",
                "url": Path(local_path).as_uri(),
            }
    elif block_type == "audio":
        block["source"] = {
            "type": "url",
            "url": Path(local_path).as_uri(),
            "media_type": _media_type_from_path(local_path),
        }
    else:
        block["source"] = {
            "type": "url",
            "url": Path(local_path).as_uri(),
        }
    return block


def _handle_download_failure(block_type: str) -> Optional[dict]:
    """Handle download failure based on block type."""
    if block_type == "file":
        return {
            "type": "text",
            "text": "[Error: Unknown file source type or empty data]",
        }
    logger.debug("Failed to download %s block, keeping original", block_type)
    return None


async def _process_single_block(
    message_content: list,
    index: int,
    block: dict,
) -> Optional[str]:
    """
    Process a single file or media block.

    Returns:
        Optional[str]: The local path if download was successful,
        None otherwise.
    """
    block_type = block.get("type")
    if not isinstance(block_type, str):
        return None

    source, filename = _extract_source_and_filename(block, block_type)
    if source is None:
        return None

    # Normalize: when source is "base64" but data is a local path (e.g.
    # DingTalk voice returns path), treat as url only if under allowed dir.
    if (
        block_type == "audio"
        and isinstance(source, dict)
        and source.get("type") == "base64"
    ):
        data = source.get("data")
        if (
            isinstance(data, str)
            and os.path.isfile(data)
            and _is_allowed_media_path(data)
        ):
            block["source"] = {
                "type": "url",
                "url": Path(data).as_uri(),
                "media_type": _media_type_from_path(data),
            }
            source = block["source"]

    try:
        local_path = await _process_single_file_block(source, filename)

        if local_path:
            message_content[index] = _update_block_with_local_path(
                block,
                block_type,
                local_path,
            )
            logger.debug(
                "Updated %s block with local path: %s",
                block_type,
                local_path,
            )
            return local_path
        else:
            error_block = _handle_download_failure(block_type)
            if error_block:
                message_content[index] = error_block
            return None

    except Exception as e:
        logger.error("Failed to process %s block: %s", block_type, e)
        if block_type == "file":
            message_content[index] = {
                "type": "text",
                "text": f"[Error: Failed to download file - {e}]",
            }
        return None


async def process_file_and_media_blocks_in_message(msg) -> None:
    """
    Process file and media blocks (file, image, audio, video) in messages.
    Downloads to local and updates paths/URLs.

    Args:
        msg: The message object (Msg or list[Msg]) to process.
    """
    messages = (
        [msg] if isinstance(msg, Msg) else msg if isinstance(msg, list) else []
    )

    for message in messages:
        if not isinstance(message, Msg):
            continue

        if not isinstance(message.content, list):
            continue

        downloaded_files = []

        for i, block in enumerate(message.content):
            if not isinstance(block, dict):
                continue

            block_type = block.get("type")
            if block_type not in ["file", "image", "audio", "video"]:
                continue

            local_path = await _process_single_block(message.content, i, block)
            if local_path:
                downloaded_files.append((i, local_path, block_type))

        # Only add text description for non-media files (not image/video/audio)
        for i, local_path, block_type in reversed(downloaded_files):
            if block_type == "file":
                text_block = {
                    "type": "text",
                    "text": f"用户上传文件，已经下载到 {local_path}",
                }
                message.content.insert(i + 1, text_block)
            # For image/video/audio: keep the block as-is


def is_first_user_interaction(messages: list) -> bool:
    """Check if this is the first user interaction.

    Args:
        messages: List of Msg objects from memory.

    Returns:
        bool: True if this is the first user message with no assistant
              responses.
    """
    system_prompt_count = sum(1 for msg in messages if msg.role == "system")
    non_system_messages = messages[system_prompt_count:]

    user_msg_count = sum(
        1 for msg in non_system_messages if msg.role == "user"
    )
    assistant_msg_count = sum(
        1 for msg in non_system_messages if msg.role == "assistant"
    )

    return user_msg_count == 1 and assistant_msg_count == 0


def prepend_to_message_content(msg, guidance: str) -> None:
    """Prepend guidance text to message content.

    Args:
        msg: Msg object to modify.
        guidance: Text to prepend to the message content.
    """
    if isinstance(msg.content, str):
        msg.content = guidance + "\n\n" + msg.content
        return

    if not isinstance(msg.content, list):
        return

    for block in msg.content:
        if isinstance(block, dict) and block.get("type") == "text":
            block["text"] = guidance + "\n\n" + block.get("text", "")
            return

    msg.content.insert(0, {"type": "text", "text": guidance})
