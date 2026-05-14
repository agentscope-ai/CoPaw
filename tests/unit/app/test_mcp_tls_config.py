# -*- coding: utf-8 -*-
"""Tests for MCP remote TLS verification configuration."""

from __future__ import annotations

import httpx

from qwenpaw.agents.react_agent import QwenPawAgent
from qwenpaw.app.mcp.manager import MCPClientManager
from qwenpaw.app.mcp.stateful_client import HttpStatefulClient
from qwenpaw.app.routers.mcp import (
    MCPClientCreateRequest,
    MCPClientUpdateRequest,
    _build_client_info,
)
from qwenpaw.config.config import MCPClientConfig


def _remote_config(**overrides):
    data = {
        "name": "remote",
        "transport": "streamable_http",
        "url": "https://mcp.example.com/mcp",
    }
    data.update(overrides)
    return MCPClientConfig(**data)


def test_mcp_client_config_tls_defaults():
    config = _remote_config()

    assert config.tls_verify is True
    assert config.ca_file == ""


def test_mcp_router_models_expose_tls_fields():
    info = _build_client_info(
        "remote",
        _remote_config(tls_verify=False, ca_file="/tmp/ca.pem"),
    )
    create = MCPClientCreateRequest(
        name="remote",
        transport="streamable_http",
        url="https://mcp.example.com/mcp",
        tls_verify=False,
        ca_file="/tmp/ca.pem",
    )
    update = MCPClientUpdateRequest(tls_verify=False, ca_file="/tmp/ca.pem")

    assert info.tls_verify is False
    assert info.ca_file == "/tmp/ca.pem"
    assert create.tls_verify is False
    assert create.ca_file == "/tmp/ca.pem"
    assert update.tls_verify is False
    assert update.ca_file == "/tmp/ca.pem"


def test_http_client_kwargs_disable_tls_verification():
    config = _remote_config(tls_verify=False, ca_file="/tmp/ca.pem")

    assert MCPClientManager._http_client_kwargs(config) == {"verify": False}


def test_http_client_kwargs_uses_ca_file_when_verification_enabled():
    config = _remote_config(ca_file="/tmp/ca.pem")

    assert MCPClientManager._http_client_kwargs(config) == {
        "verify": "/tmp/ca.pem",
    }


def test_build_client_passes_tls_kwargs_to_http_client():
    client = MCPClientManager._build_client(_remote_config(tls_verify=False))

    assert client.client_kwargs == {"verify": False}
    assert client._qwenpaw_rebuild_info["client_kwargs"] == {
        "verify": False,
    }


def test_rebuild_mcp_client_preserves_tls_kwargs():
    client = MCPClientManager._build_client(_remote_config(tls_verify=False))

    rebuilt = QwenPawAgent._rebuild_mcp_client(client)

    assert rebuilt is not None
    assert rebuilt.client_kwargs == {"verify": False}


def test_sse_httpx_factory_receives_tls_kwargs(monkeypatch):
    captured = {}

    class DummyAsyncClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)
    client = HttpStatefulClient(
        name="remote",
        transport="sse",
        url="https://mcp.example.com/sse",
        verify=False,
    )

    factory = client._make_sse_httpx_client_factory()
    created = factory(
        headers={"Authorization": "Bearer token"},
        timeout=httpx.Timeout(30),
    )

    assert isinstance(created, DummyAsyncClient)
    assert captured["verify"] is False
    assert captured["follow_redirects"] is True
    assert captured["headers"] == {"Authorization": "Bearer token"}
