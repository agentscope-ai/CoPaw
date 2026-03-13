# -*- coding: utf-8 -*-
"""Nextcloud WebDAV URL construction utilities."""

# pylint: disable=W0611  # unused-import

from urllib.parse import quote


def build_webdav_url(
    base_url: str,
    api_user: str,
    file_path_or_full: str,
) -> str | None:
    """
    Build a WebDAV download URL for a Nextcloud file.

    Uses the format: {base_url}/remote.php/dav/files/{api_user}/{file_path}
    Following OpenClaw PR #29256 implementation.

    The file_path_or_full parameter contains either:
    - A directory path (e.g., "Talk" or "Photos") when filename is provided separately  # noqa: E501
    - A full path with filename (e.g., "Talk/image.jpg") if no separate filename  # noqa: E501

    Args:
        base_url: Nextcloud base URL (e.g., https://example.com/nextcloud)
        api_user: API username for the bot account
        file_path_or_full: File path (directory or full path with filename)

    Returns:
        WebDAV URL or None if parameters are insufficient

    Example:
        >>> build_webdav_url(
        ...     "https://cloud.example.com/nextcloud",
        ...     "bot-user",
        ...     "Talk/image.jpg"
        ... )
        'https://cloud.example.com/nextcloud/remote.php/dav/files/bot-user/Talk/image.jpg'
    """
    # Normalize base URL
    base_url = base_url.rstrip("/")

    # Check required parameters
    if not base_url or not api_user or not file_path_or_full:
        return None

    # Use file_path_or_full directly (already contains full path)
    # Do NOT append filename again to avoid duplication
    webdav_path = file_path_or_full.lstrip("/")

    # Encode path: split by "/" and encode each segment
    # This ensures spaces and special characters are properly encoded
    encoded_path_segments = [
        quote(segment) for segment in webdav_path.split("/")
    ]
    encoded_path = "/".join(encoded_path_segments)

    # Encode the username
    encoded_user = quote(api_user)

    # Build WebDAV URL
    webdav_url = (
        f"{base_url}/remote.php/dav/files/{encoded_user}/{encoded_path}"
    )

    return webdav_url
