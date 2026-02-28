# -*- coding: utf-8 -*-
"""CoPaw Agents Module.

This module provides the main agent implementation and supporting utilities
for building AI agents with tools, skills, and memory management.

Public API:
- CoPawAgent: Main agent class
- create_model_and_formatter: Factory for creating models and formatters
- TaskRouter: Task complexity classifier for intelligent model routing
- ModelManager: Cached model manager for tier-based selection

Example:
    >>> from copaw.agents import CoPawAgent, create_model_and_formatter
    >>> agent = CoPawAgent()
    >>> # Or with custom model
    >>> model, formatter = create_model_and_formatter()
"""

# CoPawAgent is lazy-loaded so that importing agents.skills_manager (e.g.
# from CLI init_cmd/skills_cmd) does not pull react_agent, agentscope, tools.
# pylint: disable=undefined-all-variable
__all__ = [
    "CoPawAgent",
    "create_model_and_formatter",
    "TaskRouter",
    "ModelManager",
]


def __getattr__(name: str):
    """Lazy load heavy imports."""
    if name == "CoPawAgent":
        from .react_agent import CoPawAgent

        return CoPawAgent
    if name == "create_model_and_formatter":
        from .model_factory import create_model_and_formatter

        return create_model_and_formatter
    if name == "TaskRouter":
        from .task_router import TaskRouter

        return TaskRouter
    if name == "ModelManager":
        from .model_factory import ModelManager

        return ModelManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
