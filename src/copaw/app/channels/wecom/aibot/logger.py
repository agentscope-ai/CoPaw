"""
默认日志实现

对标 Node.js SDK src/logger.ts
带有日志级别和时间戳的控制台日志
"""

import sys
from datetime import datetime, timezone


class DefaultLogger:
    """默认日志实现，带有日志级别和时间戳的控制台日志"""

    def __init__(self, prefix: str = "AiBotSDK"):
        self._prefix = prefix

    def _format_time(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def debug(self, message: str, *args: object) -> None:
        print(
            f"[{self._format_time()}] [{self._prefix}] [DEBUG] {message}",
            *args,
            file=sys.stderr,
        )

    def info(self, message: str, *args: object) -> None:
        print(
            f"[{self._format_time()}] [{self._prefix}] [INFO] {message}",
            *args,
            file=sys.stderr,
        )

    def warn(self, message: str, *args: object) -> None:
        print(
            f"[{self._format_time()}] [{self._prefix}] [WARN] {message}",
            *args,
            file=sys.stderr,
        )

    def error(self, message: str, *args: object) -> None:
        print(
            f"[{self._format_time()}] [{self._prefix}] [ERROR] {message}",
            *args,
            file=sys.stderr,
        )
