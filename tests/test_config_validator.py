# -*- coding: utf-8 -*-
"""Tests for configuration validator."""
import pytest
from copaw.config.validator import ConfigValidator, ValidationLevel
from copaw.config.config import Config, ChannelConfig, DingTalkConfig


def test_validator_basic():
    """Test basic validator functionality."""
    config = Config()
    # Disable console channel to trigger warning
    config.channels.console.enabled = False

    validator = ConfigValidator(config)
    result = validator.validate_all()

    # Should have warning for no channels enabled
    assert len(result.warnings) > 0
    assert result.valid  # No errors, just warnings


def test_dingtalk_missing_credentials():
    """Test DingTalk validation with missing credentials."""
    config = Config()
    config.channels.dingtalk.enabled = True
    config.channels.dingtalk.client_id = ""
    config.channels.dingtalk.client_secret = ""

    validator = ConfigValidator(config)
    result = validator.validate_all()

    # Should have error for missing credentials
    assert not result.valid
    assert len(result.errors) > 0
    assert any("DINGTALK_MISSING_CREDENTIALS" in e.code for e in result.errors)


def test_agents_invalid_max_iters():
    """Test agents validation with invalid max_iters."""
    config = Config()
    config.agents.running.max_iters = 0

    validator = ConfigValidator(config)
    result = validator.validate_all()

    # Should have error for invalid max_iters
    assert not result.valid
    assert any("AGENTS_INVALID_MAX_ITERS" in e.code for e in result.errors)


def test_mcp_stdio_no_command():
    """Test MCP validation with stdio but no command."""
    # Pydantic already validates this at model level
    # This test verifies that Pydantic validation works
    from copaw.config.config import MCPClientConfig
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        MCPClientConfig(
            name="test",
            enabled=True,
            transport="stdio",
            command="",
        )

    # Verify error message
    assert "stdio MCP client requires non-empty command" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
