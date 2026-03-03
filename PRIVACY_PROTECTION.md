# Shell Command Privacy Protection

## Overview

This feature adds optional privacy protection for shell command execution in CoPaw, preventing sensitive information from being exposed in chat interfaces.

## Problem

When using CoPaw in production environments or shared chat channels, shell command execution may leak sensitive information such as:
- Credentials and API keys in command arguments
- Internal file paths and directory structures  
- Confidential data in command output
- System configurations

**Example of information leakage:**
```
🔧 execute_shell_command
{"command": "export AWS_SECRET_KEY='abc123...' && deploy.sh"}

✅ execute_shell_command:
Successfully deployed to region us-east-1
Database password: xyz789...
```

## Solution

Add environment variable `COPAW_HIDE_SHELL_DETAILS` to enable privacy mode:

**Privacy mode enabled:**
```
🔧 execute_shell_command running

✓ 操作已成功执行
```

## Usage

### Enable Privacy Mode

```bash
# Set environment variable
export COPAW_HIDE_SHELL_DETAILS=true

# Start CoPaw
copaw app
```

Or in your startup script:
```bash
COPAW_HIDE_SHELL_DETAILS=true copaw app --host 0.0.0.0 --port 8088
```

### Disable Privacy Mode (Default)

```bash
# No environment variable or set to false
export COPAW_HIDE_SHELL_DETAILS=false

# Start CoPaw
copaw app
```

This will show full command details and output (original behavior).

## Configuration

The `COPAW_HIDE_SHELL_DETAILS` environment variable accepts the following values:

**Enable privacy mode:**
- `true`
- `1`
- `yes`

**Disable privacy mode (default):**
- `false`
- `0`
- `no`
- (not set)

## Behavior

### Normal Mode (Default)

When privacy mode is disabled:
- Tool call shows: `🔧 execute_shell_command` with full command arguments
- Tool output shows: Complete stdout and stderr
- Backward compatible with existing behavior

### Privacy Mode

When `COPAW_HIDE_SHELL_DETAILS=true`:

**Tool call display:**
- Shows: `🔧 execute_shell_command running`
- Hides: Command arguments and parameters

**Tool output display:**
- Success: `✓ 操作已成功执行` (Operation completed successfully)
- Failure: `✗ 操作执行失败 (退出码: N)` (Operation failed with exit code N)
- Hides: Stdout and stderr details

## Use Cases

### Production Environments
- Protect credentials in automated deployments
- Hide internal infrastructure details
- Comply with security policies

### Shared Chat Channels
- Prevent accidental credential exposure in group chats
- Maintain confidentiality in team channels
- Safe operation in customer-facing environments

### Enterprise Deployments
- Meet compliance requirements (SOC2, ISO27001)
- Audit-friendly logging
- Minimize attack surface

## Security Considerations

1. **Command execution still happens normally** - Only the display is affected
2. **Logs may still contain details** - Configure logging separately
3. **Not a replacement for proper secret management** - Use vault systems for credentials
4. **Agent still sees full output** - This only affects what users see in chat

## Implementation Details

### Modified Files

1. **src/copaw/agents/tools/shell.py**
   - Added `HIDE_SHELL_DETAILS` environment check
   - Simplified output formatting in privacy mode

2. **src/copaw/app/channels/renderer.py**
   - Added privacy check in `_parts_for_tool_call`
   - Shows generic "running" message for shell commands

### Backward Compatibility

- ✅ No breaking changes
- ✅ Default behavior unchanged
- ✅ Opt-in feature via environment variable
- ✅ No configuration file changes required

## Testing

### Test Privacy Mode

```bash
# Enable privacy mode
export COPAW_HIDE_SHELL_DETAILS=true
copaw app

# In chat, trigger a shell command operation
# Verify: No command details are shown
# Verify: Only generic success/failure messages appear
```

### Test Normal Mode

```bash
# Disable privacy mode (or don't set the variable)
export COPAW_HIDE_SHELL_DETAILS=false
copaw app

# In chat, trigger a shell command operation  
# Verify: Full command details are shown
# Verify: Complete output is displayed
```

## Future Enhancements

Potential improvements for future versions:

- [ ] Per-channel privacy settings
- [ ] Configurable privacy levels (minimal, moderate, strict)
- [ ] Redaction patterns for partial hiding
- [ ] Audit log for privacy-protected commands
- [ ] Web UI toggle for privacy mode

## Contributing

If you have suggestions for improving this feature, please:
1. Open an issue for discussion
2. Submit a PR with your improvements
3. Update this documentation

## License

This feature is part of CoPaw and follows the same Apache 2.0 license.
