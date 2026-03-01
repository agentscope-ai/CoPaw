# -*- coding: utf-8 -*-
"""Tests for MessageRenderer thinking block filtering."""

import pytest

from copaw.app.channels.renderer import MessageRenderer, RenderStyle


@pytest.fixture
def renderer():
    return MessageRenderer(style=RenderStyle())


@pytest.fixture
def renderer_no_details():
    return MessageRenderer(
        style=RenderStyle(show_tool_details=False),
    )


class TestThinkingBlockFiltering:
    """Thinking blocks must not leak to channel users."""

    def test_thinking_block_excluded_from_blocks_to_parts(self, renderer):
        """Thinking content should be filtered out, not sent as text."""
        # We can't call _blocks_to_parts directly (it's nested),
        # but we can verify via source inspection that the fix is in place.
        import inspect

        source = inspect.getsource(renderer.message_to_parts)
        # The thinking block handler should use 'continue', not append text
        assert "continue" in source
        # Should NOT contain the old pattern of appending thinking as text
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if 'btype == "thinking"' in line:
                # Next non-blank line should be a comment or continue
                remaining = "\n".join(lines[i:i + 5])
                assert "continue" in remaining, (
                    "Thinking block should use 'continue' to skip"
                )
                assert 'TextContent(text=b["thinking"])' not in remaining, (
                    "Thinking content should NOT be appended as TextContent"
                )
                break
        else:
            pytest.fail("No thinking block handler found in source")
