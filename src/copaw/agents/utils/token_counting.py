# -*- coding: utf-8 -*-
"""Token counting utilities for managing context windows.

This module provides token counting functionality for estimating
message token usage with Qwen tokenizer.

Uses the ``tokenizers`` Rust library directly to avoid pulling in the
heavy ``transformers`` + ``onnxruntime`` stack (~142 MB).
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_tokenizer = None


def _get_tokenizer():
    """Get or initialize the global tokenizer instance.

    Returns a ``tokenizers.Tokenizer`` loaded from the bundled
    ``tokenizer.json`` (Qwen2.5).
    """
    global _tokenizer
    if _tokenizer is not None:
        return _tokenizer

    from tokenizers import Tokenizer

    local_tokenizer_json = (
        Path(__file__).parent.parent.parent / "tokenizer" / "tokenizer.json"
    )

    if local_tokenizer_json.exists():
        logger.info("Using local Qwen tokenizer from %s", local_tokenizer_json.parent)
        _tokenizer = Tokenizer.from_file(str(local_tokenizer_json))
    else:
        logger.warning(
            "Local tokenizer.json not found at %s, "
            "falling back to character estimation",
            local_tokenizer_json,
        )
    return _tokenizer


def _extract_text_from_messages(messages: list[dict]) -> str:
    """Extract text content from messages and concatenate into a string.

    Handles various message formats:
    - Simple string content: {"role": "user", "content": "hello"}
    - List content with text blocks:
      {"role": "user", "content": [{"type": "text", "text": "hello"}]}

    Args:
        messages: List of message dictionaries in chat format.

    Returns:
        str: Concatenated text content from all messages.
    """
    parts = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    # Support {"type": "text", "text": "..."} format
                    text = block.get("text") or block.get("content", "")
                    if text:
                        parts.append(str(text))
                elif isinstance(block, str):
                    parts.append(block)
    return "\n".join(parts)


async def count_message_tokens(
    messages: list[dict],
) -> int:
    """Count tokens in messages using the tokenizer.

    Extracts text content from messages and uses the tokenizer to
    count tokens. This approach is more robust across different model
    types than using apply_chat_template directly.

    Args:
        messages: List of message dictionaries in chat format.

    Returns:
        int: The estimated number of tokens in the messages.

    Raises:
        RuntimeError: If token counter fails to initialize.
    """
    tokenizer = _get_tokenizer()
    text = _extract_text_from_messages(messages)
    if tokenizer is None:
        return len(text) // 4
    encoding = tokenizer.encode(text)
    token_count = len(encoding.ids)
    logger.debug(
        "Counted %d tokens in %d messages",
        token_count,
        len(messages),
    )
    return token_count


async def safe_count_message_tokens(
    messages: list[dict],
) -> int:
    """Safely count tokens in messages with fallback estimation.

    This is a wrapper around count_message_tokens that catches exceptions
    and falls back to a character-based estimation (len // 4) if the
    tokenizer fails.

    Args:
        messages: List of message dictionaries in chat format.

    Returns:
        int: The estimated number of tokens in the messages.
    """
    try:
        return await count_message_tokens(messages)
    except Exception as e:
        # Fallback to character-based estimation
        text = _extract_text_from_messages(messages)
        estimated_tokens = len(text) // 4
        logger.warning(
            "Failed to count tokens: %s, using estimated_tokens=%d",
            e,
            estimated_tokens,
        )
        return estimated_tokens


def safe_count_str_tokens(text: str) -> int:
    """Safely count tokens in a string with fallback estimation.

    Uses the tokenizer to count tokens in the given text. If the tokenizer
    fails, falls back to a character-based estimation (len // 4).

    Args:
        text: The string to count tokens for.

    Returns:
        int: The estimated number of tokens in the string.
    """
    try:
        tokenizer = _get_tokenizer()
        if tokenizer is None:
            return len(text) // 4
        encoding = tokenizer.encode(text)
        token_count = len(encoding.ids)
        logger.debug(
            "Counted %d tokens in string of length %d",
            token_count,
            len(text),
        )
        return token_count
    except Exception as e:
        # Fallback to character-based estimation
        estimated_tokens = len(text) // 4
        logger.warning(
            "Failed to count string tokens: %s, using estimated_tokens=%d",
            e,
            estimated_tokens,
        )
        return estimated_tokens
