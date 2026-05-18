# -*- coding: utf-8 -*-
from __future__ import annotations

from qwenpaw.app.routers import _backup_helpers as helpers
from qwenpaw.app.routers._backup_helpers import restored_local_keys
from qwenpaw.backup.models import BackupMeta, BackupScope, RestoreBackupRequest


def _meta(*, include_global_config: bool) -> BackupMeta:
    return BackupMeta(
        id="backup-test",
        name="Backup",
        accepted_via_trust=True,
        scope=BackupScope(include_global_config=include_global_config),
    )


def test_preserved_keys_are_empty_for_agent_only_restore() -> None:
    req = RestoreBackupRequest(
        include_global_config=False,
        preserve_local_protected_config=True,
    )

    assert not restored_local_keys(
        req,
        _meta(include_global_config=True),
        archive_has_global_config=True,
    )


def test_preserved_keys_are_empty_when_archive_has_no_config() -> None:
    req = RestoreBackupRequest(
        include_global_config=True,
        preserve_local_protected_config=True,
    )

    assert not restored_local_keys(
        req,
        _meta(include_global_config=True),
        archive_has_global_config=False,
    )


def test_preserved_keys_report_actual_config_overlay() -> None:
    req = RestoreBackupRequest(
        include_global_config=True,
        preserve_local_protected_config=True,
    )

    assert restored_local_keys(
        req,
        _meta(include_global_config=False),
        archive_has_global_config=True,
    ) == [
        "security",
        "mcp",
    ]


def test_pending_token_preserves_trust_mode(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(helpers, "BACKUP_DIR", tmp_path)

    for mode in (None, "legacy", "foreign"):
        path = tmp_path / f"backup{helpers.upload_suffix_for_trust_mode(mode)}"
        path.write_bytes(b"zip")

        parsed_path, parsed_mode = helpers.parse_pending_token(path.name)

        assert parsed_path == path.resolve()
        assert parsed_mode == mode
