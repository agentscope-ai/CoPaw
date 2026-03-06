# -*- coding: utf-8 -*-
"""Memory compaction hook for managing context window.

This hook monitors token usage and automatically compacts older messages
when the context window approaches its limit, preserving recent messages
and the system prompt.
"""
import logging
from typing import TYPE_CHECKING, Any

from agentscope.agent._react_agent import _MemoryMark

from copaw.config import load_config
from copaw.constant import MEMORY_COMPACT_KEEP_RECENT
from ..utils import (
    check_valid_messages,
    safe_count_message_tokens,
    safe_count_str_tokens,
)

if TYPE_CHECKING:
    from ..memory import MemoryManager

logger = logging.getLogger(__name__)


class MemoryCompactionHook:
    """Hook for automatic memory compaction when context is full.

    This hook monitors the token count of messages and triggers compaction
    when it exceeds the threshold. It preserves the system prompt and recent
    messages while summarizing older conversation history.
    """

    def __init__(self, memory_manager: "MemoryManager"):
        """Initialize memory compaction hook.

        Args:
            memory_manager: Memory manager instance for compaction
        """
        self.memory_manager = memory_manager

    @staticmethod
    def calculate_memory_compact_threshold(
        max_input_length: float,
        compact_ratio: float,
    ) -> int:
        """Calculate the memory compaction threshold.

        Based on input length and ratio.

        Args:
            max_input_length: Maximum input length in tokens.
            compact_ratio: Ratio of the input length to use as the threshold.

        Returns:
            Computed compaction threshold as an integer.
        """
        return int(max_input_length * compact_ratio)

    async def __call__(
        self,
        agent: Any,
        kwargs: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Pre-reasoning hook to check and compact memory if needed.

        Formats all current messages via the agent's formatter, estimates
        total token usage (messages + compressed summary), and triggers
        compaction when the total exceeds the configured threshold.

        Memory structure:
            [System (preserved)] + [Compactable] + [Recent (preserved)]

        Args:
            agent: The agent instance (must expose .memory and .formatter)
            kwargs: Input arguments to the _reasoning method

        Returns:
            None (hook doesn't modify kwargs)
        """
        try:
            memory = agent.memory
            compressed_summary = memory.get_compressed_summary()

            messages = await memory.get_memory(prepend_summary=False)

            full_prompt = await agent.formatter.format(msgs=messages)
            estimated_message_tokens = await safe_count_message_tokens(
                full_prompt,
            )
            summary_tokens = safe_count_str_tokens(compressed_summary)
            estimated_total_tokens = estimated_message_tokens + summary_tokens

            config = load_config()
            memory_compact_threshold = (
                config.agents.running.memory_compact_threshold
            )

            logger.debug(
                "Estimated context tokens total=%d "
                "(messages=%d, summary=%d) vs threshold=%d",
                estimated_total_tokens,
                estimated_message_tokens,
                summary_tokens,
                memory_compact_threshold,
            )

            if estimated_total_tokens <= memory_compact_threshold:
                return None

            non_system_messages = [m for m in messages if m.role != "system"]
            keep_recent = MEMORY_COMPACT_KEEP_RECENT

            if len(non_system_messages) <= keep_recent:
                return None

            while keep_recent > 0 and not check_valid_messages(
                non_system_messages[-keep_recent:],
            ):
                keep_recent -= 1

            if keep_recent > 0:
                messages_to_compact = non_system_messages[:-keep_recent]
            else:
                messages_to_compact = non_system_messages

            if not messages_to_compact:
                return None

            logger.info(
                "Memory compaction triggered: total %d tokens "
                "(messages: %d, summary: %d, threshold: %d), "
                "compactable_msgs: %d, keep_recent_msgs: %d",
                estimated_total_tokens,
                estimated_message_tokens,
                summary_tokens,
                memory_compact_threshold,
                len(messages_to_compact),
                keep_recent,
            )

            self.memory_manager.add_async_summary_task(
                messages=messages_to_compact,
            )

            compact_content = await self.memory_manager.compact_memory(
                messages=messages_to_compact,
                previous_summary=memory.get_compressed_summary(),
            )

            await memory.update_compressed_summary(compact_content)
            updated_count = await memory.update_messages_mark(
                new_mark=_MemoryMark.COMPRESSED,
                msg_ids=[msg.id for msg in messages_to_compact],
            )
            logger.info("Marked %d messages as compacted", updated_count)

        except Exception as e:
            logger.error(
                "Failed to compact memory in pre_reasoning hook: %s",
                e,
                exc_info=True,
            )

        return None
