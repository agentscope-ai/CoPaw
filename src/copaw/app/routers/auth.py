# -*- coding: utf-8 -*-
"""Authentication API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..auth import authenticate, is_auth_enabled, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


class AuthStatusResponse(BaseModel):
    enabled: bool


@router.post("/login")
async def login(req: LoginRequest):
    """Authenticate with username and password."""
    if not is_auth_enabled():
        return LoginResponse(token="", username="")

    token = authenticate(req.username, req.password)
    if token is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Invalid credentials")

    return LoginResponse(token=token, username=req.username)


@router.get("/status")
async def auth_status():
    """Check if authentication is enabled."""
    return AuthStatusResponse(enabled=is_auth_enabled())


@router.get("/verify")
async def verify(request: Request):
    """Verify that the caller's Bearer token is still valid."""
    if not is_auth_enabled():
        return {"valid": True, "username": ""}

    from fastapi import HTTPException

    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    username = verify_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"valid": True, "username": username}
