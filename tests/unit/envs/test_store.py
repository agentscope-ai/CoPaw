# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from qwenpaw.envs import store


@pytest.fixture(name="fake_crypto")
def fixture_fake_crypto(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_encrypt(value: str) -> str:
        return f"ENC:{value}" if value else value

    def fake_decrypt(value: str) -> str:
        return value.removeprefix("ENC:") if value else value

    def fake_is_encrypted(value: str) -> bool:
        return bool(value) and value.startswith("ENC:")

    monkeypatch.setattr(store, "encrypt", fake_encrypt)
    monkeypatch.setattr(store, "decrypt", fake_decrypt)
    monkeypatch.setattr(store, "is_encrypted", fake_is_encrypted)


def test_load_envs_rewrites_legacy_plaintext_values(
    tmp_path: Path,
    fake_crypto,
) -> None:
    del fake_crypto
    path = tmp_path / "envs.json"
    path.write_text(
        json.dumps(
            {
                "API_KEY": "plain-secret",
                "EMPTY_VALUE": "",
            },
        ),
        encoding="utf-8",
    )

    envs = store.load_envs(path)

    assert envs == {
        "API_KEY": "plain-secret",
        "EMPTY_VALUE": "",
    }
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted == {
        "API_KEY": "ENC:plain-secret",
        "EMPTY_VALUE": "",
    }


def test_save_envs_encrypts_file_and_syncs_process_environ(
    tmp_path: Path,
    fake_crypto,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del fake_crypto
    path = tmp_path / "secrets" / "envs.json"
    path.parent.mkdir()
    path.write_text(
        json.dumps(
            {
                "REMOVE_ME": "ENC:old-value",
                "KEEP_ME": "ENC:old-keep",
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("REMOVE_ME", "old-value")
    monkeypatch.setenv("KEEP_ME", "old-keep")

    store.save_envs(
        {
            "KEEP_ME": "new-keep",
            "NEW_KEY": "new-value",
        },
        path,
    )

    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted == {
        "KEEP_ME": "ENC:new-keep",
        "NEW_KEY": "ENC:new-value",
    }
    assert "REMOVE_ME" not in os.environ
    assert os.environ["KEEP_ME"] == "new-keep"
    assert os.environ["NEW_KEY"] == "new-value"


def test_sync_environ_keeps_user_modified_stale_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USER_EDITED", "manual-value")

    store._sync_environ(
        old={"USER_EDITED": "persisted-value"},
        new={},
    )

    assert os.environ["USER_EDITED"] == "manual-value"


def test_load_envs_into_environ_skips_protected_bootstrap_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QWENPAW_WORKING_DIR", "/runtime/work")
    monkeypatch.setenv("EXISTING_KEY", "runtime-value")
    monkeypatch.setattr(
        store,
        "load_envs",
        lambda: {
            "QWENPAW_WORKING_DIR": "/persisted/work",
            "QWENPAW_SECRET_DIR": "/persisted/secret",
            "EXISTING_KEY": "persisted-value",
            "NEW_KEY": "new-value",
        },
    )
    monkeypatch.setattr(
        "qwenpaw.backup._utils.safe_swap.cleanup_stale_restore_artifacts",
        lambda *_args, **_kwargs: None,
    )

    envs = store.load_envs_into_environ()

    assert envs["QWENPAW_WORKING_DIR"] == "/persisted/work"
    assert os.environ["QWENPAW_WORKING_DIR"] == "/runtime/work"
    assert "QWENPAW_SECRET_DIR" not in os.environ
    assert os.environ["EXISTING_KEY"] == "runtime-value"
    assert os.environ["NEW_KEY"] == "new-value"
