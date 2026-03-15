# -*- coding: utf-8 -*-
# flake8: noqa: E501
# pylint: disable=line-too-long,too-many-return-statements
import os
import mimetypes
import logging
from typing import Optional

import aiofiles
import httpx

from agentscope.tool import ToolResponse
from agentscope.message import (
    TextBlock,
    ImageBlock,
    AudioBlock,
    VideoBlock,
)

from ..schema import FileBlock
from ...config import load_config

logger = logging.getLogger(__name__)


def _auto_as_type(mt: str) -> str:
    if mt.startswith("image/"):
        return "image"
    if mt.startswith("audio/"):
        return "audio"
    if mt.startswith("video/"):
        return "video"
    return "file"


async def upload_to_fivemanage(image_path: str, api_key: str) -> Optional[str]:
    """Upload image to Fivemanage CDN.

    Args:
        image_path: Path to the image file
        api_key: Fivemanage API key

    Returns:
        Public URL of the uploaded image, or None if upload failed
    """
    try:
        logger.debug(f"[Fivemanage] Starting upload for image: {image_path}")

        async with aiofiles.open(image_path, "rb") as f:
            file_content = await f.read()

        filename = os.path.basename(image_path)
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        logger.debug(
            f"[Fivemanage] File details - filename: {filename}, mime_type: {mime_type}, size: {len(file_content)} bytes",
        )

        async with httpx.AsyncClient() as client:
            logger.debug(
                "[Fivemanage] Sending POST request to https://api.fivemanage.com/api/v3/file",
            )

            response = await client.post(
                "https://api.fivemanage.com/api/v3/file",
                files={"file": (filename, file_content, mime_type)},
                headers={"Authorization": api_key},
                timeout=30,
            )

            logger.debug(
                f"[Fivemanage] Response status: {response.status_code}",
            )
            logger.debug(
                f"[Fivemanage] Response headers: {dict(response.headers)}",
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"[Fivemanage] Response body: {result}")

            # Fivemanage API returns URL nested in data field
            if result.get("data", {}).get("url"):
                uploaded_url = result["data"]["url"]
                logger.info(
                    f"[Fivemanage] Upload successful, URL: {uploaded_url}",
                )
                return uploaded_url
            else:
                logger.warning(
                    "[Fivemanage] Upload response missing 'url' field",
                )
                return None
    except httpx.HTTPStatusError as e:
        logger.error(f"[Fivemanage] HTTP error occurred: {str(e)}")
        logger.error(f"[Fivemanage] Response content: {e.response.text}")
        return None
    except Exception as e:
        logger.error(
            f"[Fivemanage] Upload failed with error: {str(e)}",
            exc_info=True,
        )
        return None


async def send_file_to_user(
    file_path: str,
) -> ToolResponse:
    """Send a file to the user.

    Args:
        file_path (`str`):
            Path to the file to send.

    Returns:
        `ToolResponse`:
            The tool response containing the file or an error message.
    """

    if not os.path.exists(file_path):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: The file {file_path} does not exist.",
                ),
            ],
        )

    if not os.path.isfile(file_path):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: The path {file_path} is not a file.",
                ),
            ],
        )

    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        # Default to application/octet-stream for unknown types
        mime_type = "application/octet-stream"
    as_type = _auto_as_type(mime_type)

    try:
        # Get config
        config = load_config()
        image_upload_provider = config.agents.running.image_upload_provider
        fivemanage_api_key = config.agents.running.fivemanage_api_key

        # Use local file URL instead of base64
        absolute_path = os.path.abspath(file_path)
        file_url = f"file://{absolute_path}"
        source = {"type": "url", "url": file_url}

        # Upload image based on provider configuration
        if as_type == "image" and image_upload_provider != "none":
            try:
                if (
                    image_upload_provider == "fivemanage"
                    and fivemanage_api_key
                ):
                    uploaded_url = await upload_to_fivemanage(
                        absolute_path,
                        fivemanage_api_key,
                    )
                    if uploaded_url:
                        file_url = uploaded_url
                        source = {"type": "url", "url": file_url}
            except Exception:
                # Fallback to local file if upload fails
                pass

        if as_type == "image":
            return ToolResponse(
                content=[
                    ImageBlock(type="image", source=source),
                    TextBlock(type="text", text="已成功发送文件"),
                ],
            )
        if as_type == "audio":
            return ToolResponse(
                content=[
                    AudioBlock(type="audio", source=source),
                    TextBlock(type="text", text="已成功发送文件"),
                ],
            )
        if as_type == "video":
            return ToolResponse(
                content=[
                    VideoBlock(type="video", source=source),
                    TextBlock(type="text", text="已成功发送文件"),
                ],
            )

        return ToolResponse(
            content=[
                FileBlock(
                    type="file",
                    source=source,
                    filename=os.path.basename(file_path),
                ),
                TextBlock(type="text", text="已成功发送文件"),
            ],
        )

    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Send file failed due to \n{e}",
                ),
            ],
        )
