# -*- coding: utf-8 -*-
"""Query token usage by date range and model."""

import json
from datetime import date, timedelta

from .storage import get_token_usage_path


def query_token_usage(
    start_date: date | None = None,
    end_date: date | None = None,
    model_name: str | None = None,
) -> list[dict]:
    """Query token usage records.

    Args:
        start_date: Start of date range (inclusive).
        end_date: End of date range (inclusive).
        model_name: Optional model name filter.

    Returns:
        List of records, each with keys: date, model, prompt_tokens,
        completion_tokens, total_tokens, call_count.
    """
    path = get_token_usage_path()
    if not path.exists():
        return []

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return []

    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    results: list[dict] = []
    current = start_date
    while current <= end_date:
        date_str = current.isoformat()
        by_model = data.get(date_str, {})
        for model, entry in by_model.items():
            if model_name is not None and model != model_name:
                continue
            results.append(
                {
                    "date": date_str,
                    "model": model,
                    "prompt_tokens": entry.get("prompt_tokens", 0),
                    "completion_tokens": entry.get("completion_tokens", 0),
                    "total_tokens": entry.get("total_tokens", 0),
                    "call_count": entry.get("call_count", 0),
                },
            )
        current += timedelta(days=1)

    return results


def get_token_usage_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    model_name: str | None = None,
) -> dict:
    """Get aggregated token usage summary.

    Args:
        start_date: Start of date range (inclusive).
        end_date: End of date range (inclusive).
        model_name: Optional model name filter.

    Returns:
        Dict with keys: total_prompt_tokens, total_completion_tokens,
        total_tokens, total_calls, by_model, by_date.
    """
    records = query_token_usage(
        start_date=start_date,
        end_date=end_date,
        model_name=model_name,
    )

    total_prompt = 0
    total_completion = 0
    total_calls = 0
    by_model: dict[str, dict] = {}
    by_date: dict[str, dict] = {}

    for r in records:
        pt = r["prompt_tokens"]
        ct = r["completion_tokens"]
        calls = r["call_count"]
        total_prompt += pt
        total_completion += ct
        total_calls += calls

        model = r["model"]
        if model not in by_model:
            by_model[model] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "call_count": 0,
            }
        by_model[model]["prompt_tokens"] += pt
        by_model[model]["completion_tokens"] += ct
        by_model[model]["total_tokens"] += pt + ct
        by_model[model]["call_count"] += calls

        dt = r["date"]
        if dt not in by_date:
            by_date[dt] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "call_count": 0,
            }
        by_date[dt]["prompt_tokens"] += pt
        by_date[dt]["completion_tokens"] += ct
        by_date[dt]["total_tokens"] += pt + ct
        by_date[dt]["call_count"] += calls

    return {
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_prompt + total_completion,
        "total_calls": total_calls,
        "by_model": by_model,
        "by_date": dict(sorted(by_date.items())),
    }
