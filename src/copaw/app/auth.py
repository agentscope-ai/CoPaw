# -*- coding: utf-8 -*-
"""Authentication module: password hashing, JWT tokens, and FastAPI middleware.

Uses only Python stdlib (hashlib, hmac, secrets) to avoid adding new
dependencies. Passwords are stored as salted SHA-256 hashes.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..constant import WORKING_DIR

logger = logging.getLogger(__name__)

AUTH_FILE = WORKING_DIR / "auth.json"

# JWT-like token validity: 7 days
TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600

# Paths that do NOT require authentication
_PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/api/auth/login",
        "/api/auth/status",
        "/api/version",
    }
)

# Prefixes that do NOT require authentication (static assets)
_PUBLIC_PREFIXES: tuple[str, ...] = (
    "/assets/",
    "/logo.png",
    "/copaw-symbol.svg",
)


# ---------------------------------------------------------------------------
# Password hashing (salted SHA-256, no external deps)
# ---------------------------------------------------------------------------

def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password with salt. Returns (hash_hex, salt_hex)."""
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return h, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash."""
    h, _ = _hash_password(password, salt)
    return hmac.compare_digest(h, stored_hash)


# ---------------------------------------------------------------------------
# Token generation / verification (HMAC-SHA256 based, no PyJWT needed)
# ---------------------------------------------------------------------------

def _get_jwt_secret() -> str:
    """Get JWT secret from auth.json, or generate one."""
    data = _load_auth_data()
    secret = data.get("jwt_secret", "")
    if not secret:
        secret = secrets.token_hex(32)
        data["jwt_secret"] = secret
        _save_auth_data(data)
    return secret


def create_token(username: str) -> str:
    """Create a simple HMAC-signed token: base64(payload).signature."""
    import base64

    secret = _get_jwt_secret()
    payload = json.dumps(
        {
            "sub": username,
            "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
            "iat": int(time.time()),
        }
    )
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(
        secret.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_token(token: str) -> Optional[str]:
    """Verify token, return username if valid, None otherwise."""
    import base64

    try:
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        secret = _get_jwt_secret()
        expected_sig = hmac.new(
            secret.encode(), payload_b64.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("sub")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Auth data persistence (auth.json in WORKING_DIR)
# ---------------------------------------------------------------------------

def _load_auth_data() -> dict:
    """Load auth.json from WORKING_DIR."""
    if AUTH_FILE.is_file():
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_auth_data(data: dict) -> None:
    """Save auth.json to WORKING_DIR."""
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_auth_enabled() -> bool:
    """Check if authentication is configured."""
    data = _load_auth_data()
    return bool(data.get("password_hash"))


def init_auth_from_env() -> None:
    """Initialize auth from ADMIN_USERNAME / ADMIN_PASSWORD env vars.

    Called at startup. If env vars are set and auth.json doesn't have
    credentials yet (or password changed), update auth.json.
    """
    username = os.environ.get("ADMIN_USERNAME", "admin").strip()
    password = os.environ.get("ADMIN_PASSWORD", "copaw").strip()

    if not username:
        username = "admin"

    data = _load_auth_data()
    # Check if we need to update
    existing_hash = data.get("password_hash", "")
    existing_salt = data.get("password_salt", "")
    existing_user = data.get("username", "")

    # If credentials already match, skip
    if (
        existing_hash
        and existing_salt
        and existing_user == username
        and verify_password(password, existing_hash, existing_salt)
    ):
        logger.debug("Auth credentials unchanged, skipping update")
        return

    # Hash and store
    pw_hash, salt = _hash_password(password)
    data["username"] = username
    data["password_hash"] = pw_hash
    data["password_salt"] = salt
    if "jwt_secret" not in data:
        data["jwt_secret"] = secrets.token_hex(32)

    _save_auth_data(data)
    logger.info("Auth credentials initialized from environment variables")


def authenticate(username: str, password: str) -> Optional[str]:
    """Authenticate user. Returns JWT token if valid, None otherwise."""
    data = _load_auth_data()
    stored_user = data.get("username", "")
    stored_hash = data.get("password_hash", "")
    stored_salt = data.get("password_salt", "")

    if not stored_hash or not stored_salt:
        return None

    if username != stored_user:
        return None

    if not verify_password(password, stored_hash, stored_salt):
        return None

    return create_token(username)


# ---------------------------------------------------------------------------
# FastAPI middleware
# ---------------------------------------------------------------------------

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that checks Bearer token on protected routes."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Skip auth check if auth is not configured
        if not is_auth_enabled():
            return await call_next(request)

        # Public paths don't need auth
        if path in _PUBLIC_PATHS:
            return await call_next(request)

        # Static assets don't need auth
        for prefix in _PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # SPA HTML pages: let them through (frontend handles redirect)
        if not path.startswith("/api/"):
            return await call_next(request)

        # Try Authorization header first, then fall back to query param
        # (WebSocket connections can't set custom headers from browser)
        token: Optional[str] = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = request.query_params.get("token")

        if not token:
            return Response(
                content=json.dumps({"detail": "Not authenticated"}),
                status_code=401,
                media_type="application/json",
            )

        user = verify_token(token)
        if user is None:
            return Response(
                content=json.dumps({"detail": "Invalid or expired token"}),
                status_code=401,
                media_type="application/json",
            )

        # Attach user to request state
        request.state.user = user
        return await call_next(request)
