# -*- coding: utf-8 -*-
"""
Bridge between channels and AgentApp process: factory to build
ProcessHandler from runner. Shared helpers for channels (e.g. file URL).
"""
from __future__ import annotations

import os
from typing import Any, Optional
from urllib.parse import urlparse
from urllib.request import url2pathname


def file_url_to_local_path(url: str) -> Optional[str]:
    """Convert file:// URL to local path. Cross-platform (Windows/Mac/Linux).

    - file:///path (three slashes): path is used as-is after url2pathname.
    - file://D:/path (Windows, two slashes): netloc "D", path "/path" ->
        D:\\path.
    - file://D:\\path (Windows, backslashes): path empty, netloc has full path
      -> use netloc as path so we do not read current dir.
    Returns None if url is not file scheme or resolved path is empty.
    """
    parsed = urlparse(url)
    if parsed.scheme != "file":
        return None
    path = url2pathname(parsed.path)
    if not path and parsed.netloc:
        path = url2pathname(parsed.netloc.replace("\\", "/"))
    elif (
        path and parsed.netloc and len(parsed.netloc) == 1 and os.name == "nt"
    ):
        path = f"{parsed.netloc}:{path}"
    return path if path else None


def make_process_from_runner(runner: Any):
    """
    Use runner.stream_query as the channel's process.

    Each channel does: native -> build_agent_request_from_native()
        -> process(request) -> send on each completed message.
    process is runner.stream_query, same as AgentApp's /process endpoint.

    Usage::
        process = make_process_from_runner(runner)
        manager = ChannelManager.from_env(process)
    """
    return runner.stream_query
