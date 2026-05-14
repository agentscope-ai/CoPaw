# -*- coding: utf-8 -*-
"""Tests for encrypted OAuth credential storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qwenpaw.providers.auth.credential_store import OAuthCredentialStore
from qwenpaw.providers.auth.models import OAuthCredential


@pytest.fixture(autouse=True)
def _isolate_master_key(tmp_path: Path, monkeypatch):
    import qwenpaw.security.secret_store as mod

    test_key = bytes.fromhex(
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    )
    monkeypatch.setattr(mod, "_cached_master_key", test_key)
    monkeypatch.setattr(mod, "_cached_fernet", None)
    monkeypatch.setattr(mod, "_get_secret_dir", lambda: tmp_path)


def _credential() -> OAuthCredential:
    return OAuthCredential(
        provider_id="fake-oauth",
        access_token="access-secret",
        refresh_token="refresh-secret",
        account_label="octocat",
        scopes=["read:user"],
        created_at=1760000000,
        updated_at=1760000001,
    )


def test_save_encrypts_and_load_restores_credential(tmp_path: Path) -> None:
    store = OAuthCredentialStore(tmp_path / "oauth")
    store.save(_credential())

    path = tmp_path / "oauth" / "fake-oauth.json"
    assert path.exists()
    raw = path.read_text("utf-8")
    assert "access-secret" not in raw
    assert "refresh-secret" not in raw

    data = json.loads(raw)
    assert str(data["access_token"]).startswith("ENC:")
    assert str(data["refresh_token"]).startswith("ENC:")

    loaded = store.load("fake-oauth")
    assert loaded is not None
    assert loaded.provider_id == "fake-oauth"
    assert loaded.access_token == "access-secret"
    assert loaded.refresh_token == "refresh-secret"
    assert loaded.account_label == "octocat"
    assert loaded.scopes == ["read:user"]


def test_delete_removes_credential_file(tmp_path: Path) -> None:
    store = OAuthCredentialStore(tmp_path / "oauth")
    store.save(_credential())
    assert store.exists("fake-oauth")

    store.delete("fake-oauth")

    assert not store.exists("fake-oauth")
    assert store.load("fake-oauth") is None


def test_load_returns_none_for_corrupt_json(tmp_path: Path) -> None:
    root = tmp_path / "oauth"
    root.mkdir()
    (root / "fake-oauth.json").write_text("{not-json", "utf-8")

    assert OAuthCredentialStore(root).load("fake-oauth") is None


def test_load_returns_none_when_secret_field_cannot_decrypt(
    tmp_path: Path,
) -> None:
    root = tmp_path / "oauth"
    root.mkdir()
    (root / "fake-oauth.json").write_text(
        json.dumps(
            {
                "version": 1,
                "provider_id": "fake-oauth",
                "access_token": "ENC:corrupt",
                "created_at": 1760000000,
                "updated_at": 1760000001,
            },
        ),
        "utf-8",
    )

    assert OAuthCredentialStore(root).load("fake-oauth") is None


def test_save_rejects_empty_access_token(tmp_path: Path) -> None:
    credential = _credential()
    credential.access_token = ""
    store = OAuthCredentialStore(tmp_path / "oauth")

    with pytest.raises(ValueError):
        store.save(credential)

    assert not (tmp_path / "oauth" / "fake-oauth.json").exists()
