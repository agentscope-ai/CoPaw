# -*- coding: utf-8 -*-
"""Rule models for CoPaw rule management.

This module defines the data models for rule specification and management.
"""
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import uuid4


class RuleScope(str, Enum):
    """Rule application scope.

    Defines the scope of where a rule applies:
    - GLOBAL: Applies to all channels and users
    - CHANNEL: Applies to a specific channel (e.g., dingtalk, feishu)
    - USER: Applies to a specific user across all channels
    - SESSION: Applies to a specific session only
    """
    GLOBAL = "global"
    CHANNEL = "channel"
    USER = "user"
    SESSION = "session"


class RuleSpec(BaseModel):
    """Rule specification.

    Attributes:
        id: Unique identifier for the rule
        content: The rule content/description
        scope: The scope of rule application
        channel: Channel name (for CHANNEL scope)
        user_id: User identifier (for USER scope)
        session_id: Session identifier (for SESSION scope)
        priority: Rule priority (higher = more important)
        created_at: When the rule was created
        reinforced_at: When the rule was last reinforced
        enabled: Whether the rule is currently active
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    scope: RuleScope = RuleScope.GLOBAL

    # Scope-specific fields
    channel: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Metadata
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reinforced_at: Optional[datetime] = None

    # Status
    enabled: bool = True

    class Config:
        """Pydantic model config."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            RuleScope: lambda v: v.value,
        }

    def is_applicable_to(
        self,
        channel: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """Check if this rule applies to the given context.

        Args:
            channel: Channel name to check
            user_id: User ID to check
            session_id: Session ID to check

        Returns:
            True if the rule applies to the given context
        """
        if not self.enabled:
            return False

        if self.scope == RuleScope.GLOBAL:
            return True
        elif self.scope == RuleScope.CHANNEL:
            return self.channel == channel
        elif self.scope == RuleScope.USER:
            return self.user_id == user_id
        elif self.scope == RuleScope.SESSION:
            return self.session_id == session_id

        return False


__all__ = ["RuleScope", "RuleSpec"]
