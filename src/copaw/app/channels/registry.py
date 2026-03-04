# -*- coding: utf-8 -*-
"""Channel registry: built-in + custom channels from working dir.

Channel classes are lazily imported to avoid pulling in heavy SDKs
(e.g. lark_oapi ~1.7s) at module load time.
"""
from __future__ import annotations

import importlib
import logging
import sys
from typing import TYPE_CHECKING

from ...constant import CUSTOM_CHANNELS_DIR
from .base import BaseChannel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Lazy channel mapping: key -> (module_path, class_name)
# Channels are only imported when actually needed.
_BUILTIN_LAZY: dict[str, tuple[str, str]] = {
    "imessage": (".imessage", "IMessageChannel"),
    "discord": (".discord_", "DiscordChannel"),
    "dingtalk": (".dingtalk", "DingTalkChannel"),
    "feishu": (".feishu", "FeishuChannel"),
    "qq": (".qq", "QQChannel"),
    "telegram": (".telegram", "TelegramChannel"),
    "console": (".console", "ConsoleChannel"),
}

# Cache for resolved channel classes
_resolved_channels: dict[str, type[BaseChannel]] = {}


def _resolve_channel(key: str) -> type[BaseChannel] | None:
    """Lazily import and cache a built-in channel class."""
    if key in _resolved_channels:
        return _resolved_channels[key]

    entry = _BUILTIN_LAZY.get(key)
    if entry is None:
        return None

    module_path, class_name = entry
    try:
        mod = importlib.import_module(module_path, package=__package__)
        cls = getattr(mod, class_name)
        _resolved_channels[key] = cls
        logger.debug("Lazily loaded channel: %s -> %s", key, class_name)
        return cls
    except Exception:
        logger.exception("Failed to lazily load channel: %s", key)
        return None


def _discover_custom_channels() -> dict[str, type[BaseChannel]]:
    """Load channel classes from CUSTOM_CHANNELS_DIR."""
    out: dict[str, type[BaseChannel]] = {}
    if not CUSTOM_CHANNELS_DIR.is_dir():
        return out

    dir_str = str(CUSTOM_CHANNELS_DIR)
    if dir_str not in sys.path:
        sys.path.insert(0, dir_str)

    for path in sorted(CUSTOM_CHANNELS_DIR.iterdir()):
        if path.suffix == ".py" and path.stem != "__init__":
            name = path.stem
        elif path.is_dir() and (path / "__init__.py").exists():
            name = path.name
        else:
            continue
        try:
            mod = importlib.import_module(name)
        except Exception:
            logger.exception("failed to load custom channel: %s", name)
            continue
        for obj in vars(mod).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseChannel)
                and obj is not BaseChannel
            ):
                channel_key = getattr(obj, "channel", None)
                if channel_key:
                    out[channel_key] = obj
                    logger.debug("custom channel registered: %s", channel_key)
    return out


BUILTIN_CHANNEL_KEYS = frozenset(_BUILTIN_LAZY.keys())


def get_channel_registry() -> dict[str, type[BaseChannel]]:
    """Built-in channel classes + custom channels from custom_channels/.
    
    Built-in channels are resolved lazily on first access.
    """
    out: dict[str, type[BaseChannel]] = {}
    for key in _BUILTIN_LAZY:
        cls = _resolve_channel(key)
        if cls is not None:
            out[key] = cls
    out.update(_discover_custom_channels())
    return out


def get_channel_class(key: str) -> type[BaseChannel] | None:
    """Get a single channel class by key (lazy, no full registry scan)."""
    cls = _resolve_channel(key)
    if cls is not None:
        return cls
    # Fallback: check custom channels
    custom = _discover_custom_channels()
    return custom.get(key)
