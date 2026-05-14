# -*- coding: utf-8 -*-
"""Provider authentication adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .models import (
    AuthStartRequest,
    AuthStartResult,
    AuthStatusResult,
    OAuthCredential,
    ProviderAuthStatus,
    ProviderAuthType,
)

if TYPE_CHECKING:
    from ..provider import Provider


class ProviderAuthAdapter(ABC):
    """Provider-specific implementation of an OAuth-style auth flow."""

    provider_id: str
    auth_type: ProviderAuthType

    @abstractmethod
    async def start(
        self,
        provider: Provider,
        request: AuthStartRequest,
    ) -> AuthStartResult:
        """Start an authentication flow."""

    async def poll(
        self,
        provider: Provider,  # pylint: disable=unused-argument
        flow_id: str,  # pylint: disable=unused-argument
    ) -> AuthStatusResult:
        """Poll an in-progress auth flow."""
        return AuthStatusResult(
            status=ProviderAuthStatus.ERROR,
            message="Polling is not supported for this auth flow",
        )

    async def handle_callback(
        self,
        provider: Provider,
        state: str,
        code: str,
    ) -> OAuthCredential:
        """Exchange callback data for an OAuth credential."""
        raise NotImplementedError

    async def refresh(
        self,
        provider: Provider,  # pylint: disable=unused-argument
        credential: OAuthCredential,
    ) -> OAuthCredential:
        """Refresh a stored credential if the provider supports it."""
        return credential

    async def logout(
        self,
        provider: Provider,  # pylint: disable=unused-argument
        credential: OAuthCredential | None,  # pylint: disable=unused-argument
    ) -> None:
        """Revoke or invalidate credentials with the remote provider."""
        return None

    async def get_status(
        self,
        provider: Provider,  # pylint: disable=unused-argument
        credential: OAuthCredential | None,
    ) -> AuthStatusResult:
        """Return safe auth status metadata for frontend display."""
        if credential and credential.access_token:
            return AuthStatusResult(
                status=ProviderAuthStatus.AUTHENTICATED,
                account_label=credential.account_label,
                expires_at=credential.expires_at,
                scopes=credential.scopes,
            )
        return AuthStatusResult(status=ProviderAuthStatus.NOT_CONFIGURED)
