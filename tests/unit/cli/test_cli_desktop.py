# -*- coding: utf-8 -*-
from __future__ import annotations

import socket

from qwenpaw.cli.desktop_cmd import (
    _connect_host_for_bind_host,
    _wait_for_http,
)


def test_connect_host_for_bind_host_uses_loopback_for_any_addr() -> None:
    assert _connect_host_for_bind_host("0.0.0.0") == "127.0.0.1"
    assert _connect_host_for_bind_host("127.0.0.1") == "127.0.0.1"


def test_wait_for_http_reaches_server_bound_to_any_addr() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("0.0.0.0", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        assert _wait_for_http("0.0.0.0", port, timeout_sec=1.0)
