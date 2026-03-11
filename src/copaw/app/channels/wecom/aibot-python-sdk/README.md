# wecom-aibot-sdk (Python)

企业微信智能机器人 Python SDK —— 基于 WebSocket 长连接通道，提供消息收发、流式回复、模板卡片、事件回调、文件下载解密等核心能力。

> 本项目是 [@wecom/aibot-node-sdk](../README.md)（Node.js 版）的 Python 等价实现。

## ✨ 特性

- 🔗 **WebSocket 长连接** — 基于 `wss://openws.work.weixin.qq.com` 内置默认地址，开箱即用
- 🔐 **自动认证** — 连接建立后自动发送认证帧（bot_id + secret）
- 💓 **心跳保活** — 自动维护心跳，连续未收到 ack 时自动判定连接异常
- 🔄 **断线重连** — 指数退避重连策略（1s → 2s → 4s → ... → 30s 上限），支持自定义最大重连次数
- 📨 **消息分发** — 自动解析消息类型并触发对应事件（text / image / mixed / voice / file）
- 🌊 **流式回复** — 内置流式回复方法，支持 Markdown 和图文混排
- 🃏 **模板卡片** — 支持回复模板卡片消息、流式+卡片组合回复、更新卡片
- 📤 **主动推送** — 支持向指定会话主动发送 Markdown 或模板卡片消息，无需依赖回调帧
- 📡 **事件回调** — 支持进入会话、模板卡片按钮点击、用户反馈等事件
- ⏩ **串行回复队列** — 同一 req_id 的回复消息串行发送，自动等待回执
- 🔑 **文件下载解密** — 内置 AES-256-CBC 文件解密，每个图片/文件消息自带独立的 aeskey
- 🪵 **可插拔日志** — 支持自定义 Logger，内置带时间戳的 DefaultLogger
- 🐍 **asyncio 原生** — 基于 Python asyncio 异步架构，支持 async/await

## 📦 安装

```bash
pip install wecom-aibot-sdk
# 或
pip install -r requirements.txt
```

**依赖：**
- Python >= 3.8
- websockets >= 12.0
- aiohttp >= 3.9
- pyee >= 11.0
- cryptography >= 42.0
- certifi>=2023.0

## 🚀 快速开始

```python
import asyncio
from aibot import WSClient, WSClientOptions, generate_req_id

# 1. 创建客户端实例
ws_client = WSClient(
    WSClientOptions(
        bot_id='your-bot-id',       # 企业微信后台获取的机器人 ID
        secret='your-bot-secret',   # 企业微信后台获取的机器人 Secret
    )
)

# 2. 监听认证成功
@ws_client.on('authenticated')
def on_authenticated():
    print('🔐 认证成功')

# 3. 监听文本消息并进行流式回复
@ws_client.on('message.text')
async def on_text(frame):
    content = frame.get('body', {}).get('text', {}).get('content', '')
    print(f'收到文本: {content}')

    stream_id = generate_req_id('stream')

    # 发送流式中间内容
    await ws_client.reply_stream(frame, stream_id, '正在思考中...', False)

    # 发送最终结果
    await asyncio.sleep(1)
    await ws_client.reply_stream(frame, stream_id, f'你好！你说的是: "{content}"', True)

# 4. 监听进入会话事件（发送欢迎语）
@ws_client.on('event.enter_chat')
async def on_enter_chat(frame):
    await ws_client.reply_welcome(frame, {
        'msgtype': 'text',
        'text': {'content': '您好！我是智能助手，有什么可以帮您的吗？'},
    })

# 5. 启动（便捷方法，内部管理事件循环）
ws_client.run()
```

或者手动管理事件循环：

```python
async def main():
    await ws_client.connect()
    # 保持运行
    await asyncio.Event().wait()

asyncio.run(main())
```

## 📖 API 文档

### `WSClient`

核心客户端类，继承自 `pyee.AsyncIOEventEmitter`，提供连接管理、消息收发等功能。

#### 构造函数

```python
ws_client = WSClient(options: WSClientOptions)
```

#### 方法

