# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copaw.app.routers import skills as skills_router_module


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(skills_router_module.router)
    return TestClient(app)


def test_install_from_hub_returns_conflict_for_existing_skill(
    monkeypatch,
) -> None:
    def _raise_exists(**_kwargs):
        raise FileExistsError(
            "Skill 'find-skills' already exists. "
            "Use overwrite=true to replace.",
        )

    monkeypatch.setattr(
        skills_router_module,
        "install_skill_from_hub",
        _raise_exists,
    )

    client = _build_client()
    response = client.post(
        "/skills/hub/install",
        json={
            "bundle_url": "https://skills.sh/vercel-labs/skills/find-skills",
            "enable": True,
            "overwrite": False,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Skill 'find-skills' already exists. "
            "Use overwrite=true to replace."
        ),
    }


def test_install_from_hub_returns_bad_request_for_invalid_url() -> None:
    client = _build_client()
    response = client.post(
        "/skills/hub/install",
        json={
            "bundle_url": "not-a-url",
            "enable": True,
            "overwrite": False,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "bundle_url must be a valid http(s) URL",
    }
