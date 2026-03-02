# -*- coding: utf-8 -*-
"""Rules package for CoPaw.

This package provides rule management capabilities for CoPaw,
allowing users to define persistent rules that guide agent behavior.

Example:
    >>> from copaw.agents.rules import RuleManager, RuleScope
    >>> manager = RuleManager()
    >>> await manager.load()
    >>> rule = await manager.add_rule(
    ...     content="Always respond in Chinese",
    ...     scope=RuleScope.GLOBAL,
    ... )
"""

from .models import RuleScope, RuleSpec
from .rule_manager import RuleManager

__all__ = [
    "RuleScope",
    "RuleSpec",
    "RuleManager",
]
