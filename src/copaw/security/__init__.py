# -*- coding: utf-8 -*-
"""
Security framework for CoPaw.

This package centralises all security-related mechanisms:

* **Skill scanning** (``copaw.security.skill_scan``)
  Static analysis of skill directories before install / activation.

Sub-modules are kept independent so each concern can evolve (or be
disabled) without affecting the others.  Import-time cost is near-zero
because heavy dependencies are lazily loaded inside each sub-module.

Quick start – skill scanning::

    from copaw.security import scan_skill_directory, SkillScanError

    result = scan_skill_directory("/path/to/skill")
    if result and not result.is_safe:
        print(result.max_severity)
"""
from __future__ import annotations

# -- Skill scanning (re-exported for backward compatibility) ----------------
from .skill_scan import SkillScanError, scan_skill_directory

__all__ = [
    # Skill scanning
    "SkillScanError",
    "scan_skill_directory",
]
