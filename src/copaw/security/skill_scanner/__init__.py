# -*- coding: utf-8 -*-
"""
Skill security scanner for CoPaw.

Integrates pattern-based detection (YAML signatures + YARA rules) from
`skill-scanner <https://github.com/cisco/skill-scanner>`_ to scan skills
for security threats before they are activated or installed.

Architecture
~~~~~~~~~~~~

The scanner is modular and extensible:

* **BaseAnalyzer** – abstract interface every analyzer must implement.
* **PatternAnalyzer** – YAML regex-signature matching (fast, line-based).
* **YaraAnalyzer** – YARA-X rule matching (binary-safe, complex conditions).
* **SkillScanner** – orchestrator that runs all registered analyzers and
  aggregates results into a :class:`ScanResult`.

Only pattern-based detection is shipped today.  The :class:`BaseAnalyzer`
interface is intentionally kept thin so that new engines (LLM-as-a-judge,
behavioral analysis, …) can be plugged in without changes to the
orchestrator.

Quick start::

    from copaw.security.skill_scanner import SkillScanner

    scanner = SkillScanner()
    result = scanner.scan_skill("/path/to/skill_directory")
    if not result.is_safe:
        print(f"Blocked: {result.max_severity.value} findings detected")
"""
from __future__ import annotations

from .models import (
    Finding,
    ScanResult,
    Severity,
    SkillFile,
    ThreatCategory,
)
from .scan_policy import ScanPolicy
from .scanner import SkillScanner

__all__ = [
    "Finding",
    "ScanPolicy",
    "ScanResult",
    "Severity",
    "SkillFile",
    "SkillScanner",
    "ThreatCategory",
]
