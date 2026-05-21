# -*- coding: utf-8 -*-
# pylint: disable=protected-access

import pytest
from agentscope_runtime.engine.schemas.exception import (
    ConfigurationException,
)

from qwenpaw.app.mcp.manager import MCPClientManager
from qwenpaw.app.mcp.stateful_client import HttpStatefulClient
from qwenpaw.app.routers.mcp import _build_client_info
from qwenpaw.config.config import MCPClientConfig


def _remote_config(**overrides):
    data = {
        "name": "remote-mcp",
        "transport": "streamable_http",
        "url": "https://mcp.example.com/mcp",
    }
    data.update(overrides)
    return MCPClientConfig.model_validate(data)


def test_build_client_passes_remote_timeouts():
    config = _remote_config(timeout=1200.0, sse_read_timeout=900.0)

    client = MCPClientManager._build_client(config)

    assert isinstance(client, HttpStatefulClient)
    assert client.timeout == 1200.0
    assert client.sse_read_timeout == 900.0
    assert client._qwenpaw_rebuild_info["timeout"] == 1200.0
    assert client._qwenpaw_rebuild_info["sse_read_timeout"] == 900.0


def test_build_client_uses_default_remote_timeouts():
    config = _remote_config()

    client = MCPClientManager._build_client(config)

    assert isinstance(client, HttpStatefulClient)
    assert client.timeout == 30.0
    assert client.sse_read_timeout == 300.0


def test_build_client_info_exposes_timeout_fields():
    config = _remote_config(timeout=60.0, sse_read_timeout=120.0)

    info = _build_client_info("remote", config)

    assert info.timeout == 60.0
    assert info.sse_read_timeout == 120.0


@pytest.mark.parametrize("field", ["timeout", "sse_read_timeout"])
def test_remote_timeout_fields_must_be_positive(field):
    with pytest.raises(ConfigurationException):
        _remote_config(**{field: 0})
