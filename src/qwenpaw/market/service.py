# -*- coding: utf-8 -*-
"""Market search service.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any

from .providers import PROVIDERS
from .schema import MarketResult, MarketSearchError, ProviderInfo


logger = logging.getLogger(__name__)


_MAX_LIMIT = 50


def list_providers() -> list[ProviderInfo]:
    out: list[ProviderInfo] = []
    for key, provider in PROVIDERS.items():
        is_available, reason = provider.available()
        out.append(
            ProviderInfo(
                key=key,
                label=provider.label,
                available=is_available,
                reason=reason,
            ),
        )
    return out


async def search_market(
    query: str,
    providers: list[str] | None = None,
    limit: int = 20,
    page: int = 1,
    lang: str = "en",
) -> tuple[list[MarketResult], list[MarketSearchError], bool, int]:
    capped_limit = max(1, min(int(limit or 1), _MAX_LIMIT))
    capped_page = max(1, int(page or 1))
    selected_keys = _select_keys(providers)

    coros = [
        _run_one(key, query, capped_limit, capped_page, lang)
        for key in selected_keys
    ]
    paired = await asyncio.gather(*coros)

    results: list[MarketResult] = []
    errors: list[MarketSearchError] = []
    has_more = False
    total = 0
    # `total` is a best-effort sum across providers and only ever a lower
    # bound: ClawHub contributes `len(local_slice)` capped at its overfetch
    # ceiling, ModelScope/Aliyun contribute upstream-truthful filtered
    # counts. Providers that fail to report a total contribute 0. The
    # frontend pairs this with `has_more` to render "X+" vs "X" — see
    # `useMarketSearch.ts` and `Market/index.tsx:showTotal`.
    #
    # `has_more` is OR'd across providers: as long as any one provider
    # could yield more results, the UI shows pagination affordances and
    # prefetches page+1. Exhausted providers naturally contribute empty
    # slices on subsequent pages — no extra coordination needed.
    for outcome in paired:
        if isinstance(outcome, MarketSearchError):
            errors.append(outcome)
            continue
        sub_results, sub_has_more, sub_total = outcome
        results.extend(sub_results)
        has_more = has_more or sub_has_more
        if isinstance(sub_total, int) and sub_total > 0:
            total += sub_total
    return results, errors, has_more, total


def _select_keys(requested: list[str] | None) -> list[str]:
    if not requested:
        return [key for key, p in PROVIDERS.items() if p.available()[0]]
    return [key for key in requested if key in PROVIDERS]


async def _run_one(
    key: str,
    query: str,
    limit: int,
    page: int,
    lang: str,
) -> tuple[list[MarketResult], bool, int | None] | MarketSearchError:
    provider = PROVIDERS[key]
    is_available, reason = provider.available()
    if not is_available:
        return MarketSearchError(
            provider=key,
            message=reason or "provider unavailable",
        )
    # Providers that don't declare a `lang` kwarg simply ignore it.
    kwargs = _supported_kwargs(provider.search, lang=lang)
    try:
        return await provider.search(query, limit, page, **kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Market provider %s failed for query=%r: %s",
            key,
            query,
            exc,
        )
        return MarketSearchError(provider=key, message=str(exc) or repr(exc))


def _supported_kwargs(func: Any, **candidates: Any) -> dict[str, Any]:
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return {}
    params = sig.parameters
    accepts_var_kw = any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()
    )
    if accepts_var_kw:
        return candidates
    return {k: v for k, v in candidates.items() if k in params}
