# -*- coding: utf-8 -*-
"""Storage for token usage records."""

from pathlib import Path

from ..constant import WORKING_DIR, TOKEN_USAGE_FILE


def get_token_usage_path() -> Path:
    """Return the path to the token usage JSON file."""
    return (WORKING_DIR / TOKEN_USAGE_FILE).expanduser()
