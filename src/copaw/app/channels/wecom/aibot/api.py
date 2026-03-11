"""
企业微信 API 客户端

对标 Node.js SDK src/api.ts
仅负责文件下载等 HTTP 辅助功能，消息收发均走 WebSocket 通道。
"""

import re
import ssl
from typing import Any, Optional, Tuple
from urllib.parse import unquote

import aiohttp

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    # 未安装 certifi 时回退到系统默认证书
    _SSL_CONTEXT = ssl.create_default_context()


class WeComApiClient:
    """企业微信 API 客户端"""

    def __init__(self, logger: Any, timeout: int = 10000):
        self._logger = logger
        self._timeout = aiohttp.ClientTimeout(total=timeout / 1000)

    async def download_file_raw(self, url: str) -> Tuple[bytes, Optional[str]]:
        """
        下载文件（返回原始 bytes 及文件名）

        :param url: 文件下载地址
        :return: (文件数据, 文件名)
        """
        self._logger.info("Downloading file...")

        try:
            connector = aiohttp.TCPConnector(ssl=_SSL_CONTEXT)
            async with aiohttp.ClientSession(timeout=self._timeout, connector=connector) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.read()

                    # 从 Content-Disposition 头中解析文件名
                    content_disposition = response.headers.get("Content-Disposition", "")
                    filename: Optional[str] = None

                    if content_disposition:
                        # 优先匹配 filename*=UTF-8''xxx 格式（RFC 5987）
                        utf8_match = re.search(
                            r"filename\*=UTF-8''([^;\s]+)",
                            content_disposition,
                            re.IGNORECASE,
                        )
                        if utf8_match:
                            filename = unquote(utf8_match.group(1))
                        else:
                            # 匹配 filename="xxx" 或 filename=xxx 格式
                            match = re.search(
                                r'filename="?([^";\s]+)"?',
                                content_disposition,
                                re.IGNORECASE,
                            )
                            if match:
                                filename = unquote(match.group(1))

                    self._logger.info("File downloaded successfully")
                    return data, filename

        except Exception as e:
            self._logger.error("File download failed:", str(e))
            raise
