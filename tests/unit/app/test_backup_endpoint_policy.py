# -*- coding: utf-8 -*-
from __future__ import annotations

from types import SimpleNamespace

from starlette.requests import Request
from starlette.responses import Response

from qwenpaw.app import auth, backup_endpoint_policy


def _request(
    path: str = "/api/backups",
    *,
    method: str = "GET",
    client_host: str = "127.0.0.1",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "raw_path": path.encode(),
            "headers": headers or [],
            "client": (client_host, 12345),
            "scheme": "http",
            "server": ("127.0.0.1", 8088),
            "query_string": b"",
        },
    )


def _config(allowed_hosts: list[str]):
    return SimpleNamespace(
        security=SimpleNamespace(allow_no_auth_hosts=allowed_hosts),
    )


def test_non_backup_paths_are_passthrough():
    decision = backup_endpoint_policy.apply(
        _request("/api/agents", client_host="192.0.2.10"),
        skip_auth=True,
    )

    assert decision is True


def test_auth_off_rejects_remote_backup_host(monkeypatch):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: False)
    monkeypatch.setattr(auth, "has_registered_users", lambda: False)
    monkeypatch.setattr(
        backup_endpoint_policy,
        "_get_cached_config",
        lambda: _config(["127.0.0.1", "::1"]),
    )

    decision = backup_endpoint_policy.apply(
        _request(client_host="192.0.2.10"),
        skip_auth=True,
    )

    assert isinstance(decision, Response)
    assert decision.status_code == 403


def test_ipv4_mapped_loopback_matches_allow_list(monkeypatch):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: False)
    monkeypatch.setattr(auth, "has_registered_users", lambda: False)
    monkeypatch.setattr(
        backup_endpoint_policy,
        "_get_cached_config",
        lambda: _config(["127.0.0.1", "::1"]),
    )

    decision = backup_endpoint_policy.apply(
        _request(client_host="::ffff:127.0.0.1"),
        skip_auth=True,
    )

    assert decision is True


def test_cross_site_backup_request_is_rejected(monkeypatch):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: False)
    monkeypatch.setattr(auth, "has_registered_users", lambda: False)

    decision = backup_endpoint_policy.apply(
        _request(headers=[(b"sec-fetch-site", b"cross-site")]),
        skip_auth=True,
    )

    assert isinstance(decision, Response)
    assert decision.status_code == 403


def test_same_site_backup_request_requires_configured_origin(monkeypatch):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: False)
    monkeypatch.setattr(auth, "has_registered_users", lambda: False)
    monkeypatch.setattr(
        backup_endpoint_policy,
        "_get_cached_config",
        lambda: _config(["127.0.0.1"]),
    )
    monkeypatch.setattr(
        backup_endpoint_policy,
        "CORS_ORIGINS",
        "http://localhost:5173",
    )

    decision = backup_endpoint_policy.apply(
        _request(
            headers=[
                (b"sec-fetch-site", b"same-site"),
                (b"origin", b"http://localhost:5173"),
            ],
        ),
        skip_auth=True,
    )

    assert decision is True


def test_same_site_backup_request_rejects_unconfigured_origin(monkeypatch):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: False)
    monkeypatch.setattr(auth, "has_registered_users", lambda: False)
    monkeypatch.setattr(
        backup_endpoint_policy,
        "CORS_ORIGINS",
        "http://localhost:5173",
    )

    decision = backup_endpoint_policy.apply(
        _request(
            headers=[
                (b"sec-fetch-site", b"same-site"),
                (b"origin", b"http://evil.localhost:5173"),
            ],
        ),
        skip_auth=True,
    )

    assert isinstance(decision, Response)
    assert decision.status_code == 403


def test_auth_on_backup_endpoint_forces_token_even_from_allow_list(
    monkeypatch,
):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: True)
    monkeypatch.setattr(auth, "has_registered_users", lambda: True)

    decision = backup_endpoint_policy.apply(_request(), skip_auth=True)

    assert decision is False


def test_auth_on_loopback_export_keeps_desktop_save_file_working(
    monkeypatch,
):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: True)
    monkeypatch.setattr(auth, "has_registered_users", lambda: True)

    decision = backup_endpoint_policy.apply(
        _request("/api/backups/backup-1/export"),
        skip_auth=False,
    )

    assert decision is True


def test_auth_on_non_loopback_export_still_requires_token(monkeypatch):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: True)
    monkeypatch.setattr(auth, "has_registered_users", lambda: True)

    decision = backup_endpoint_policy.apply(
        _request("/api/backups/backup-1/export", client_host="192.0.2.10"),
        skip_auth=False,
    )

    assert decision is False


def test_allow_hosts_endpoint_is_protected_boundary(monkeypatch):
    monkeypatch.setattr(auth, "is_auth_enabled", lambda: False)
    monkeypatch.setattr(auth, "has_registered_users", lambda: False)
    monkeypatch.setattr(
        backup_endpoint_policy,
        "_get_cached_config",
        lambda: _config(["127.0.0.1"]),
    )

    decision = backup_endpoint_policy.apply(
        _request(
            "/api/config/security/allow-no-auth-hosts",
            method="PUT",
            client_host="192.0.2.10",
        ),
        skip_auth=True,
    )

    assert isinstance(decision, Response)
    assert decision.status_code == 403
