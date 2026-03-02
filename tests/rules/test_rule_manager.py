# -*- coding: utf-8 -*-
"""Tests for RuleManager and RuleSpec."""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from copaw.agents.rules import RuleManager, RuleScope, RuleSpec


@pytest.fixture
def temp_rules_dir():
    """Create a temporary directory for rule tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def rule_manager(temp_rules_dir):
    """Create a RuleManager with temporary storage."""
    manager = RuleManager(save_dir=temp_rules_dir)
    return manager


@pytest.mark.asyncio
async def test_add_rule_global(rule_manager):
    """Test adding a global rule."""
    rule = await rule_manager.add_rule(
        content="Always respond in Chinese",
        scope=RuleScope.GLOBAL,
        priority=10,
    )

    assert rule.content == "Always respond in Chinese"
    assert rule.scope == RuleScope.GLOBAL
    assert rule.priority == 10
    assert rule.enabled is True
    assert rule.id is not None

    # Verify it was saved
    loaded_rule = await rule_manager.get_rule(rule.id)
    assert loaded_rule is not None
    assert loaded_rule.content == "Always respond in Chinese"


@pytest.mark.asyncio
async def test_add_rule_channel(rule_manager):
    """Test adding a channel-specific rule."""
    rule = await rule_manager.add_rule(
        content="Use formal language in DingTalk",
        scope=RuleScope.CHANNEL,
        channel="dingtalk",
        priority=5,
    )

    assert rule.scope == RuleScope.CHANNEL
    assert rule.channel == "dingtalk"
    assert rule.content == "Use formal language in DingTalk"


@pytest.mark.asyncio
async def test_add_rule_user(rule_manager):
    """Test adding a user-specific rule."""
    rule = await rule_manager.add_rule(
        content="Use technical terms for this user",
        scope=RuleScope.USER,
        user_id="user123",
    )

    assert rule.scope == RuleScope.USER
    assert rule.user_id == "user123"


@pytest.mark.asyncio
async def test_add_rule_session(rule_manager):
    """Test adding a session-specific rule."""
    rule = await rule_manager.add_rule(
        content="Be concise in this session",
        scope=RuleScope.SESSION,
        session_id="session456",
    )

    assert rule.scope == RuleScope.SESSION
    assert rule.session_id == "session456"


@pytest.mark.asyncio
async def test_add_rule_validation(rule_manager):
    """Test validation when adding rules."""
    # CHANNEL scope requires channel
    with pytest.raises(ValueError, match="channel is required"):
        await rule_manager.add_rule(
            content="Test",
            scope=RuleScope.CHANNEL,
        )

    # USER scope requires user_id
    with pytest.raises(ValueError, match="user_id is required"):
        await rule_manager.add_rule(
            content="Test",
            scope=RuleScope.USER,
        )

    # SESSION scope requires session_id
    with pytest.raises(ValueError, match="session_id is required"):
        await rule_manager.add_rule(
            content="Test",
            scope=RuleScope.SESSION,
        )


@pytest.mark.asyncio
async def test_remove_rule(rule_manager):
    """Test removing a rule."""
    rule = await rule_manager.add_rule(
        content="To be removed",
        scope=RuleScope.GLOBAL,
    )

    # Remove it
    removed = await rule_manager.remove_rule(rule.id)
    assert removed is True

    # Verify it's gone
    loaded_rule = await rule_manager.get_rule(rule.id)
    assert loaded_rule is None

    # Removing non-existent rule returns False
    result = await rule_manager.remove_rule("non-existent-id")
    assert result is False


@pytest.mark.asyncio
async def test_update_rule(rule_manager):
    """Test updating a rule."""
    rule = await rule_manager.add_rule(
        content="Original content",
        scope=RuleScope.GLOBAL,
        priority=5,
        enabled=True,
    )

    # Update content and priority
    updated = await rule_manager.update_rule(
        rule.id,
        content="Updated content",
        priority=10,
    )

    assert updated is not None
    assert updated.content == "Updated content"
    assert updated.priority == 10

    # Update enabled status
    updated = await rule_manager.update_rule(
        rule.id,
        enabled=False,
    )
    assert updated is not None
    assert updated.enabled is False


@pytest.mark.asyncio
async def test_enable_disable_rule(rule_manager):
    """Test enabling and disabling rules."""
    rule = await rule_manager.add_rule(
        content="Test rule",
        scope=RuleScope.GLOBAL,
        enabled=True,
    )

    # Disable it
    result = await rule_manager.disable_rule(rule.id)
    assert result is True

    loaded_rule = await rule_manager.get_rule(rule.id)
    assert loaded_rule.enabled is False

    # Enable it again
    result = await rule_manager.enable_rule(rule.id)
    assert result is True

    loaded_rule = await rule_manager.get_rule(rule.id)
    assert loaded_rule.enabled is True


@pytest.mark.asyncio
async def test_list_rules(rule_manager):
    """Test listing rules with filters."""
    # Add multiple rules
    await rule_manager.add_rule(
        content="Global rule 1",
        scope=RuleScope.GLOBAL,
    )
    await rule_manager.add_rule(
        content="Global rule 2",
        scope=RuleScope.GLOBAL,
    )
    await rule_manager.add_rule(
        content="Channel rule",
        scope=RuleScope.CHANNEL,
        channel="dingtalk",
    )

    # List all
    all_rules = await rule_manager.list_rules()
    assert len(all_rules) == 3

    # List only GLOBAL
    global_rules = await rule_manager.list_rules(scope=RuleScope.GLOBAL)
    assert len(global_rules) == 2

    # Add a disabled rule
    disabled_rule = await rule_manager.add_rule(
        content="Disabled rule",
        scope=RuleScope.GLOBAL,
        enabled=False,
    )

    # enabled_only=True should exclude it (3 enabled rules)
    enabled_rules = await rule_manager.list_rules(enabled_only=True)
    assert len(enabled_rules) == 3

    # enabled_only=False should include it (4 total rules)
    all_with_disabled = await rule_manager.list_rules(enabled_only=False)
    assert len(all_with_disabled) == 4


@pytest.mark.asyncio
async def test_get_active_rules(rule_manager):
    """Test getting active rules for a context."""
    # Add rules with different scopes
    await rule_manager.add_rule(
        content="Global rule",
        scope=RuleScope.GLOBAL,
        priority=1,
    )
    await rule_manager.add_rule(
        content="DingTalk rule",
        scope=RuleScope.CHANNEL,
        channel="dingtalk",
        priority=5,
    )
    await rule_manager.add_rule(
        content="User rule",
        scope=RuleScope.USER,
        user_id="user123",
        priority=10,
    )
    await rule_manager.add_rule(
        content="Other channel rule",
        scope=RuleScope.CHANNEL,
        channel="feishu",
        priority=3,
    )

    # Get rules for dingtalk/user123
    active_rules = await rule_manager.get_active_rules(
        channel="dingtalk",
        user_id="user123",
        session_id="session1",
    )

    # Should get 3 rules (global + dingtalk + user)
    assert len(active_rules) == 3

    # Check priority ordering (highest first)
    assert active_rules[0].priority == 10  # User rule
    assert active_rules[1].priority == 5   # DingTalk rule
    assert active_rules[0].content == "User rule"
    assert active_rules[1].content == "DingTalk rule"
    assert active_rules[2].content == "Global rule"

    # Get rules for feishu/other-user
    active_rules = await rule_manager.get_active_rules(
        channel="feishu",
        user_id="other-user",
        session_id="session2",
    )

    # Should get 2 rules (global + feishu)
    assert len(active_rules) == 2
    assert active_rules[0].content == "Other channel rule"
    assert active_rules[1].content == "Global rule"


@pytest.mark.asyncio
async def test_rule_is_applicable_to():
    """Test RuleSpec.is_applicable_to method."""
    # Global rule
    global_rule = RuleSpec(
        content="Global",
        scope=RuleScope.GLOBAL,
    )
    assert global_rule.is_applicable_to(
        channel="dingtalk",
        user_id="user1",
        session_id="session1",
    ) is True

    # Disabled rule should not apply
    disabled_rule = RuleSpec(
        content="Disabled",
        scope=RuleScope.GLOBAL,
        enabled=False,
    )
    assert disabled_rule.is_applicable_to() is False

    # Channel-specific rule
    channel_rule = RuleSpec(
        content="Channel",
        scope=RuleScope.CHANNEL,
        channel="dingtalk",
    )
    assert channel_rule.is_applicable_to(channel="dingtalk") is True
    assert channel_rule.is_applicable_to(channel="feishu") is False

    # User-specific rule
    user_rule = RuleSpec(
        content="User",
        scope=RuleScope.USER,
        user_id="user123",
    )
    assert user_rule.is_applicable_to(user_id="user123") is True
    assert user_rule.is_applicable_to(user_id="user456") is False

    # Session-specific rule
    session_rule = RuleSpec(
        content="Session",
        scope=RuleScope.SESSION,
        session_id="session1",
    )
    assert session_rule.is_applicable_to(session_id="session1") is True
    assert session_rule.is_applicable_to(session_id="session2") is False


@pytest.mark.asyncio
async def test_persistence(rule_manager, temp_rules_dir):
    """Test rules are persisted to disk."""
    # Add a rule
    rule = await rule_manager.add_rule(
        content="Persistent rule",
        scope=RuleScope.GLOBAL,
        priority=7,
    )

    # Verify file exists
    rules_file = Path(temp_rules_dir) / "rules.json"
    assert rules_file.exists()

    # Create a new manager and load
    new_manager = RuleManager(save_dir=temp_rules_dir)
    await new_manager.load()

    # Verify rule was loaded
    loaded_rule = await new_manager.get_rule(rule.id)
    assert loaded_rule is not None
    assert loaded_rule.content == "Persistent rule"
    assert loaded_rule.priority == 7


@pytest.mark.asyncio
async def test_load_nonexistent_file(rule_manager):
    """Test loading when rules file doesn't exist."""
    # Should not raise, just start with empty rules
    await rule_manager.load()
    rules = await rule_manager.list_rules()
    assert len(rules) == 0


