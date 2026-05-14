# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from datetime import datetime, timedelta, timezone

from qwenpaw.backup._ops import create as create_ops
from qwenpaw.backup.models import BackupMeta, DeleteBackupsResponse


def _meta(backup_id: str, minutes_ago: int) -> BackupMeta:
    return BackupMeta(
        id=backup_id,
        name=backup_id,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
    )


def test_backup_retention_disabled_does_not_delete(monkeypatch):
    calls = []

    monkeypatch.setattr(create_ops, "_list_sync", lambda: [_meta("old", 10)])
    monkeypatch.setattr(
        create_ops,
        "_delete_sync",
        lambda ids: calls.append(ids) or DeleteBackupsResponse(deleted=ids),
    )

    result = create_ops._apply_backup_retention(
        keep_last=None,
        protected_backup_id="new",
    )

    assert result == DeleteBackupsResponse()
    assert not calls


def test_backup_retention_keeps_newest_and_protected_backup(monkeypatch):
    deleted = []
    backups = [
        _meta("newest", 0),
        _meta("middle", 5),
        _meta("new", 10),
        _meta("oldest", 20),
    ]

    monkeypatch.setattr(create_ops, "_list_sync", lambda: backups)
    monkeypatch.setattr(
        create_ops,
        "_delete_sync",
        lambda ids: deleted.extend(ids) or DeleteBackupsResponse(deleted=ids),
    )

    result = create_ops._apply_backup_retention(
        keep_last=2,
        protected_backup_id="new",
    )

    assert result.deleted == ["middle", "oldest"]
    assert deleted == ["middle", "oldest"]


def test_backup_retention_keep_one_preserves_created_backup(monkeypatch):
    deleted = []
    backups = [
        _meta("newest", 0),
        _meta("new", 5),
        _meta("oldest", 10),
    ]

    monkeypatch.setattr(create_ops, "_list_sync", lambda: backups)
    monkeypatch.setattr(
        create_ops,
        "_delete_sync",
        lambda ids: deleted.extend(ids) or DeleteBackupsResponse(deleted=ids),
    )

    result = create_ops._apply_backup_retention(
        keep_last=1,
        protected_backup_id="new",
    )

    assert result.deleted == ["newest", "oldest"]
    assert deleted == ["newest", "oldest"]
