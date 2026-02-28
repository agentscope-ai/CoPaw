# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

from ..constant import HEARTBEAT_FILE, JOBS_FILE, CHATS_FILE, WORKING_DIR
from .config import Config, HeartbeatConfig, LastApiConfig, LastDispatchConfig


def get_config_path() -> Path:
    """Get the path to the config file."""
    return WORKING_DIR.joinpath("config.json")


def get_heartbeat_query_path() -> Path:
    """Get path to heartbeat query file (HEARTBEAT.md in working dir)."""
    return get_config_path().parent.joinpath(HEARTBEAT_FILE)


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load config from file. Returns default Config if file is missing."""
    if config_path is None:
        config_path = get_config_path()
    if not config_path.is_file():
        return Config()
    with open(config_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    # Backward compat: top-level last_api_host / last_api_port -> last_api
    if "last_api_host" in data or "last_api_port" in data:
        la = data.setdefault("last_api", {})
        if "host" not in la and "last_api_host" in data:
            la["host"] = data.get("last_api_host")
        if "port" not in la and "last_api_port" in data:
            la["port"] = data.get("last_api_port")
    return Config.model_validate(data)


def save_config(config: Config, config_path: Optional[Path] = None) -> None:
    """Save the config to the file."""
    if config_path is None:
        config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(
            config.model_dump(mode="json", by_alias=True),
            file,
            indent=2,
            ensure_ascii=False,
        )


def get_timezone() -> str:
    """Return the configured timezone name (e.g. 'Asia/Shanghai').

    Falls back to the system local timezone when the config value is empty.
    """
    import zoneinfo

    config = load_config()
    tz_name = config.timezone.strip()
    if tz_name:
        return tz_name
    # Detect system local timezone via tzlocal (if available) or env
    import os
    import time

    # 1. Check TZ environment variable
    env_tz = os.environ.get("TZ", "").strip()
    if env_tz:
        try:
            zoneinfo.ZoneInfo(env_tz)
            return env_tz
        except (KeyError, Exception):
            pass
    # 2. macOS/Linux: read /etc/localtime symlink
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        target = str(localtime.resolve())
        # e.g. .../zoneinfo/Asia/Shanghai or .../zoneinfo.default/Asia/Shanghai
        for marker in ("/zoneinfo/", "/zoneinfo.default/"):
            idx = target.find(marker)
            if idx != -1:
                candidate = target[idx + len(marker) :]
                try:
                    zoneinfo.ZoneInfo(candidate)
                    return candidate
                except (KeyError, Exception):
                    pass
    # 3. Fallback: compute UTC offset and pick a generic Etc/GMT name
    offset_seconds = -time.timezone if time.daylight == 0 else -time.altzone
    offset_hours = offset_seconds // 3600
    # Etc/GMT sign is inverted: Etc/GMT-8 = UTC+8
    etc_name = f"Etc/GMT{-offset_hours:+d}" if offset_hours != 0 else "UTC"
    try:
        zoneinfo.ZoneInfo(etc_name)
        return etc_name
    except (KeyError, Exception):
        return "UTC"


def get_heartbeat_config() -> HeartbeatConfig:
    """Return effective heartbeat config (from file or default 30m/main)."""
    config = load_config()
    hb = config.agents.defaults.heartbeat
    return hb if hb is not None else HeartbeatConfig()


def update_last_dispatch(channel: str, user_id: str, session_id: str) -> None:
    """Persist last user-reply dispatch target (user send+reply only)."""
    config = load_config()
    config.last_dispatch = LastDispatchConfig(
        channel=channel,
        user_id=user_id,
        session_id=session_id,
    )
    save_config(config)


def read_last_api() -> Optional[Tuple[str, int]]:
    """Read last API host/port from config (via config load/save)."""
    config = load_config()
    host = config.last_api.host
    port = config.last_api.port
    if not host or port is None:
        return None
    return host, port


def write_last_api(host: str, port: int) -> None:
    """Write last API host/port to config (via config load/save)."""
    config = load_config()
    config.last_api = LastApiConfig(host=host, port=port)
    save_config(config)


def get_jobs_path() -> Path:
    """Return cron jobs.json path."""

    return (WORKING_DIR / JOBS_FILE).expanduser()


def get_chats_path() -> Path:
    """Return chats.json path."""
    return (WORKING_DIR / CHATS_FILE).expanduser()
