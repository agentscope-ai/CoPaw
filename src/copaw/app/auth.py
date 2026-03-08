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
    },
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


def _hash_password(
    password: str,
    salt: Optional[str] = None,
) -> tuple[str, str]:
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
        },
    )
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(
        secret.encode(),
        payload_b64.encode(),
        hashlib.sha256,
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
            secret.encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("sub")
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
        logger.debug("Token verification failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Auth data persistence (auth.json in WORKING_DIR)
# ---------------------------------------------------------------------------


def _load_auth_data() -> dict:
    """Load auth.json from WORKING_DIR.

    Returns the parsed dict, or a sentinel with ``_auth_load_error``
    set to ``True`` when the file exists but cannot be read/parsed so
    that callers can fail closed instead of silently bypassing auth.
    """
    if AUTH_FILE.is_file():
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load auth file %s: %s", AUTH_FILE, exc)
            return {"_auth_load_error": True}
    return {}


def _save_auth_data(data: dict) -> None:
    """Save auth.json to WORKING_DIR with restrictive permissions."""
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    try:
        os.chmod(AUTH_FILE, 0o600)
    except OSError:
        pass


def is_auth_enabled() -> bool:
    """Check if authentication is configured.

    Returns ``True`` when credentials are present **or** when the auth
    file cannot be read (fail closed) to avoid silently bypassing auth.
    """
    data = _load_auth_data()
    if data.get("_auth_load_error"):
        return True  # fail closed
    return bool(data.get("password_hash"))


def init_auth_from_env() -> None:
    """Initialize auth from ADMIN_USERNAME / ADMIN_PASSWORD env vars.

    Called at startup.  Auth is only enabled when ADMIN_PASSWORD is
    explicitly set in the environment (non-empty).  If the env var is
    absent or blank, initialization is skipped and any existing
    auth.json is left untouched (auth remains in whatever state it
    was previously — enabled credentials stay enabled, empty file
    stays unauthenticated).
    """
    raw_password = os.environ.get("ADMIN_PASSWORD", "")
    raw_username = os.environ.get("ADMIN_USERNAME", "")

    password = raw_password.strip()
    username = raw_username.strip() or "admin"

    if not password:
        logger.debug(
            "ADMIN_PASSWORD not set; skipping auth initialization",
        )
        return

    data = _load_auth_data()
    existing_hash = data.get("password_hash", "")
    existing_salt = data.get("password_salt", "")
    existing_user = data.get("username", "")

    if (
        existing_hash
        and existing_salt
        and existing_user == username
        and verify_password(password, existing_hash, existing_salt)
    ):
        logger.debug("Auth credentials unchanged, skipping update")
        return

    pw_hash, salt = _hash_password(password)
    data["username"] = username
    data["password_hash"] = pw_hash
    data["password_salt"] = salt
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

    async def dispatch(  # pylint: disable=too-many-return-statements
        self,
        request: Request,
        call_next,
    ) -> Response:
        """Check Bearer token on protected API routes; skip public paths."""
        path = request.url.path

        if not is_auth_enabled():
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        if path in _PUBLIC_PATHS:
            return await call_next(request)

        if any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            return await call_next(request)

        if not path.startswith("/api/"):
            return await call_next(request)

        token: Optional[str] = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        elif "upgrade" in request.headers.get("connection", "").lower():
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

        request.state.user = user
        return await call_next(request)
