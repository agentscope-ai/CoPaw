# -*- coding: utf-8 -*-
"""Regression tests for timezone configuration (issue #154)."""

import asyncio
import json

import pytest


@pytest.fixture()
def tmp_config(monkeypatch, tmp_path):
    """Point config loading at a temporary config.json."""
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "copaw.config.utils.get_config_path",
        lambda: config_path,
    )
    return config_path


class TestGetTimezone:
    def test_returns_config_value_when_set(self, tmp_config):
        tmp_config.write_text(
            json.dumps({"timezone": "America/New_York"}),
            encoding="utf-8",
        )
        from copaw.config.utils import get_timezone

        assert get_timezone() == "America/New_York"

    def test_falls_back_to_system_timezone(self, tmp_config):
        """When config timezone is empty, should detect system timezone."""
        tmp_config.write_text(json.dumps({"timezone": ""}), encoding="utf-8")
        from copaw.config.utils import get_timezone

        tz = get_timezone()
        # Should be a non-empty valid IANA timezone name
        assert tz
        assert tz != ""
        # Verify it's a valid timezone
        from zoneinfo import ZoneInfo

        ZoneInfo(tz)  # should not raise

    def test_default_config_has_empty_timezone(self, tmp_config):
        from copaw.config.utils import load_config

        config = load_config()
        assert config.timezone == ""


class TestGetCurrentTimeUsesConfig:
    def test_uses_configured_timezone(self, tmp_config):
        tmp_config.write_text(
            json.dumps({"timezone": "America/New_York"}),
            encoding="utf-8",
        )
        from copaw.agents.tools.get_current_time import get_current_time

        result = asyncio.run(get_current_time())
        text = result.content[0]["text"]
        # Should contain EST or EDT (Eastern time)
        assert "EST" in text or "EDT" in text or "-0500" in text or "-0400" in text

    def test_utc_fallback_on_invalid_timezone(self, tmp_config):
        tmp_config.write_text(
            json.dumps({"timezone": "Invalid/Timezone"}),
            encoding="utf-8",
        )
        from copaw.agents.tools.get_current_time import get_current_time

        result = asyncio.run(get_current_time())
        text = result.content[0]["text"]
        # Should fall back to UTC
        assert "UTC" in text


class TestScheduleSpecTimezone:
    def test_empty_timezone_resolves_from_config(self, tmp_config):
        tmp_config.write_text(
            json.dumps({"timezone": "Asia/Tokyo"}),
            encoding="utf-8",
        )
        from copaw.app.crons.models import ScheduleSpec

        spec = ScheduleSpec(cron="0 9 * * *", timezone="")
        assert spec.timezone == "Asia/Tokyo"

    def test_explicit_timezone_preserved(self, tmp_config):
        from copaw.app.crons.models import ScheduleSpec

        spec = ScheduleSpec(cron="0 9 * * *", timezone="Europe/London")
        assert spec.timezone == "Europe/London"
