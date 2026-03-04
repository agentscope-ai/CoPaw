# -*- coding: utf-8 -*-
"""Memory management module for CoPaw agents."""

from .agent_md_manager import AgentMdManager

# CoPawInMemoryMemory and MemoryManager both pull in heavy dependencies:
# - CoPawInMemoryMemory -> agentscope.agent._react_agent (~77ms)
# - MemoryManager -> reme package (~0.9s)
# Defer their imports until first access.


def __getattr__(name: str):
    if name == "CoPawInMemoryMemory":
        from .copaw_memory import CoPawInMemoryMemory

        globals()["CoPawInMemoryMemory"] = CoPawInMemoryMemory
        return CoPawInMemoryMemory
    if name == "MemoryManager":
        from .memory_manager import MemoryManager

        globals()["MemoryManager"] = MemoryManager
        return MemoryManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AgentMdManager",
    "CoPawInMemoryMemory",
    "MemoryManager",
]
