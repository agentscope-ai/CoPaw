# -*- coding: utf-8 -*-
"""Unit tests for cron executor checkpoint and auto-reset logic."""

import json
from pathlib import Path

from qwenpaw.app.crons.executor import (
    _save_checkpoint,
    _build_checkpoint_summary,
)
from qwenpaw.app.crons.models import JobRuntimeSpec


class TestSaveCheckpoint:
    """Tests for _save_checkpoint function."""

    def test_creates_checkpoint_file(self, tmp_path):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        checkpoint_dir = str(tmp_path / "checkpoints")
        path = _save_checkpoint(
            checkpoint_dir=checkpoint_dir,
            job_id="job-1",
            session_id="session-abc",
            messages=messages,
            compressed_summary="test summary",
        )
        assert Path(path).exists()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["job_id"] == "job-1"
        assert data["session_id"] == "session-abc"
        assert data["message_count"] == 2
        assert data["compressed_summary"] == "test summary"
        assert len(data["messages"]) == 2

    def test_creates_directory_if_missing(self, tmp_path):
        checkpoint_dir = str(tmp_path / "nested" / "dir" / "cp")
        path = _save_checkpoint(
            checkpoint_dir=checkpoint_dir,
            job_id="job-2",
            session_id="session-xyz",
            messages=[],
        )
        assert Path(path).exists()

    def test_empty_messages_and_summary(self, tmp_path):
        checkpoint_dir = str(tmp_path / "checkpoints")
        path = _save_checkpoint(
            checkpoint_dir=checkpoint_dir,
            job_id="job-3",
            session_id="session-empty",
            messages=[],
            compressed_summary="",
        )
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["message_count"] == 0
        assert data["compressed_summary"] == ""


class TestBuildCheckpointSummary:
    """Tests for _build_checkpoint_summary function."""

    def test_with_compressed_summary(self):
        messages = [{"role": "user", "content": "hello"}]
        result = _build_checkpoint_summary(messages, "existing summary")
        assert "existing summary" in result
        assert "Previous session checkpoint summary" in result

    def test_with_recent_exchanges(self):
        messages = [
            {"role": "user", "content": "do task A"},
            {"role": "assistant", "content": "task A done"},
        ]
        result = _build_checkpoint_summary(messages)
        assert "[user]" in result
        assert "[assistant]" in result

    def test_empty_messages(self):
        result = _build_checkpoint_summary([])
        assert "Previous session checkpoint summary" in result
        assert "fresh session" in result

    def test_content_as_list_blocks(self):
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "block content here"},
                ],
            },
        ]
        result = _build_checkpoint_summary(messages)
        assert "block content here" in result


class TestJobRuntimeSpecAutoReset:
    """Tests for auto_reset field in JobRuntimeSpec."""

    def test_default_auto_reset_is_false(self):
        spec = JobRuntimeSpec()
        assert spec.auto_reset is False

    def test_default_checkpoint_dir(self):
        spec = JobRuntimeSpec()
        assert spec.reset_checkpoint_dir == "checkpoints"

    def test_auto_reset_true(self):
        spec = JobRuntimeSpec(auto_reset=True, reset_checkpoint_dir="/tmp/cp")
        assert spec.auto_reset is True
        assert spec.reset_checkpoint_dir == "/tmp/cp"

    def test_serialization_roundtrip(self):
        spec = JobRuntimeSpec(auto_reset=True, reset_checkpoint_dir="my_cps")
        data = spec.model_dump()
        spec2 = JobRuntimeSpec(**data)
        assert spec2.auto_reset is True
        assert spec2.reset_checkpoint_dir == "my_cps"