| 方法 | 说明 | 返回值 |
| --- | --- | --- |
| `await connect()` | 建立 WebSocket 连接，连接后自动认证 | `WSClient`（支持链式调用） |
| `disconnect()` | 主动断开连接 | `None` |
| `await reply(frame, body, cmd?)` | 通过 WebSocket 通道发送回复消息（通用方法） | `WsFrame` |
| `await reply_stream(frame, stream_id, content, finish?, msg_item?, feedback?)` | 发送流式文本回复（便捷方法，支持 Markdown） | `WsFrame` |
| `await reply_welcome(frame, body)` | 发送欢迎语回复（支持文本或模板卡片），需在收到事件 5s 内调用 | `WsFrame` |
| `await reply_template_card(frame, template_card, feedback?)` | 回复模板卡片消息 | `WsFrame` |
| `await reply_stream_with_card(frame, stream_id, content, finish?, ...)` | 发送流式消息 + 模板卡片组合回复 | `WsFrame` |
| `await update_template_card(frame, template_card, userids?)` | 更新模板卡片，需在收到事件 5s 内调用 | `WsFrame` |
| `await send_message(chatid, body)` | 主动发送消息（支持 Markdown 或模板卡片），无需依赖回调帧 | `WsFrame` |
| `await download_file(url, aes_key?)` | 下载文件并使用 AES 密钥解密 | `tuple[bytes, str \| None]` |
| `run()` | 便捷启动方法（创建事件循环并连接） | `None` |

#### 属性

| 属性 | 说明 | 类型 |
| --- | --- | --- |
| `is_connected` | 当前 WebSocket 连接状态 | `bool` |
| `api` | 内部 API 客户端实例（高级用途） | `WeComApiClient` |

### `reply_stream` 详细说明

```python
await ws_client.reply_stream(
    frame,              # 收到的原始 WebSocket 帧（透传 req_id）
    stream_id: str,     # 流式消息 ID（使用 generate_req_id('stream') 生成）
    content: str,       # 回复内容（支持 Markdown）
    finish: bool = False,  # 是否结束流式消息
    msg_item: list = None, # 图文混排项（仅 finish=True 时有效）
    feedback: dict = None, # 反馈信息（仅首次回复时设置）
)
```

### `reply_welcome` 详细说明

发送欢迎语回复，需在收到 `event.enter_chat` 事件 5 秒内调用。

```python
# 文本欢迎语
await ws_client.reply_welcome(frame, {
    'msgtype': 'text',
    'text': {'content': '欢迎！'},
})

# 模板卡片欢迎语
await ws_client.reply_welcome(frame, {
    'msgtype': 'template_card',
    'template_card': {'card_type': 'text_notice', 'main_title': {'title': '欢迎'}},
})
```

### `reply_stream_with_card` 详细说明

```python
await ws_client.reply_stream_with_card(
    frame,                          # 收到的原始 WebSocket 帧
    stream_id: str,                 # 流式消息 ID
    content: str,                   # 回复内容（支持 Markdown）
    finish: bool = False,           # 是否结束流式消息
    msg_item: list = None,          # 图文混排项（仅 finish=True 时有效）
    stream_feedback: dict = None,   # 流式消息反馈信息（首次回复时设置）
    template_card: dict = None,     # 模板卡片内容（同一消息只能回复一次）
    card_feedback: dict = None,     # 模板卡片反馈信息
)
```

### `send_message` 详细说明

主动向指定会话推送消息，无需依赖收到的回调帧。

```python
# 发送 Markdown 消息
await ws_client.send_message('userid_or_chatid', {
    'msgtype': 'markdown',
    'markdown': {'content': '这是一条**主动推送**的消息'},
})

# 发送模板卡片消息
await ws_client.send_message('userid_or_chatid', {
    'msgtype': 'template_card',
    'template_card': {'card_type': 'text_notice', 'main_title': {'title': '通知'}},
})
```

### `download_file` 使用示例

```python
# aes_key 取自消息体中的 image.aeskey 或 file.aeskey
@ws_client.on('message.image')
async def on_image(frame):
    body = frame.get('body', {})
    image = body.get('image', {})
    buffer, filename = await ws_client.download_file(image.get('url'), image.get('aeskey'))
    print(f'文件名: {filename}, 大小: {len(buffer)} bytes')
```

## ⚙️ 配置选项

