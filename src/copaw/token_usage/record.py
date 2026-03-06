# -*- coding: utf-8 -*-
"""Record token usage from LLM API calls."""

import json
import logging
import threading
from datetime import date, datetime
from pathlib import Path

from .storage import get_token_usage_path

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()


def record_token_usage(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    at_date: date | None = None,
) -> None:
    """Record token usage for a given model and date.

    Args:
        model_name: Name of the model (e.g. "qwen3-max", "gpt-4").
        prompt_tokens: Number of input/prompt tokens.
        completion_tokens: Number of output/completion tokens.
        at_date: Date to record under. Defaults to today (UTC).
    """
    if at_date is None:
        at_date = date.today()

    date_str = at_date.isoformat()
    path = get_token_usage_path()

    with _LOCK:
        try:
            data: dict = {}
            if path.exists():
                try:
                    raw = path.read_text(encoding="utf-8")
                    data = json.loads(raw) if raw.strip() else {}
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(
                        "Failed to read token usage file %s: %s",
                        path,
                        e,
                    )

            if date_str not in data:
                data[date_str] = {}

            by_model = data[date_str]
            if model_name not in by_model:
                by_model[model_name] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "call_count": 0,
                }

            entry = by_model[model_name]
            entry["prompt_tokens"] += prompt_tokens
            entry["completion_tokens"] += completion_tokens
            entry["total_tokens"] += prompt_tokens + completion_tokens
            entry["call_count"] += 1

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning(
                "Failed to write token usage to %s: %s",
                path,
                e,
            )