@pytest.mark.asyncio
async def test_clear_all_rules(rule_manager):
    """Test clearing all rules."""
    # Add multiple rules
    await rule_manager.add_rule(content="Rule 1", scope=RuleScope.GLOBAL)
    await rule_manager.add_rule(content="Rule 2", scope=RuleScope.GLOBAL)
    await rule_manager.add_rule(content="Rule 3", scope=RuleScope.GLOBAL)

    # Clear all
    await rule_manager.clear_all()

    # Verify all are gone
    rules = await rule_manager.list_rules()
    assert len(rules) == 0


@pytest.mark.asyncio
async def test_reinforce_rule(rule_manager):
    """Test reinforcing a rule (updating reinforced_at)."""
    rule = await rule_manager.add_rule(
        content="Test rule",
        scope=RuleScope.GLOBAL,
    )

    # Initial reinforced_at should be None
    assert rule.reinforced_at is None

    # Reinforce it
    await asyncio.sleep(0.01)  # Small delay to ensure timestamp difference
    result = await rule_manager.reinforce_rule(rule.id)
    assert result is True

    # Verify reinforced_at was updated
    updated_rule = await rule_manager.get_rule(rule.id)
    assert updated_rule.reinforced_at is not None
    assert isinstance(updated_rule.reinforced_at, datetime)


@pytest.mark.asyncio
async def test_reinforce_nonexistent_rule(rule_manager):
    """Test reinforcing a nonexistent rule."""
    result = await rule_manager.reinforce_rule("nonexistent-id")
    assert result is False


@pytest.mark.asyncio
async def test_update_nonexistent_rule(rule_manager):
    """Test updating a nonexistent rule."""
    result = await rule_manager.update_rule(
        "nonexistent-id",
        content="New content",
    )
    assert result is None


@pytest.mark.asyncio
async def test_atomic_write(rule_manager, temp_rules_dir):
    """Test that rules are written atomically."""
    rules_file = Path(temp_rules_dir) / "rules.json"

    # Add multiple rules concurrently
    tasks = [
        rule_manager.add_rule(
            content=f"Rule {i}",
            scope=RuleScope.GLOBAL,
        )
        for i in range(10)
    ]
    await asyncio.gather(*tasks)

    # Verify file is valid JSON (not corrupted)
    assert rules_file.exists()
    data = json.loads(rules_file.read_text())
    assert len(data["rules"]) == 10


# Import json for the atomic write test
import json
