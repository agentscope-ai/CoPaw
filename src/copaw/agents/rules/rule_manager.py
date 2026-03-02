# -*- coding: utf-8 -*-
"""Rule Manager for CoPaw.

This module provides rule management capabilities for CoPaw, allowing
users to define persistent rules that guide agent behavior.

Features:
- Create, read, update, delete rules
- Scope-based rule application (global, channel, user, session)
- Priority-based rule ordering
- Persistent storage with JSON backend
- Automatic rule injection into system prompt

Example:
    >>> from copaw.agents.rules import RuleManager, RuleScope
    >>>
    >>> manager = RuleManager()
    >>> await manager.load()
    >>>
    >>> # Add a global rule
    >>> rule = await manager.add_rule(
    ...     content="Always respond in Chinese",
    ...     scope=RuleScope.GLOBAL,
    ...     priority=10,
    ... )
    >>>
    >>> # Get rules applicable to a context
    >>> rules = await manager.get_active_rules(
    ...     channel="dingtalk",
    ...     user_id="user123",
    ... )
"""
import json
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from .models import RuleSpec, RuleScope

__all__ = ["RuleManager"]


class RuleManager:
    """Rule manager for persistent rule storage and retrieval.

    This manager handles:
    - Rule CRUD operations
    - Scope-based rule filtering
    - Priority-based ordering
    - JSON file persistence

    Attributes:
        save_dir: Directory where rules are stored
        rules_file: Path to the rules.json file
    """

    def __init__(self, save_dir: str = "~/.copaw/rules"):
        """Initialize RuleManager.

        Args:
            save_dir: Directory to store rule files
        """
        self.save_dir = Path(save_dir).expanduser()
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self._rules: dict[str, RuleSpec] = {}
        self._lock = asyncio.Lock()
        self._rules_file = self.save_dir / "rules.json"

    @property
    def rules_file(self) -> Path:
        """Get the rules file path."""
        return self._rules_file

    async def load(self) -> None:
        """Load rules from disk.

        Reads rules.json and populates the in-memory rule cache.
        If the file doesn't exist, starts with an empty rule set.
        """
        async with self._lock:
            if not self._rules_file.exists():
                return

            try:
                data = json.loads(self._rules_file.read_text(encoding="utf-8"))
                for rule_data in data.get("rules", []):
                    rule = RuleSpec(**rule_data)
                    self._rules[rule.id] = rule
            except (json.JSONDecodeError, KeyError) as e:
                # Log error but continue with empty rules
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to load rules: {e}")

    async def save(self) -> None:
        """Save rules to disk.

        Persists all rules to rules.json atomically.
        Uses write-to-temp-then-rename pattern for safety.
        """
        async with self._lock:
            await self._persist()

    async def add_rule(
        self,
        content: str,
        scope: RuleScope = RuleScope.GLOBAL,
        channel: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        priority: int = 0,
        enabled: bool = True,
    ) -> RuleSpec:
        """Add a new rule.

        Args:
            content: The rule content/description
            scope: Rule application scope
            channel: Channel name (for CHANNEL scope)
            user_id: User ID (for USER scope)
            session_id: Session ID (for SESSION scope)
            priority: Rule priority (higher = more important)
            enabled: Whether the rule is initially enabled

        Returns:
            The created RuleSpec

        Raises:
            ValueError: If scope-channel/user_id/session_id mismatch
        """
        # Validate scope-specific fields
        if scope == RuleScope.CHANNEL and not channel:
            raise ValueError("channel is required for CHANNEL scope")
        if scope == RuleScope.USER and not user_id:
            raise ValueError("user_id is required for USER scope")
        if scope == RuleScope.SESSION and not session_id:
            raise ValueError("session_id is required for SESSION scope")

        rule = RuleSpec(
            content=content,
            scope=scope,
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            priority=priority,
            enabled=enabled,
        )

        async with self._lock:
            self._rules[rule.id] = rule
            await self._persist()

        return rule

    async def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID.

        Args:
            rule_id: The rule ID to remove

        Returns:
            True if the rule was removed, False if not found
        """
        async with self._lock:
            if rule_id not in self._rules:
                return False
            del self._rules[rule_id]
            await self._persist()
            return True

    async def update_rule(
        self,
        rule_id: str,
        content: Optional[str] = None,
        priority: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[RuleSpec]:
        """Update an existing rule.

        Args:
            rule_id: The rule ID to update
            content: New content (optional)
            priority: New priority (optional)
            enabled: New enabled status (optional)

        Returns:
            The updated RuleSpec, or None if not found
        """
        async with self._lock:
            if rule_id not in self._rules:
                return None

            rule = self._rules[rule_id]
            if content is not None:
                rule.content = content
            if priority is not None:
                rule.priority = priority
            if enabled is not None:
                rule.enabled = enabled

            await self._persist()
            return rule

    async def get_rule(self, rule_id: str) -> Optional[RuleSpec]:
        """Get a rule by ID.

        Args:
            rule_id: The rule ID to get

        Returns:
            The RuleSpec, or None if not found
        """
        async with self._lock:
            return self._rules.get(rule_id)

    async def list_rules(
        self,
        scope: Optional[RuleScope] = None,
        enabled_only: bool = True,
    ) -> list[RuleSpec]:
        """List all rules with optional filtering.

        Args:
            scope: Filter by scope (optional)
            enabled_only: If True, only return enabled rules

        Returns:
            List of matching RuleSpecs
        """
        async with self._lock:
            rules = []
            for rule in self._rules.values():
                if enabled_only and not rule.enabled:
                    continue
                if scope is not None and rule.scope != scope:
                    continue
                rules.append(rule)
            return rules

    async def get_active_rules(
        self,
        channel: str,
        user_id: str,
        session_id: str,
    ) -> list[RuleSpec]:
        """Get rules applicable to the given context.

        Rules are filtered by scope and sorted by priority (highest first).

        Args:
            channel: Channel name
            user_id: User identifier
            session_id: Session identifier

        Returns:
            List of applicable RuleSpecs, sorted by priority (descending)
        """
        async with self._lock:
            active_rules = []
            for rule in self._rules.values():
                if rule.is_applicable_to(
                    channel=channel,
                    user_id=user_id,
                    session_id=session_id,
                ):
                    active_rules.append(rule)

            # Sort by priority (highest first)
            active_rules.sort(key=lambda r: r.priority, reverse=True)
            return active_rules

    async def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule.

        Args:
            rule_id: The rule ID to enable

        Returns:
            True if the rule was enabled, False if not found
        """
        async with self._lock:
            if rule_id not in self._rules:
                return False
            self._rules[rule_id].enabled = True
            await self._persist()
            return True

    async def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule.

        Args:
            rule_id: The rule ID to disable

        Returns:
            True if the rule was disabled, False if not found
        """
        async with self._lock:
            if rule_id not in self._rules:
                return False
            self._rules[rule_id].enabled = False
            await self._persist()
            return True

    async def reinforce_rule(self, rule_id: str) -> bool:
        """Mark a rule as reinforced (update reinforced_at timestamp).

        Args:
            rule_id: The rule ID to reinforce

        Returns:
            True if the rule was reinforced, False if not found
        """
        async with self._lock:
            if rule_id not in self._rules:
                return False
            self._rules[rule_id].reinforced_at = datetime.utcnow()
            await self._persist()
            return True

    async def _persist(self) -> None:
        """Persist rules to disk atomically.

        Uses write-to-temp-then-rename pattern for safety.
        """
        data = {
            "version": 1,
            "rules": [
                rule.model_dump(mode="json")
                for rule in self._rules.values()
            ],
        }

        # Atomic write: write to temp file, then rename
        tmp_path = self._rules_file.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(self._rules_file)

    async def clear_all(self) -> None:
        """Clear all rules.

        Warning: This will delete all stored rules!
        """
        async with self._lock:
            self._rules.clear()
            await self._persist()
