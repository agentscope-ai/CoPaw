# -*- coding: utf-8 -*-
"""
Security framework for CoPaw.

This package centralises all security-related mechanisms:

* **Tool-call guarding** (``copaw.security.tool_guardrail``)
  Pre-execution parameter scanning to detect dangerous tool usage
  patterns (command injection, data exfiltration, etc.).

Sub-modules are kept independent so each concern can evolve (or be
disabled) without affecting the others.  Import-time cost is near-zero
because heavy dependencies are lazily loaded inside each sub-module.

Quick start – tool-call guarding::

    from copaw.security import guard_tool_call

    result = guard_tool_call("execute_shell_command", {"command": "rm -rf /"})
    if result and not result.is_safe:
        print(result.max_severity)
"""
from __future__ import annotations

# -- Tool-call guarding (lazy re-exports) ----------------------------------
from .tool_guardrail import ToolGuardError, guard_tool_call
from .tool_guard.hook import ToolGuardHook

__all__ = [
    # Tool-call guarding
    "ToolGuardError",
    "guard_tool_call",
    "ToolGuardHook",
]
