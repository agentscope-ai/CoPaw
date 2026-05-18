# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from qwenpaw.app.goal_dispatch import (
    DEFAULT_GOAL_MAX_TURNS,
    GOAL_STATUS_ACHIEVED,
    GOAL_STATUS_ACTIVE,
    GOAL_STATUS_PAUSED,
    build_goal_continuation,
    build_goal_refresher,
    detect_active_goal,
    handle_goal_command,
    maybe_handle_goal_command,
    should_continue_goal,
    update_goal_from_message,
)


@pytest.mark.asyncio
async def test_goal_command_starts_session_goal(tmp_path):
    result = await handle_goal_command(
        "/goal Finish the retry patch and run tests",
        workspace_dir=tmp_path,
        session_id="chat:1",
        user_id="user:1",
        channel="console",
    )

    assert isinstance(result, dict)
    assert result["objective"] == "Finish the retry patch and run tests"
    assert result["status"] == GOAL_STATUS_ACTIVE

    state_path = tmp_path / "goals" / "console" / "user--1_chat--1.json"
    assert state_path.exists()
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["objective"] == "Finish the retry patch and run tests"
    assert data["max_turns"] == DEFAULT_GOAL_MAX_TURNS


@pytest.mark.asyncio
async def test_goal_status_pause_resume_clear(tmp_path):
    await handle_goal_command(
        "/goal Prepare release notes",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )

    paused = await handle_goal_command(
        "/goal pause",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )
    assert "Status: `paused`" in paused
    assert (
        detect_active_goal(
            tmp_path,
            session_id="s1",
            user_id="u1",
            channel="console",
        )
        is None
    )

    resumed = await handle_goal_command(
        "/goal resume",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )
    assert "Status: `active`" in resumed
    assert (
        detect_active_goal(
            tmp_path,
            session_id="s1",
            user_id="u1",
            channel="console",
        )
        is not None
    )

    cleared = await handle_goal_command(
        "/goal clear",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )
    assert "Goal Cleared" in cleared
    assert (
        detect_active_goal(
            tmp_path,
            session_id="s1",
            user_id="u1",
            channel="console",
        )
        is None
    )


@pytest.mark.asyncio
async def test_maybe_handle_goal_status_returns_assistant_msg(tmp_path):
    msg = await maybe_handle_goal_command(
        "/goal status",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
        agent_name="QwenPaw",
    )

    assert msg is not None
    assert msg.role == "assistant"
    assert "No goal is set" in msg.get_text_content()


def test_build_goal_refresher_rewrites_initial_command():
    refresher = build_goal_refresher(
        {
            "objective": "Ship the goal MVP",
            "_goal_path": "/tmp/goal.json",
            "_goal_started": True,
        },
        "/goal Ship the goal MVP",
    )

    assert "Objective: Ship the goal MVP" in refresher
    assert "User message:\nShip the goal MVP" in refresher
    assert "normal main-agent tools and approval flow" in refresher
    assert "Mission workers" in refresher
    assert "Goal status: paused" in refresher


@pytest.mark.asyncio
async def test_goal_in_progress_builds_auto_continuation(tmp_path):
    goal = await handle_goal_command(
        "/goal Document the feature",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )
    assert isinstance(goal, dict)

    updated = update_goal_from_message(
        goal,
        {"content": "I inspected the files and still need to write docs."},
    )

    assert updated is not None
    assert updated["status"] == GOAL_STATUS_ACTIVE
    assert should_continue_goal(updated)

    continuation = build_goal_continuation(updated)
    assert "[Goal continuation]" in continuation
    assert "Objective: Document the feature" in continuation
    assert "Turn budget: 1/5 completed" in continuation
    assert "Previous response excerpt" in continuation

    state_path = tmp_path / "goals" / "console" / "u1_s1.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert "_goal_path" not in data


@pytest.mark.asyncio
async def test_goal_auto_pauses_when_turn_budget_is_exhausted(tmp_path):
    goal = await handle_goal_command(
        "/goal Document the feature",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )
    assert isinstance(goal, dict)

    updated = goal
    for _ in range(DEFAULT_GOAL_MAX_TURNS):
        updated = update_goal_from_message(
            updated,
            {"content": "Still working."},
        )

    assert updated is not None
    assert updated["status"] == GOAL_STATUS_PAUSED
    assert updated["last_result"] == "turn_budget_exhausted"
    assert not should_continue_goal(updated)


@pytest.mark.asyncio
async def test_goal_can_pause_when_model_needs_user_input(tmp_path):
    goal = await handle_goal_command(
        "/goal Choose a deployment target",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )
    assert isinstance(goal, dict)

    paused_text = "I need you to pick staging or prod.\nGoal status: paused"
    updated = update_goal_from_message(
        goal,
        {"content": paused_text},
    )

    assert updated is not None
    assert updated["status"] == GOAL_STATUS_PAUSED
    assert updated["last_result"] == "paused"
    assert not should_continue_goal(updated)


@pytest.mark.asyncio
async def test_update_goal_from_message_marks_achieved(tmp_path):
    goal = await handle_goal_command(
        "/goal Document the feature",
        workspace_dir=tmp_path,
        session_id="s1",
        user_id="u1",
        channel="console",
    )
    assert isinstance(goal, dict)

    update_goal_from_message(
        goal,
        {"content": "Done.\n\nGoal status: achieved"},
    )

    state_path = tmp_path / "goals" / "console" / "u1_s1.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["status"] == GOAL_STATUS_ACHIEVED
    assert data["attempts"] == 1
