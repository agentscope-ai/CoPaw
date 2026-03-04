# -*- coding: utf-8 -*-
"""Pydantic data models for providers and models."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ModelInfo(BaseModel):
    id: str = Field(..., description="Model identifier used in API calls")
    name: str = Field(..., description="Human-readable model name")


class ProviderDefinition(BaseModel):
    """Static definition of a provider (built-in or custom)."""

    id: str = Field(..., description="Provider identifier")
    name: str = Field(..., description="Human-readable provider name")
    default_base_url: Optional[str] = Field(
        default=None,
        description="Default API base URL",
    )
    api_key_prefix: str = Field(
        default="",
        description="Expected prefix for the API key",
    )
    models: List[ModelInfo] = Field(
        default_factory=list,
        description="Built-in LLM model list",
    )
    is_custom: bool = Field(default=False)
    is_local: bool = Field(default=False)
    chat_model: str = Field(
        default="OpenAIChatModel",
        description="Chat model class name (e.g., 'OpenAIChatModel')",
    )

    @field_validator("default_base_url", mode="before")
    @classmethod
    def _empty_default_base_url_to_none(cls, v: object) -> object:
        return None if v == "" else v


class ProviderSettings(BaseModel):
    """Per-provider settings stored in providers.json (built-in only)."""

    base_url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    extra_models: List[ModelInfo] = Field(default_factory=list)
    chat_model: str = Field(
        default="",
        description="Chat model class name (e.g., 'OpenAIChatModel'). "
        "If empty, uses ProviderDefinition default.",
    )

    @field_validator("base_url", "api_key", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class CustomProviderData(BaseModel):
    """Persisted definition + runtime config of a user-created custom provider.

    All configuration lives here; custom providers do NOT have a
    corresponding entry in the ``providers`` dict.
    """

    id: str = Field(..., description="Provider identifier (unique)")
    name: str = Field(..., description="Human-readable provider name")
    default_base_url: Optional[str] = Field(default=None)
    api_key_prefix: str = Field(default="")
    models: List[ModelInfo] = Field(default_factory=list)
    base_url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    chat_model: str = Field(
        default="OpenAIChatModel",
        description="Chat model class name (e.g., 'OpenAIChatModel')",
    )

    @field_validator("default_base_url", "base_url", "api_key", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        return None if v == "" else v


class ModelSlotConfig(BaseModel):
    provider_id: str = Field(default="")
    model: str = Field(default="")


class ProvidersData(BaseModel):
    """Top-level structure of providers.json."""

    providers: Dict[str, ProviderSettings] = Field(default_factory=dict)
    custom_providers: Dict[str, CustomProviderData] = Field(
        default_factory=dict,
    )
    active_llm: ModelSlotConfig = Field(default_factory=ModelSlotConfig)

    def get_credentials(
        self,
        provider_id: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Return ``(base_url, api_key)`` for *provider_id*."""
        cpd = self.custom_providers.get(provider_id)
        if cpd is not None:
            return cpd.base_url or cpd.default_base_url or None, cpd.api_key
        s = self.providers.get(provider_id)
        return (s.base_url, s.api_key) if s else (None, None)

    def is_configured(self, defn: "ProviderDefinition") -> bool:
        """Determine if a provider is configured/available.

        - Local providers are always configured (no credentials needed).
        - Ollama is configured if it has base_url set.
        - Custom providers need base_url.
        - Built-in remote providers are configured if they exist in settings.
        """
        if defn.is_local:
            return True

        if defn.id == "ollama":
            s = self.providers.get(defn.id)
            return bool(s and s.base_url) if s else False

        cpd = self.custom_providers.get(defn.id)
        if cpd is not None:
            return bool(cpd.base_url or cpd.default_base_url)

        # Built-in remote providers are configured if they exist in settings
        # (they have default_base_url)
        return defn.id in self.providers


class ProviderInfo(BaseModel):
    """Provider info returned by API."""

    id: str
    name: str
    api_key_prefix: str
    models: List[ModelInfo] = Field(default_factory=list)
    extra_models: List[ModelInfo] = Field(default_factory=list)
    is_custom: bool = Field(default=False)
    is_local: bool = Field(default=False)
    needs_base_url: bool = Field(
        default=False,
        description="True when the user must supply a base URL "
        "(custom providers or providers without a default URL).",
    )
    current_api_key: Optional[str] = Field(default=None)
    current_base_url: Optional[str] = Field(default=None)


class ActiveModelsInfo(BaseModel):
    active_llm: ModelSlotConfig


class ResolvedModelConfig(BaseModel):
    model: str = Field(default="")
    base_url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    is_local: bool = Field(default=False)
