# -*- coding: utf-8 -*-
"""QwenPaw plugin HTTP routes."""

from __future__ import annotations

import json
import mimetypes
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, model_validator

from emitter import (
    desktop_health,
    emit_pet_event,
    start_desktop_interactive,
    switch_pet_desktop,
)
from pet_paths import list_installed_pets, pets_install_dir


class SwitchPetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pet_dir: str | None = None
    pet_id: str | None = None

    @model_validator(mode="after")
    def _one_target(self) -> SwitchPetRequest:
        d = (self.pet_dir or "").strip()
        i = (self.pet_id or "").strip()
        if bool(d) == bool(i):
            raise ValueError("provide exactly one of pet_dir or pet_id")
        return self


class EmitPayload(BaseModel):
    event: str
    text: str | None = None
    state: str | None = None
    duration_ms: int | None = None


_SAFE_PET_FOLDER = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")


def _resolved_pet_spritesheet_path(folder: str) -> Path:
    """Return spritesheet path for ``pets/<folder>`` or raise HTTPException."""
    if not _SAFE_PET_FOLDER.fullmatch(folder):
        raise HTTPException(status_code=400, detail="invalid pet folder name")
    root = pets_install_dir().resolve()
    pet_dir = (root / folder).resolve()
    try:
        pet_dir.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="pet not found") from exc
    if not pet_dir.is_dir():
        raise HTTPException(status_code=404, detail="pet not found")
    manifest_path = pet_dir / "pet.json"
    if not manifest_path.is_file():
        raise HTTPException(status_code=404, detail="missing pet.json")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="invalid pet.json",
        ) from exc
    rel = data.get("spritesheetPath")
    if not isinstance(rel, str) or not rel.strip():
        raise HTTPException(status_code=404, detail="missing spritesheetPath")
    sheet = (pet_dir / rel).resolve()
    try:
        sheet.relative_to(pet_dir)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="invalid spritesheet path",
        ) from exc
    if not sheet.is_file():
        raise HTTPException(status_code=404, detail="spritesheet file missing")
    return sheet


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/status")
    def status():
        return {
            "ok": True,
            "plugin": "qwenpaw-pet",
            "desktop": desktop_health(),
        }

    @router.get("/pets")
    def list_pets():
        return {
            "ok": True,
            "petsDir": str(pets_install_dir()),
            "pets": list_installed_pets(),
        }

    @router.get("/pets/{folder}/spritesheet")
    def pet_spritesheet(folder: str):
        """Serve the raw spritesheet image for console previews.

        Auth via the QwenPaw API.
        """
        sheet = _resolved_pet_spritesheet_path(folder)
        media_type, _ = mimetypes.guess_type(str(sheet))
        if not media_type:
            media_type = "application/octet-stream"
        return FileResponse(sheet, media_type=media_type)

    @router.post("/desktop/start")
    def desktop_start():
        return start_desktop_interactive()

    @router.post("/emit-test")
    def emit_test(payload: EmitPayload):
        emit_pet_event(
            payload.event,
            text=payload.text,
            state=payload.state,
            duration_ms=payload.duration_ms,
            manual=True,
        )
        return {"ok": True}

    @router.post("/switch-pet")
    def switch_pet_route(payload: SwitchPetRequest):
        return switch_pet_desktop(
            pet_dir=payload.pet_dir,
            pet_id=payload.pet_id,
        )

    return router
