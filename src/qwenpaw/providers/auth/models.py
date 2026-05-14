# -*- coding: utf-8 -*-
"""Shared models for provider authentication flows."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProviderAuthType(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    OAUTH_DEVICE_CODE = "oauth_device_code"
    OAUTH_AUTHORIZATION_CODE = "oauth_authorization_code"
    OAUTH_VENDOR_USER_CODE = "oauth_vendor_user_code"


class ProviderAuthStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    NOT_CONFIGURED = "not_configured"
    PENDING = "pending"
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    ERROR = "error"


class ProviderAuthFlowType(str, Enum):
    DEVICE_CODE = "device_code"
    AUTHORIZATION_CODE = "authorization_code"
    VENDOR_USER_CODE = "vendor_user_code"


class ProviderAuthInfo(BaseModel):
    type: ProviderAuthType = ProviderAuthType.API_KEY
    status: ProviderAuthStatus = ProviderAuthStatus.NOT_CONFIGURED
    account_label: str = ""
    expires_at: int | None = None
    scopes: list[str] = Field(default_factory=list)
    supports_logout: bool = False
    message: str = ""


class AuthStartRequest(BaseModel):
    redirect_uri: str | None = Field(
        default=None,
        description=(
            "Optional OAuth callback URI. API routes must validate this "
            "against the configured callback endpoint before adapters use it."
        ),
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Provider-specific non-sensitive flow metadata. Adapters must "
            "validate any keys they consume."
        ),
    )


class AuthStartResult(BaseModel):
    flow_id: str
    flow_type: ProviderAuthFlowType
    user_code: str | None = None
    verification_uri: str | None = None
    authorization_url: str | None = None
    expires_at: int | None = None
    interval: int | None = None
    message: str = ""


class AuthStatusResult(BaseModel):
    status: ProviderAuthStatus
    account_label: str = ""
    expires_at: int | None = None
    scopes: list[str] = Field(default_factory=list)
    message: str = ""


class OAuthCredential(BaseModel):
    provider_id: str
    token_type: str = "Bearer"
    access_token: str = ""
    refresh_token: str = ""
    id_token: str = ""
    client_secret: str = ""
    account_label: str = ""
    expires_at: int | None = None
    scopes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: int
    updated_at: int
