# -*- coding: utf-8 -*-
"""Task complexity classification for intelligent model routing.

This module implements indicator-based task classification inspired by
ClawRouter, using keyword counting and special rules for <1ms local
routing decisions.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

from ..providers import ModelTier

if TYPE_CHECKING:
    from agentscope.tool import Toolkit

# Tier override prefixes for force-override
TIER_OVERRIDES = {
    "/simple:": ModelTier.SIMPLE,
    "/medium:": ModelTier.MEDIUM,
    "/complex:": ModelTier.COMPLEX,
    "/reasoning:": ModelTier.REASONING,
}


class TaskRouter:
    """Indicator-based task complexity classifier.

    Uses keyword counting and special rules for fast (<1ms) local routing.
    Inspired by ClawRouter's proven patterns.
    """

    # SIMPLE indicators - greetings, status, basic queries
    SIMPLE_KEYWORDS = [
        # English
        "what is",
        "define",
        "translate",
        "list",
        "check",
        "hello",
        "hi ",
        "thanks",
        "thank you",
        "status",
        "help",
        "what are",
        "who is",
        "when is",
        "where is",
        "how many",
        "yes",
        "no",
        "ok",
        "okay",
        "sure",
        "got it",
        "understood",
        # Chinese
        "你好",
        "您好",
        "谢谢",
        "感谢",
        "是什么",
        "定义",
        "列出",
        "查看",
        "帮助",
        "好的",
        "收到",
        "明白",
    ]

    # MEDIUM indicators - summarization, single-file edits, explanations
    MEDIUM_KEYWORDS = [
        # English
        "summarize",
        "summary",
        "explain",
        "write",
        "fix this",
        "how to",
        "extract",
        "edit",
        "read",
        "show",
        "find",
        "search",
        "look for",
        "tell me",
        "describe",
        "convert",
        "format",
        "organize",
        "sort",
        "filter",
        "update",
        "modify",
        "change",
        "rename",
        "move",
        "copy",
        # Chinese
        "总结",
        "解释",
        "修复",
        "如何",
        "读取",
        "查找",
        "搜索",
        "描述",
        "转换",
        "格式化",
        "更新",
        "修改",
        "重命名",
        "移动",
        "复制",
    ]

    # COMPLEX indicators - multi-file, architecture, code generation
    COMPLEX_KEYWORDS = [
        # English
        "build",
        "design",
        "architect",
        "refactor",
        "create",
        "implement",
        "analyze",
        "debug",
        "develop",
        "construct",
        "generate",
        "scaffold",
        "migrate",
        "integrate",
        "deploy",
        "optimize",
        "restructure",
        "rewrite",
        "extend",
        "add feature",
        "new feature",
        "multi-file",
        "multiple files",
        "across files",
        # Chinese
        "构建",
        "设计",
        "重构",
        "创建",
        "实现",
        "分析",
        "调试",
        "生成",
        "迁移",
        "集成",
        "部署",
        "优化",
        "重写",
        "扩展",
        "新功能",
        "多文件",
    ]

    # REASONING indicators - proofs, deep analysis, multi-step
    REASONING_KEYWORDS = [
        # English
        "prove",
        "derive",
        "reason",
        "why does",
        "evaluate",
        "theorem",
        "compare and contrast",
        "step by step",
        "first principles",
        "logically",
        "inference",
        "deduce",
        "hypothesis",
        "validate",
        "verify",
        "proof",
        "demonstrate",
        "justify",
        "argue",
        "critique",
        "assess",
        "examine",
        "investigate",
        "explore",
        "consider",
        "weigh",
        "tradeoff",
        "trade-off",
        "pros and cons",
        "advantages and disadvantages",
        # Chinese
        "证明",
        "推导",
        "为什么",
        "评估",
        "对比",
        "逐步",
        "逻辑",
        "推断",
        "假设",
        "验证",
        "论证",
        "批判",
        "考察",
        "权衡",
        "优缺点",
        "利弊",
    ]

    # Heartbeat/status patterns - require full match
    HEARTBEAT_PATTERNS = [
        r"^ping$",
        r"^pong$",
        r"^status$",
        r"^heartbeat$",
        r"^health\s*check$",
        r"^are you there$",
        r"^you there$",
        r"^你还在吗$",
        r"^在吗$",
        r"^还在吗$",
    ]

    # Stack trace pattern for debugging detection
    STACK_TRACE_PATTERN = re.compile(
        r"(Traceback\s*\(|at\s+\w+\.\w+\(|File\s+\"[^\"]+\",\s*line\s+\d+|"
        r"Error:|Exception:|Stack\s+trace:)",
        re.IGNORECASE,
    )

    # Code block pattern
    CODE_BLOCK_PATTERN = re.compile(r"```\w*\n", re.MULTILINE)

    # Multi-file reference patterns
    MULTI_FILE_PATTERNS = [
        re.compile(
            r"\bin\s+\S+\.(py|js|ts|java|go|rs|cpp|c|h)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bfiles?\s*:?\s*\[", re.IGNORECASE),
        re.compile(
            r"\bfrom\s+\S+\.(py|js|ts|java|go|rs|cpp|c|h)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\band\s+\S+\.(py|js|ts|java|go|rs|cpp|c|h)\b",
            re.IGNORECASE,
        ),
    ]

    def __init__(self) -> None:
        """Initialize TaskRouter with compiled patterns."""
        self._heartbeat_re = [
            re.compile(p, re.IGNORECASE) for p in self.HEARTBEAT_PATTERNS
        ]

    def classify_task(
        self,
        query: str,
        tools: Optional[list] = None,  # pylint: disable=unused-argument
        context: Optional[list] = None,  # pylint: disable=unused-argument
    ) -> str:
        """Classify task complexity and return appropriate tier.

        Args:
            query: User query text
            tools: Available tools (optional, for future enhancement)
            context: Conversation context (optional, for future enhancement)

        Returns:
            Tier name: "simple", "medium", "complex", or "reasoning"
        """
        # pylint: disable=too-many-return-statements
        query_lower = query.lower()

        # Special rule: Heartbeats/status always SIMPLE
        if self._is_heartbeat(query_lower):
            return ModelTier.SIMPLE

        # Count indicators per tier
        reasoning_count = self._count_keywords(
            query_lower,
            self.REASONING_KEYWORDS,
        )
        complex_count = self._count_keywords(
            query_lower,
            self.COMPLEX_KEYWORDS,
        )
        medium_count = self._count_keywords(query_lower, self.MEDIUM_KEYWORDS)
        simple_count = self._count_keywords(query_lower, self.SIMPLE_KEYWORDS)

        # Special rule: 2+ reasoning keywords -> REASONING
        if reasoning_count >= 2:
            return ModelTier.REASONING

        # Check for code blocks or multi-file references
        has_code_blocks = self._has_code_blocks(query)
        has_multi_file = self._has_multi_file_refs(query)
        has_stack_trace = self._has_stack_trace(query)

        # Code blocks or multi-file -> minimum MEDIUM
        if has_code_blocks or has_multi_file:
            if reasoning_count > 0:
                return ModelTier.REASONING
            if complex_count > 0 or has_stack_trace:
                return ModelTier.COMPLEX
            return ModelTier.MEDIUM

        # "Debug" + stack trace -> COMPLEX
        if has_stack_trace and "debug" in query_lower:
            return ModelTier.COMPLEX

        # Return highest tier with matches
        if complex_count > 0:
            return ModelTier.COMPLEX
        if medium_count > 0:
            return ModelTier.MEDIUM
        if simple_count > 0:
            return ModelTier.SIMPLE

        # Default to MEDIUM (ClawRouter pattern: safe default)
        return ModelTier.MEDIUM

    def parse_override(self, query: str) -> tuple[Optional[str], str]:
        """Parse force-override prefix from query.

        Args:
            query: User query text

        Returns:
            Tuple of (tier_override or None, cleaned_query)
        """
        for prefix, tier in TIER_OVERRIDES.items():
            if query.startswith(prefix):
                return tier, query[len(prefix) :].strip()
        return None, query

    def _is_heartbeat(self, query_lower: str) -> bool:
        """Check if query is a heartbeat/status check."""
        query_stripped = query_lower.strip()
        for pattern in self._heartbeat_re:
            if pattern.fullmatch(query_stripped):
                return True
        return False

    def _count_keywords(self, text: str, keywords: list[str]) -> int:
        """Count how many keywords from the list appear in text as whole words."""
        count = 0
        text_lower = text.lower()
        for kw in keywords:
            # Use word boundaries to match whole words only
            import re
            pattern = re.compile(rf"\b{re.escape(kw.lower())}\b", re.IGNORECASE)
            if pattern.search(text_lower):
                count += 1
        return count

    def _has_code_blocks(self, query: str) -> bool:
        """Check if query contains code blocks."""
        return bool(self.CODE_BLOCK_PATTERN.search(query))

    def _has_multi_file_refs(self, query: str) -> bool:
        """Check if query references multiple files."""
        matches = 0
        for pattern in self.MULTI_FILE_PATTERNS:
            if pattern.search(query):
                matches += 1
        return matches >= 1

    def _has_stack_trace(self, query: str) -> bool:
        """Check if query contains a stack trace."""
        return bool(self.STACK_TRACE_PATTERN.search(query))


__all__ = ["TaskRouter", "TIER_OVERRIDES"]