`WSClientOptions` 完整配置：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `bot_id` | `str` | ✅ | — | 机器人 ID（企业微信后台获取） |
| `secret` | `str` | ✅ | — | 机器人 Secret（企业微信后台获取） |
| `reconnect_interval` | `int` | — | `1000` | 重连基础延迟（毫秒），实际延迟按指数退避递增 |
| `max_reconnect_attempts` | `int` | — | `10` | 最大重连次数（`-1` 表示无限重连） |
| `heartbeat_interval` | `int` | — | `30000` | 心跳间隔（毫秒） |
| `request_timeout` | `int` | — | `10000` | HTTP 请求超时时间（毫秒） |
| `ws_url` | `str` | — | `wss://openws.work.weixin.qq.com` | 自定义 WebSocket 连接地址 |
| `logger` | `Logger` | — | `DefaultLogger` | 自定义日志实例 |

## 📡 事件列表

所有事件均通过 `@ws_client.on(event)` 装饰器或 `ws_client.on(event, handler)` 监听：

| 事件 | 回调参数 | 说明 |
| --- | --- | --- |
| `connected` | — | WebSocket 连接建立 |
| `authenticated` | — | 认证成功 |
| `disconnected` | `reason: str` | 连接断开 |
| `reconnecting` | `attempt: int` | 正在重连（第 N 次） |
| `error` | `error: Exception` | 发生错误 |
| `message` | `frame: WsFrame` | 收到消息（所有类型） |
| `message.text` | `frame: WsFrame` | 收到文本消息 |
| `message.image` | `frame: WsFrame` | 收到图片消息 |
| `message.mixed` | `frame: WsFrame` | 收到图文混排消息 |
| `message.voice` | `frame: WsFrame` | 收到语音消息 |
| `message.file` | `frame: WsFrame` | 收到文件消息 |
| `event` | `frame: WsFrame` | 收到事件回调（所有事件类型） |
| `event.enter_chat` | `frame: WsFrame` | 收到进入会话事件 |
| `event.template_card_event` | `frame: WsFrame` | 收到模板卡片事件 |
| `event.feedback_event` | `frame: WsFrame` | 收到用户反馈事件 |

## 📋 消息类型

SDK 支持以下消息类型（`MessageType` 枚举）：

| 类型 | 值 | 说明 |
| --- | --- | --- |
| `MessageType.Text` | `'text'` | 文本消息 |
| `MessageType.Image` | `'image'` | 图片消息 |
| `MessageType.Mixed` | `'mixed'` | 图文混排消息 |
| `MessageType.Voice` | `'voice'` | 语音消息 |
| `MessageType.File` | `'file'` | 文件消息 |

SDK 支持以下事件类型（`EventType` 枚举）：

| 类型 | 值 | 说明 |
| --- | --- | --- |
| `EventType.EnterChat` | `'enter_chat'` | 进入会话事件 |
| `EventType.TemplateCardEvent` | `'template_card_event'` | 模板卡片事件 |
| `EventType.FeedbackEvent` | `'feedback_event'` | 用户反馈事件 |

## 🪵 自定义日志

实现 `Logger` Protocol 接口即可自定义日志输出：

```python
class MyLogger:
    def debug(self, message: str, *args) -> None:
        pass  # 静默 debug 日志

    def info(self, message: str, *args) -> None:
        print(f"[INFO] {message}", *args)

    def warn(self, message: str, *args) -> None:
        print(f"[WARN] {message}", *args)

    def error(self, message: str, *args) -> None:
        print(f"[ERROR] {message}", *args)

ws_client = WSClient(
    WSClientOptions(
        bot_id='your-bot-id',
        secret='your-bot-secret',
        logger=MyLogger(),
    )
)
```

## 📂 项目结构

```
aibot-python-sdk/
├── aibot/
│   ├── __init__.py          # 入口文件，统一导出
│   ├── client.py            # WSClient 核心客户端
│   ├── ws.py                # WebSocket 长连接管理器
│   ├── message_handler.py   # 消息解析与事件分发
│   ├── api.py               # HTTP API 客户端（文件下载）
│   ├── crypto_utils.py      # AES-256-CBC 文件解密
│   ├── logger.py            # 默认日志实现
│   ├── utils.py             # 工具方法（generate_req_id 等）
│   └── types.py             # 类型定义（枚举、常量、dataclass）
├── examples/
│   └── basic.py             # 基础使用示例
├── pyproject.toml           # 项目配置
├── requirements.txt         # 依赖清单
├── README.md                # 本文件
└── COMPARISON.md            # Node.js 与 Python 版本对比
```

## 📄 License

MIT
