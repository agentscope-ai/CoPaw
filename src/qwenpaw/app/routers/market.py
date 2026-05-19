# -*- coding: utf-8 -*-
"""Skill Market HTTP routes.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...market import (
    MarketResult,
    MarketSearchError,
    ProviderInfo,
    list_providers,
    search_market,
)
from ...market.providers import PROVIDERS


router = APIRouter(prefix="/market", tags=["market"])


class ProviderInfoSpec(BaseModel):
    key: str
    label: str
    available: bool
    reason: str | None = None


class MarketResultSpec(BaseModel):
    source: str
    slug: str
    name: str
    description: str | None = None
    source_url: str
    version: str | None = None
    author: str | None = None
    icon_url: str | None = None
    stats: dict[str, str | int] | None = None


class MarketSearchErrorSpec(BaseModel):
    provider: str
    message: str


class MarketSearchRequest(BaseModel):
    query: str = Field("", description="User-typed search string")
    providers: list[str] | None = Field(default=None)
    limit: int = Field(20, ge=1, le=50)
    page: int = Field(1, ge=1, le=100)
    lang: str = Field("en", description="UI language for locale-aware fields")


class MarketSearchResponse(BaseModel):
    results: list[MarketResultSpec]
    errors: list[MarketSearchErrorSpec]
    has_more: bool = False
    total: int = 0


@router.get("/providers", response_model=list[ProviderInfoSpec])
async def get_market_providers() -> list[ProviderInfoSpec]:
    return [_provider_info_to_spec(p) for p in list_providers()]


@router.post("/search", response_model=MarketSearchResponse)
async def market_search(body: MarketSearchRequest) -> MarketSearchResponse:
    requested = body.providers or []
    if requested:
        unknown = [k for k in requested if k not in PROVIDERS]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"unknown providers: {sorted(unknown)}",
            )
        unavailable: list[dict[str, Any]] = []
        for key in requested:
            ok, reason = PROVIDERS[key].available()
            if not ok:
                unavailable.append({"provider": key, "reason": reason})
        if unavailable:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "providers_unavailable",
                    "providers": unavailable,
                },
            )

    results, errors, has_more, total = await search_market(
        query=body.query,
        providers=requested or None,
        limit=body.limit,
        page=body.page,
        lang=body.lang,
    )
    return MarketSearchResponse(
        results=[_result_to_spec(r) for r in results],
        errors=[_error_to_spec(e) for e in errors],
        has_more=has_more,
        total=total,
    )


def _provider_info_to_spec(info: ProviderInfo) -> ProviderInfoSpec:
    return ProviderInfoSpec(
        key=info.key,
        label=info.label,
        available=info.available,
        reason=info.reason,
    )


def _result_to_spec(item: MarketResult) -> MarketResultSpec:
    return MarketResultSpec(
        source=item.source,
        slug=item.slug,
        name=item.name,
        description=item.description,
        source_url=item.source_url,
        version=item.version,
        author=item.author,
        icon_url=item.icon_url,
        stats=item.stats,
    )


def _error_to_spec(item: MarketSearchError) -> MarketSearchErrorSpec:
    return MarketSearchErrorSpec(
        provider=item.provider,
        message=item.message,
    )
