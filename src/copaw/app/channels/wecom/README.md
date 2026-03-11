# WeCom AI Bot Channel

WeCom AI Bot Channel connects to WeCom (Enterprise WeChat) via WebSocket long-connection using the official `wecom-aibot-sdk`.

## Features

- WebSocket long-connection, low-latency real-time messaging
- Automatic heartbeat keepalive
- Auto-reconnection with exponential backoff
- Streaming message replies (typewriter effect)
- Text, image, mixed, voice, and file message support
- Single chat and group chat support
- Welcome message on enter_chat event
- Template card event and feedback event handling

## Configuration

Add the WeCom configuration to `config.json`:

```json
{
  "channels": {
    "wecom": {
      "enabled": true,
      "bot_id": "YOUR_BOT_ID",
      "secret": "YOUR_SECRET",
      "media_dir": "~/.copaw/media",
      "filter_tool_messages": false,
      "filter_thinking": false,
      "dm_policy": "open",
      "group_policy": "open",
      "allow_from": [],
      "deny_message": "",
      "require_mention": false
    }
  }
}
```

Or configure interactively:

```bash
copaw channels config
```

### Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable this channel |
| `bot_id` | str | `""` | WeCom AI Bot ID (from WeCom admin console) |
| `secret` | str | `""` | Long-connection secret (from WeCom admin console) |
| `media_dir` | str | `~/.copaw/media` | Directory to save received media files |
| `filter_tool_messages` | bool | `false` | Hide tool call/result details from replies |
| `filter_thinking` | bool | `false` | Hide agent thinking process from replies |
| `dm_policy` | str | `open` | Direct message policy: `open` or `allowlist` |
| `group_policy` | str | `open` | Group chat policy: `open` or `allowlist` |
| `allow_from` | list | `[]` | Allowlist of user IDs (used when policy is `allowlist`) |
| `deny_message` | str | `""` | Message to send when a user is denied access |
| `require_mention` | bool | `false` | Require @mention in group chats to trigger the bot |

## Getting Credentials

1. Log in to the WeCom Admin Console
2. Go to **App Management** -> **AI Bot**
3. Select your bot and enter its configuration page
4. Enable **API Mode** and select **Long Connection** method
5. Copy the `BotID` and `Secret`

## Usage

1. After configuration, start CoPaw:
   ```bash
   copaw start
   ```

2. In WeCom:
   - **Direct chat**: send a message directly to the bot
   - **Group chat**: `@bot` followed by your message

3. The bot replies in streaming mode (typewriter effect)

## Implementation

Built entirely on the official `wecom-aibot-sdk` package:

| Feature | SDK API |
|---------|---------|
| WebSocket connection | `WSClient.connect()` |
| Event registration | `WSClient.on(event, handler)` |
| Streaming reply | `WSClient.reply_stream()` |
| Welcome message | `WSClient.reply_welcome()` |
| Proactive message | `WSClient.send_message()` |
| Image download/decrypt | `WSClient.download_file()` |
| Heartbeat & reconnect | Managed internally by SDK |

**Supported events:**

| Event | Description |
|-------|-------------|
| `message.text` | Text message received |
| `message.image` | Image message received |
| `message.mixed` | Mixed (text + image) message received |
| `message.voice` | Voice message received (transcribed to text) |
| `message.file` | File message received (logged, not yet processed) |
| `event.enter_chat` | User entered the chat session |
| `event.template_card_event` | Template card interaction |
| `event.feedback_event` | User feedback |

**Runtime parameters:**

- WebSocket endpoint: `wss://openws.work.weixin.qq.com`
- Heartbeat interval: 30 seconds (SDK managed)
- Streaming timeout: 6 minutes
- Max stream frame size: 20 KB

## Troubleshooting

### Connection fails

- Verify `bot_id` and `secret` are correct
- Confirm long-connection mode is enabled in the WeCom admin console
- Check network connectivity

### Messages not responded to

- Check logs to confirm the message callback was received
- Review `dm_policy` and `group_policy` settings
- Verify the bot has permission to access the conversation

### Frequent disconnections

- Check network stability
- Review error messages in the logs
- Ensure only one CoPaw instance is running (a new connection will kick out the old one)

### Image decryption fails

- Confirm the message contains an `aeskey` field
- The `secret` config field is for WebSocket authentication only; image decryption uses the per-message `aeskey` provided by WeCom
