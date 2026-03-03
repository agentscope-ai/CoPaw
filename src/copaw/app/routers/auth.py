# -*- coding: utf-8 -*-
"""Authentication API endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..auth import authenticate, is_auth_enabled

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
        return {"token": "", "username": "", "message": "Auth not enabled"}

    token = authenticate(req.username, req.password)
    if token is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Invalid credentials")

    return LoginResponse(token=token, username=req.username)


@router.get("/status")
async def auth_status():
    """Check if authentication is enabled."""
    return AuthStatusResponse(enabled=is_auth_enabled())
