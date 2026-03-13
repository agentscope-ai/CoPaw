# -*- coding: utf-8 -*-
"""Nextcloud Files API client for accessing shared files."""

# pylint: disable=C0301  # line-too-long
# pylint: disable=W0621  # redefined-outer-name
# pylint: disable=W0404  # reimported
# pylint: disable=R0912  # too-many-branches
# pylint: disable=R0915  # too-many-statements
# pylint: disable=W0611  # unused-import

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import quote

import aiohttp

logger = logging.getLogger(__name__)


class NextcloudFilesClient:
    """
    Client for Nextcloud Files API (WebDAV).

    Used to access file metadata and download links for files shared in Talk.
    """

    def __init__(self, base_url: str, username: str = "", password: str = ""):
        """
        Initialize Nextcloud Files client.

        Args:
            base_url: Base URL of Nextcloud server (e.g., https://example.com/nextcloud)  # noqa: E501
            username: Username for authentication (optional for public shares)
            password: Password or app token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None

        # Load credentials from config if not provided
        if not username or not password:
            self._load_credentials_from_config()

    def _load_credentials_from_config(self):
        """Load Nextcloud credentials from config file."""
        try:
            import json
            from pathlib import Path

            config_path = Path.home() / ".copaw" / "config.json"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                nc_config = config.get("channels", {}).get(
                    "nextcloud_talk",
                    {},
                )
                if nc_config:
                    self.username = nc_config.get("username", "")
                    self.password = nc_config.get("password", "")

                    if self.username and self.password:
                        logger.info(
                            f"Loaded Nextcloud credentials from config: username={self.username[:3]}...",  # noqa: E501
                        )
                    else:
                        logger.warning(
                            "Nextcloud credentials not found in config",
                        )
            else:
                logger.warning(f"Config file not found: {config_path}")

        except Exception as e:
            logger.error(
                f"Failed to load Nextcloud credentials from config: {e}",
            )

    def build_webdav_url(self, api_user: str, file_path: str) -> Optional[str]:
        """
        Build a WebDAV download URL for a Nextcloud file.

        Uses the format: {base_url}/remote.php/dav/files/{api_user}/{file_path}
        Following OpenClaw PR #29256 implementation.

        Args:
            api_user: API username for the bot account
            file_path: File path relative to user's files root (e.g., Talk/image.jpg)  # noqa: E501

        Returns:
            WebDAV URL or None if parameters are insufficient

        Example:
            >>> client.build_webdav_url("bot-user", "Talk/image.jpg")
            'https://cloud.example.com/nextcloud/remote.php/dav/files/bot-user/Talk/image.jpg'
        """
        if not self.base_url or not api_user or not file_path:
            return None

        # Normalize base URL
        base_url = self.base_url.rstrip("/")

        # Encode file path: split by "/" and encode each segment
        # This ensures spaces and special characters are properly encoded
        encoded_path_segments = [
            quote(segment) for segment in file_path.split("/")
        ]
        encoded_path = "/".join(encoded_path_segments)

        # Encode the username
        encoded_user = quote(api_user)

        # Build WebDAV URL
        webdav_url = (
            f"{base_url}/remote.php/dav/files/{encoded_user}/{encoded_path}"
        )

        return webdav_url

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None:
            logger.info(
                f"Creating session with username='{self.username}', password present={bool(self.password)})",  # noqa: E501
            )

            # Debug environment variables
            env_username = os.environ.get("NEXTCLOUD_USERNAME", "NOT_SET")
            env_password = os.environ.get("NEXTCLOUD_PASSWORD", "NOT_SET")
            logger.info(
                f"Environment vars: NEXTCLOUD_USERNAME={env_username[:3]}..., NEXTCLOUD_PASSWORD={'SET' if env_password != 'NOT_SET' else 'NOT_SET'})",  # noqa: E501
            )

            auth = (
                aiohttp.BasicAuth(self.username, self.password)
                if self.username
                else None
            )
            if auth:
                logger.info(
                    f"Created BasicAuth with username: {self.username[:3]}...",
                )
            else:
                logger.warning("No authentication credentials provided")

            self._session = aiohttp.ClientSession(auth=auth)
        return self._session

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information via WebDAV PROPFIND request.

        Args:
            file_path: Path to file relative to user's files root

        Returns:
            File information dict or None
        """
        try:
            session = await self.get_session()

            # Build WebDAV URL
            dav_url = f"{self.base_url}/remote.php/dav/files/{quote(file_path.lstrip('/'))}"  # noqa: E501

            # PROPFIND request to get file properties
            propfind_body = """<?xml version="1.0"?>
            <d:propfind xmlns:d="DAV:" xmlns:nc="http://nextcloud.org/ns" xmlns:oc="http://owncloud.org/ns">  # noqa: E501
                <d:prop>
                    <d:getlastmodified/>
                    <d:getcontentlength/>
                    <d:getcontenttype/>
                    <d:resourcetype/>
                    <oc:id/>
                    <oc:owner-id/>
                    <oc:owner-display-name/>
                    <nc:has-preview/>
                </d:prop>
            </d:propfind>"""

            headers = {
                "Depth": "0",
                "Content-Type": "application/xml",
            }

            async with session.propfind(
                dav_url,
                data=propfind_body,
                headers=headers,
            ) as resp:
                if resp.status == 207:  # Multi-Status
                    await resp.text()  # consume response
                    # Parse XML response (simplified)
                    logger.debug(f"Got file info for {file_path}")
                    return {
                        "path": file_path,
                        "success": True,
                    }
                else:
                    logger.warning(f"Failed to get file info: {resp.status}")
                    return None

        except Exception as e:
            logger.exception(f"Error getting file info: {e}")
            return None

    async def get_file_download_url(self, file_path: str) -> Optional[str]:
        """
        Get direct download URL for a file.

        Args:
            file_path: Path to file relative to user's files root

        Returns:
            Download URL or None
        """
        try:
            # For authenticated access, use WebDAV endpoint
            download_url = f"{self.base_url}/remote.php/dav/files/{quote(file_path.lstrip('/'))}"  # noqa: E501
            logger.debug(f"Generated download URL for {file_path}")
            return download_url

        except Exception as e:
            logger.exception(f"Error generating download URL: {e}")
            return None

    async def get_file_preview_url(
        self,
        file_path: str,
        max_width: int = 384,
        max_height: int = 384,
    ) -> Optional[str]:
        """
        Get preview image URL for a file (if available).

        Args:
            file_path: Path to file
            max_width: Maximum preview width
            max_height: Maximum preview height

        Returns:
            Preview URL or None
        """
        try:
            # Use Nextcloud preview endpoint
            preview_url = (
                f"{self.base_url}/index.php/core/preview.png?"
                f"file={quote(file_path)}&"
                f"x={max_width}&y={max_height}&a=1"
            )
            logger.debug(f"Generated preview URL for {file_path}")
            return preview_url

        except Exception as e:
            logger.exception(f"Error generating preview URL: {e}")
            return None

    async def get_public_share_link(
        self,
        share_token: str,
        path: str = "",
    ) -> Optional[str]:
        """
        Get public share link for a file.

        Args:
            share_token: Share token (from file_shared event parameters)
            path: Optional path within the share

        Returns:
            Public share URL or None
        """
        try:
            if path:
                share_url = f"{self.base_url}/index.php/s/{share_token}/files?path={quote(path)}"  # noqa: E501
            else:
                share_url = f"{self.base_url}/index.php/s/{share_token}"

            logger.debug(f"Generated share link: {share_url}")
            return share_url

        except Exception as e:
            logger.exception(f"Error generating share link: {e}")
            return None

    async def download_file(self, url: str, local_path: str) -> bool:
        """
        Download file from URL to local path, handling Nextcloud authentication.  # noqa: E501

        For Nextcloud share URLs (/s/...) and WebDAV URLs, this method uses
        Basic Auth if credentials are available.

        Args:
            url: URL to download from
            local_path: Local file path to save to

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            f"NextcloudFilesClient.download_file: url={url[:50]}..., local_path={local_path}",  # noqa: E501
        )

        try:
            session = await self.get_session()

            logger.info(
                f"Downloading file from Nextcloud: url={url} -> {local_path}",
            )

            # Check if this is a Nextcloud URL that needs auth
            is_share_url = "/s/" in url
            is_webdav_url = "/remote.php/dav/files/" in url
            needs_auth = (
                (is_share_url or is_webdav_url)
                and self.username
                and self.password
            )

            logger.info(
                f"Nextcloud download auth: is_share={is_share_url}, is_webdav={is_webdav_url}, needs_auth={needs_auth}, username={self.username[:2]}...",  # noqa: E501
            )

            # Prepare headers - DON'T add Authorization header when session already has auth  # noqa: E501
            headers = {}
            # For share URLs, we need to add Authorization header manually
            # But for WebDAV URLs, the session already has BasicAuth configured
            if needs_auth and is_share_url:
                import base64

                credentials = f"{self.username}:{self.password}"
                encoded_credentials = base64.b64encode(
                    credentials.encode("utf-8"),
                ).decode("ascii")
                headers["Authorization"] = f"Basic {encoded_credentials}"
                logger.info(
                    "Added Authorization header for share URL download",
                )
            elif needs_auth and is_webdav_url:
                logger.info("Using session BasicAuth for WebDAV URL download")

            # Download with aiohttp (using the authenticated session)
            timeout = aiohttp.ClientTimeout(total=60)
            logger.info(f"Making authenticated request to: {url}")
            logger.info(
                f"Using session auth: username={self.username[:3]}..., password present={bool(self.password)})",  # noqa: E501
            )

            async with session.get(
                url,
                headers=headers,
                timeout=timeout,
            ) as resp:
                logger.info(f"Response status: {resp.status}")
                logger.info(f"Response headers: {dict(resp.headers)}")

                if resp.status != 200:
                    resp_text = await resp.text()
                    logger.error(
                        f"Failed to download file: status={resp.status}, resp={resp_text[:500]}",  # noqa: E501
                    )

                    # Log more details for debugging
                    if resp.status == 401:
                        logger.error(
                            "401 Unauthorized - Authentication failed",
                        )
                    elif resp.status == 404:
                        logger.error("404 Not Found - File not found")
                    elif resp.status == 403:
                        logger.error("403 Forbidden - Access denied")

                    return False

                # Verify content is not HTML (login page)
                content = await resp.read()
                logger.info(f"Downloaded content size: {len(content)} bytes")

                # Detailed content analysis
                if content.startswith(b"<!DOCTYPE") or content.startswith(
                    b"<html",
                ):
                    logger.error(
                        f"Downloaded content is HTML (login page), not binary file: url={url}",  # noqa: E501
                    )
                    logger.error(
                        f"First 500 bytes of content: {content[:500]}",
                    )
                    return False

                # Check for XML error responses
                if content.startswith(b"<?xml"):
                    logger.error(
                        f"Downloaded content is XML (likely error response): url={url}",  # noqa: E501
                    )
                    logger.error(
                        f"First 500 bytes of XML content: {content[:500]}",
                    )
                    return False

                # Validate image file signatures
                if url.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".webp"),
                ):
                    # PNG signature: \x89PNG
                    # JPEG signature: \xff\xd8\xff
                    # GIF signature: GIF87a or GIF89a
                    png_sig = b"\x89PNG\r\n\x1a\n"
                    jpg_sig = b"\xff\xd8\xff"
                    gif_sig = b"GIF8"
                    webp_sig = b"RIFF"

                    valid_image = (
                        content.startswith(png_sig)
                        or content.startswith(jpg_sig)
                        or content.startswith(gif_sig)
                        or content.startswith(webp_sig)
                    )

                    if not valid_image:
                        logger.error(
                            f"Downloaded content doesn't match expected image format: url={url}",  # noqa: E501
                        )
                        logger.error(f"Content starts with: {content[:20]}")
                        logger.error("Expected image signatures not found")
                        return False
                    else:
                        logger.info(
                            f"Valid image file signature confirmed for: {url}",
                        )

                # Check content type
                content_type = resp.headers.get("content-type", "unknown")
                logger.info(f"Content-Type: {content_type}")

                # Additional validation for image files
                if "image" in content_type.lower():
                    logger.info(
                        f"Confirmed image content type: {content_type}",
                    )

                # Save to file
                local_path_obj = Path(local_path)
                local_path_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path_obj, "wb") as f:
                    f.write(content)

                logger.info(
                    f"Successfully downloaded file to {local_path} ({len(content)} bytes)",  # noqa: E501
                )
                return True

        except Exception as e:
            logger.exception(f"Error downloading file from Nextcloud: {e}")
            return False

    async def download_file_via_webdav(
        self,
        api_user: str,
        file_path: str,
        local_path: str,
    ) -> bool:
        """
        Download file using WebDAV URL with authentication.

        This follows the OpenClaw PR #29256 implementation, using:
        {base_url}/remote.php/dav/files/{api_user}/{file_path}

        Args:
            api_user: API username for the bot account
            file_path: File path relative to user's files root
            local_path: Local file path to save to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build WebDAV URL
            webdav_url = self.build_webdav_url(api_user, file_path)
            if not webdav_url:
                logger.error("Failed to build WebDAV URL")
                return False

            logger.info(
                f"Downloading via WebDAV: {webdav_url} -> {local_path}",
            )

            # Get session with authenticated Basic Auth
            session = await self.get_session()

            # Download file
            timeout = aiohttp.ClientTimeout(total=60)
            logger.info(f"WebDAV request to: {webdav_url}")
            logger.info(
                f"Using session with auth: username={self.username[:2]}... password={'*' * len(self.password) if self.password else 'None'}",  # noqa: E501
            )

            async with session.get(webdav_url, timeout=timeout) as resp:
                logger.info(f"WebDAV Response status: {resp.status}")
                logger.info(f"WebDAV Response headers: {dict(resp.headers)}")

                if resp.status != 200:
                    resp_text = await resp.text()
                    logger.error(
                        f"WebDAV download failed: status={resp.status}, url={webdav_url}, resp={resp_text[:500]}",  # noqa: E501
                    )

                    # More detailed error logging
                    if resp.status == 401:
                        logger.error(
                            "WebDAV 401 Unauthorized - Check username/password",  # noqa: E501
                        )
                    elif resp.status == 404:
                        logger.error(
                            "WebDAV 404 Not Found - File path may be incorrect",  # noqa: E501
                        )
                    elif resp.status == 403:
                        logger.error(
                            "WebDAV 403 Forbidden - Insufficient permissions",
                        )

                    return False

                # Read content
                content = await resp.read()
                logger.info(
                    f"WebDAV downloaded content size: {len(content)} bytes",
                )

                # Verify content is not HTML (shouldn't happen with WebDAV)
                if content.startswith(b"<!DOCTYPE") or content.startswith(
                    b"<html",
                ):
                    logger.error(
                        f"WebDAV downloaded content is HTML (unexpected): url={webdav_url}",  # noqa: E501
                    )
                    logger.error(f"First 200 bytes: {content[:200]}")
                    return False

                # Check content type
                content_type = resp.headers.get("content-type", "unknown")
                logger.info(f"WebDAV Content-Type: {content_type}")

                # Save to file
                local_path_obj = Path(local_path)
                local_path_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path_obj, "wb") as f:
                    f.write(content)

                logger.info(
                    f"Successfully downloaded via WebDAV: {local_path} ({len(content)} bytes)",  # noqa: E501
                )
                return True

        except Exception as e:
            logger.exception(f"Error downloading file via WebDAV: {e}")
            return False


async def create_nextcloud_files_client(
    backend_url: str,
    username: str = "",
    password: str = "",
) -> NextcloudFilesClient:
    """
    Create a Nextcloud Files client instance.

    Args:
        backend_url: Nextcloud backend URL
        username: Optional username
        password: Optional password/token

    Returns:
        NextcloudFilesClient instance
    """
    return NextcloudFilesClient(backend_url, username, password)
