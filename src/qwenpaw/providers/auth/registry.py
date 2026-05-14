# -*- coding: utf-8 -*-
"""In-process registry for provider auth adapters."""

from __future__ import annotations

from .adapter import ProviderAuthAdapter


class ProviderAuthRegistry:
    """Small adapter registry keyed by provider id."""

    def __init__(self) -> None:
        self._adapters: dict[str, ProviderAuthAdapter] = {}

    def register(self, adapter: ProviderAuthAdapter) -> None:
        self._adapters[adapter.provider_id] = adapter

    def get(self, provider_id: str) -> ProviderAuthAdapter | None:
        return self._adapters.get(provider_id)

    def clear_for_test(self) -> None:
        self._adapters.clear()


auth_registry = ProviderAuthRegistry()
