# -*- coding: utf-8 -*-
# pylint: disable=protected-access
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


def test_build_client_disables_tls_verification():
    config = _remote_config(tls_verify=False)

    client = MCPClientManager._build_client(config)

    assert isinstance(client, HttpStatefulClient)
    assert client.client_kwargs == {"verify": False}
    assert client._qwenpaw_rebuild_info["tls_verify"] is False


def test_build_client_uses_custom_ca_file(monkeypatch, tmp_path):
    ca_file = tmp_path / "ca.pem"
    monkeypatch.setenv("QWENPAW_TEST_CA_FILE", str(ca_file))
    config = _remote_config(ca_file="$QWENPAW_TEST_CA_FILE")

    client = MCPClientManager._build_client(config)

    assert isinstance(client, HttpStatefulClient)
    assert client.client_kwargs == {"verify": str(ca_file)}
    assert client._qwenpaw_rebuild_info["ca_file"] == "$QWENPAW_TEST_CA_FILE"


def test_build_client_keeps_default_tls_settings_empty():
    config = _remote_config()

    client = MCPClientManager._build_client(config)

    assert isinstance(client, HttpStatefulClient)
    assert not client.client_kwargs


def test_build_client_info_exposes_tls_fields():
    config = _remote_config(
        tls_verify=False,
        ca_file="/etc/ssl/private-ca.pem",
    )

    info = _build_client_info("remote", config)

    assert info.tls_verify is False
    assert info.ca_file == "/etc/ssl/private-ca.pem"
