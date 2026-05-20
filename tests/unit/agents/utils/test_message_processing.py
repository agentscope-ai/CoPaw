# -*- coding: utf-8 -*-
"""Tests for message_processing utils.

Covers:
- is_first_user_interaction
- prepend_to_message_content
"""
# pylint: disable=protected-access
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from agentscope.message import Msg

from qwenpaw.agents.utils.message_processing import (
    _extract_source_and_filename,
    is_first_user_interaction,
    prepend_to_message_content,
    process_file_and_media_blocks_in_message,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _msg(role: str, content="content"):
    m = MagicMock()
    m.role = role
    m.content = content
    return m


# ---------------------------------------------------------------------------
# is_first_user_interaction
# ---------------------------------------------------------------------------


class TestIsFirstUserInteraction:
    """P0: first user interaction detection."""

    def test_empty_messages_returns_false(self):
        assert is_first_user_interaction([]) is False

    def test_single_user_no_assistant_is_first(self):
        msgs = [_msg("user")]
        assert is_first_user_interaction(msgs) is True

    def test_user_with_assistant_is_not_first(self):
        msgs = [_msg("user"), _msg("assistant")]
        assert is_first_user_interaction(msgs) is False

    def test_multiple_users_is_not_first(self):
        msgs = [_msg("user"), _msg("user")]
        assert is_first_user_interaction(msgs) is False

    def test_system_then_user_is_first(self):
        """System messages before the user message are skipped."""
        msgs = [_msg("system"), _msg("user")]
        assert is_first_user_interaction(msgs) is True

    def test_multiple_system_then_user_is_first(self):
        msgs = [_msg("system"), _msg("system"), _msg("user")]
        assert is_first_user_interaction(msgs) is True

    def test_system_user_assistant_is_not_first(self):
        msgs = [_msg("system"), _msg("user"), _msg("assistant")]
        assert is_first_user_interaction(msgs) is False

    def test_only_system_messages_returns_false(self):
        msgs = [_msg("system"), _msg("system")]
        assert is_first_user_interaction(msgs) is False

    def test_only_assistant_returns_false(self):
        msgs = [_msg("assistant")]
        assert is_first_user_interaction(msgs) is False


# ---------------------------------------------------------------------------
# prepend_to_message_content
# ---------------------------------------------------------------------------


class TestPrependToMessageContent:
    """P0: guidance text is prepended to the message."""

    def test_prepend_to_string_content(self):
        msg = _msg("user", content="hello")
        prepend_to_message_content(msg, "guidance")
        assert msg.content == "guidance\n\nhello"

    def test_prepend_to_string_content_empty_string(self):
        msg = _msg("user", content="")
        prepend_to_message_content(msg, "guidance")
        assert msg.content == "guidance\n\n"

    def test_prepend_to_list_with_text_block(self):
        """Prepends into the first text block dict."""
        msg = _msg(
            "user",
            content=[
                {"type": "text", "text": "original"},
            ],
        )
        prepend_to_message_content(msg, "guidance")
        assert msg.content[0]["text"] == "guidance\n\noriginal"

    def test_prepend_inserts_block_when_no_text_block(self):
        """No text block → inserts new block at start."""
        msg = _msg(
            "user",
            content=[
                {"type": "image", "url": "http://img"},
            ],
        )
        prepend_to_message_content(msg, "guidance")
        first = msg.content[0]
        assert first == {"type": "text", "text": "guidance"}

    def test_prepend_to_non_list_non_str_content_noop(self):
        """Non-string, non-list content is left untouched."""
        msg = _msg("user", content=42)
        prepend_to_message_content(msg, "guidance")
        assert msg.content == 42

    def test_prepend_modifies_first_text_block_only(self):
        """Only the first text block is modified."""
        msg = _msg(
            "user",
            content=[
                {"type": "text", "text": "first"},
                {"type": "text", "text": "second"},
            ],
        )
        prepend_to_message_content(msg, "guidance")
        assert msg.content[0]["text"] == "guidance\n\nfirst"
        assert msg.content[1]["text"] == "second"

    def test_prepend_preserves_other_blocks(self):
        """Non-text blocks after the text block are preserved."""
        msg = _msg(
            "user",
            content=[
                {"type": "text", "text": "text"},
                {"type": "image", "url": "http://img"},
            ],
        )
        prepend_to_message_content(msg, "guidance")
        assert len(msg.content) == 2
        assert msg.content[1]["type"] == "image"


# ---------------------------------------------------------------------------
# audio source extraction
# ---------------------------------------------------------------------------


class TestAudioDataSource:
    def test_audio_top_level_data_local_path_becomes_file_url(self, tmp_path):
        audio_path = tmp_path / "voice.oga"
        audio_path.write_bytes(b"audio")

        source, filename = _extract_source_and_filename(
            {
                "type": "audio",
                "data": str(audio_path),
                "format": "ogg",
            },
            "audio",
        )

        assert source == {
            "type": "url",
            "url": audio_path.resolve().as_uri(),
            "media_type": "audio/ogg",
        }
        assert filename == "voice.oga"

    def test_audio_top_level_data_base64_stays_base64(self):
        source, filename = _extract_source_and_filename(
            {
                "type": "audio",
                "data": "YXVkaW8=",
                "format": "mp3",
            },
            "audio",
        )

        assert source == {
            "type": "base64",
            "data": "YXVkaW8=",
            "media_type": "audio/mp3",
        }
        assert filename is None

    @pytest.mark.asyncio
    async def test_audio_top_level_data_is_transcribed(
        self,
        tmp_path,
        monkeypatch,
    ):
        audio_path = tmp_path / "voice.oga"
        audio_path.write_bytes(b"audio")

        async def fake_transcribe(path):
            assert path == str(audio_path.resolve())
            return "hello from voice"

        monkeypatch.setattr(
            "qwenpaw.agents.utils.audio_transcription.transcribe_audio",
            fake_transcribe,
        )
        monkeypatch.setattr(
            "qwenpaw.agents.utils.message_processing.load_config",
            lambda: SimpleNamespace(
                agents=SimpleNamespace(audio_mode="auto", language="en"),
            ),
        )

        msg = Msg(
            name="user",
            role="user",
            content=[
                {
                    "type": "audio",
                    "data": str(audio_path),
                    "format": "ogg",
                },
            ],
        )

        await process_file_and_media_blocks_in_message(msg)

        assert msg.content == [
            {
                "type": "text",
                "text": "[Voice message]: hello from voice",
            },
        ]
