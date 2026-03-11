# wecom-aibot-sdk

企业微信智能机器人 Python SDK —— 基于 WebSocket 长连接通道，提供消息收发、流式回复、模板卡片、事件回调、文件下载解密等核心能力。

> 本项目为 [@wecom/aibot-node-sdk](https://github.com/WecomTeam/aibot-node-sdk) 的 Python 版本，API 和使用方式保持一致。

## 特性

- **WebSocket 长连接** — 基于 `wss://openws.work.weixin.qq.com` 内置默认地址，开箱即用
- **自动认证** — 连接建立后自动发送认证帧（botId + secret）
- **心跳保活** — 自动维护心跳，连续未收到 ack 时自动判定连接异常
- **断线重连** — 指数退避重连策略（1s → 2s → 4s → ... → 30s 上限），支持自定义最大重连次数
- **消息分发** — 自动解析消息类型并触发对应事件（text / image / mixed / voice / file）
- **流式回复** — 内置流式回复方法，支持 Markdown 和图文混排
- **模板卡片** — 支持回复模板卡片消息、流式+卡片组合回复、更新卡片
- **主动推送** — 支持向指定会话主动发送 Markdown 或模板卡片消息，无需依赖回调帧
- **事件回调** — 支持进入会话、模板卡片按钮点击、用户反馈等事件
- **串行回复队列** — 同一 req_id 的回复消息串行发送，自动等待回执
- **文件下载解密** — 内置 AES-256-CBC 文件解密，每个图片/文件消息自带独立的 aeskey
- **可插拔日志** — 支持自定义 Logger，内置带时间戳的 DefaultLogger
- **异步架构** — 基于 `asyncio` + `websockets`，性能优异

## 安装

```bash
# 使用 uv
uv add wecom-aibot-sdk

# 或 pip
pip install wecom-aibot-sdk
```

## 快速开始

```python
import asyncio
from wecom_aibot_sdk import WSClient, generate_req_id

async def main():
    # 1. 创建客户端实例
    ws_client = WSClient(
        bot_id="your-bot-id",       # 企业微信后台获取的机器人 ID
        secret="your-bot-secret",   # 企业微信后台获取的机器人 Secret
    )

    # 2. 监听认证成功
    ws_client.on("authenticated", lambda: print("认证成功"))

    # 3. 监听文本消息并进行流式回复
    async def on_text(frame):
        content = frame["body"]["text"]["content"]
        print(f"收到文本: {content}")

        stream_id = generate_req_id("stream")

        # 发送流式中间内容
        await ws_client.reply_stream(frame, stream_id, "正在思考中...", False)

        # 发送最终结果
        await asyncio.sleep(1)
        await ws_client.reply_stream(frame, stream_id, f'你好！你说的是: "{content}"', True)

    ws_client.on("message.text", on_text)

    # 4. 监听进入会话事件（发送欢迎语）
    async def on_enter(frame):
        await ws_client.reply_welcome(frame, {
            "msgtype": "text",
            "text": {"content": "您好！我是智能助手，有什么可以帮您的吗？"},
        })

    ws_client.on("event.enter_chat", on_enter)

    # 5. 建立连接
    await ws_client.connect()

    # 6. 保持运行
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await ws_client.disconnect()

asyncio.run(main())
```

## API 文档

### `WSClient`

核心客户端类，提供连接管理、消息收发等功能。

#### 构造函数

```python
ws_client = WSClient(
    bot_id="your-bot-id",
    secret="your-bot-secret",
    # 以下为可选参数
    reconnect_interval=1000,
    max_reconnect_attempts=10,
    heartbeat_interval=30000,
    request_timeout=10000,
    ws_url="",
    logger=None,
)
```

#### 方法

| 方法                                                                           | 说明                                    | 返回值                                       |
| ------------------------------------------------------------------------------ | --------------------------------------- | -------------------------------------------- |
| `await connect()`                                                              | 建立 WebSocket 连接，连接后自动认证     | `WSClient`（支持链式调用）                   |
| `await disconnect()`                                                           | 主动断开连接                            | `None`                                       |
| `on(event, handler)`                                                           | 注册事件监听器（支持同步/异步 handler） | `WSClient`（支持链式调用）                   |
| `off(event, handler?)`                                                         | 移除事件监听器                          | `WSClient`                                   |
| `await reply(frame, body, cmd?)`                                               | 通用回复方法                            | `WsFrame`                                    |
| `await reply_stream(frame, stream_id, content, finish?, msg_item?, feedback?)` | 流式文本回复（支持 Markdown）           | `WsFrame`                                    |
| `await reply_welcome(frame, body)`                                             | 欢迎语回复（5s 内调用）                 | `WsFrame`                                    |
| `await reply_template_card(frame, template_card, feedback?)`                   | 回复模板卡片消息                        | `WsFrame`                                    |
| `await reply_stream_with_card(frame, stream_id, content, finish?, ...)`        | 流式 + 模板卡片组合回复                 | `WsFrame`                                    |
| `await update_template_card(frame, template_card, userids?)`                   | 更新模板卡片（5s 内调用）               | `WsFrame`                                    |
| `await send_message(chatid, body)`                                             | 主动发送消息                            | `WsFrame`                                    |
| `await download_file(url, aes_key?)`                                           | 下载文件并解密                          | `{"buffer": bytes, "filename": str \| None}` |

#### 属性

| 属性           | 说明                            | 类型             |
| -------------- | ------------------------------- | ---------------- |
| `is_connected` | 当前 WebSocket 连接状态         | `bool`           |
| `api`          | 内部 API 客户端实例（高级用途） | `WeComApiClient` |

### `reply_stream` 详细说明

```python
await ws_client.reply_stream(
    frame,              # 收到的原始 WebSocket 帧（透传 req_id）
    stream_id,          # 流式消息 ID（使用 generate_req_id("stream") 生成）
    content,            # 回复内容（支持 Markdown）
    finish=False,       # 是否结束流式消息
    msg_item=None,      # 图文混排项（仅 finish=True 时有效）
    feedback=None,      # 反馈信息（仅首次回复时设置）
)
```

### `reply_welcome` 详细说明

发送欢迎语回复，需在收到 `event.enter_chat` 事件 5 秒内调用。

```python
# 文本欢迎语
await ws_client.reply_welcome(frame, {
    "msgtype": "text",
    "text": {"content": "欢迎！"},
})

# 模板卡片欢迎语
await ws_client.reply_welcome(frame, {
    "msgtype": "template_card",
    "template_card": {"card_type": "text_notice", "main_title": {"title": "欢迎"}},
})
```

### `reply_stream_with_card` 详细说明

```python
await ws_client.reply_stream_with_card(
    frame,                          # 收到的原始 WebSocket 帧
    stream_id,                      # 流式消息 ID
    content,                        # 回复内容（支持 Markdown）
    finish=False,                   # 是否结束流式消息
    msg_item=None,                  # 图文混排项（仅 finish=True 时有效）
    stream_feedback=None,           # 流式消息反馈信息（首次回复时设置）
    template_card=None,             # 模板卡片内容（同一消息只能回复一次）
    card_feedback=None,             # 模板卡片反馈信息
)
```

### `send_message` 详细说明

```python
# 发送 Markdown 消息
await ws_client.send_message("userid_or_chatid", {
    "msgtype": "markdown",
    "markdown": {"content": "这是一条**主动推送**的消息"},
})

# 发送模板卡片消息
await ws_client.send_message("userid_or_chatid", {
    "msgtype": "template_card",
    "template_card": {"card_type": "text_notice", "main_title": {"title": "通知"}},
})
```

### `download_file` 使用示例

```python
async def on_image(frame):
    body = frame.get("body", {})
    image_url = body.get("image", {}).get("url", "")
    aes_key = body.get("image", {}).get("aeskey")

    result = await ws_client.download_file(image_url, aes_key)
    print(f"文件名: {result['filename']}, 大小: {len(result['buffer'])} bytes")

ws_client.on("message.image", on_image)
```

## 配置选项

| 参数                     | 类型     | 必填 | 默认值                            | 说明                                                                |
| ------------------------ | -------- | ---- | --------------------------------- | ------------------------------------------------------------------- |
| `bot_id`                 | `str`    | 是   | —                                 | 机器人 ID（企业微信后台获取）                                       |
| `secret`                 | `str`    | 是   | —                                 | 机器人 Secret（企业微信后台获取）                                   |
| `reconnect_interval`     | `int`    | —    | `1000`                            | 重连基础延迟（毫秒），指数退避递增（1s → 2s → 4s → ... → 30s 上限） |
| `max_reconnect_attempts` | `int`    | —    | `10`                              | 最大重连次数（`-1` 表示无限重连）                                   |
| `heartbeat_interval`     | `int`    | —    | `30000`                           | 心跳间隔（毫秒）                                                    |
| `request_timeout`        | `int`    | —    | `10000`                           | HTTP 请求超时时间（毫秒）                                           |
| `ws_url`                 | `str`    | —    | `wss://openws.work.weixin.qq.com` | 自定义 WebSocket 连接地址                                           |
| `logger`                 | `Logger` | —    | `DefaultLogger`                   | 自定义日志实例                                                      |

## 事件列表

所有事件均通过 `ws_client.on(event, handler)` 监听，handler 支持同步函数和异步函数：

| 事件                        | 回调参数           | 说明                         |
| --------------------------- | ------------------ | ---------------------------- |
| `connected`                 | —                  | WebSocket 连接建立           |
| `authenticated`             | —                  | 认证成功                     |
| `disconnected`              | `reason: str`      | 连接断开                     |
| `reconnecting`              | `attempt: int`     | 正在重连（第 N 次）          |
| `error`                     | `error: Exception` | 发生错误                     |
| `message`                   | `frame: WsFrame`   | 收到消息（所有类型）         |
| `message.text`              | `frame: WsFrame`   | 收到文本消息                 |
| `message.image`             | `frame: WsFrame`   | 收到图片消息                 |
| `message.mixed`             | `frame: WsFrame`   | 收到图文混排消息             |
| `message.voice`             | `frame: WsFrame`   | 收到语音消息                 |
| `message.file`              | `frame: WsFrame`   | 收到文件消息                 |
| `event`                     | `frame: WsFrame`   | 收到事件回调（所有事件类型） |
| `event.enter_chat`          | `frame: WsFrame`   | 收到进入会话事件             |
| `event.template_card_event` | `frame: WsFrame`   | 收到模板卡片事件             |
| `event.feedback_event`      | `frame: WsFrame`   | 收到用户反馈事件             |

## 消息类型

SDK 支持以下消息类型（`MessageType` 枚举）：

| 类型    | 值        | 说明                                                     |
| ------- | --------- | -------------------------------------------------------- |
| `TEXT`  | `"text"`  | 文本消息                                                 |
| `IMAGE` | `"image"` | 图片消息（URL 已加密，使用消息中的 `image.aeskey` 解密） |
| `MIXED` | `"mixed"` | 图文混排消息（包含 text / image 子项）                   |
| `VOICE` | `"voice"` | 语音消息（已转文本）                                     |
| `FILE`  | `"file"`  | 文件消息（URL 已加密，使用消息中的 `file.aeskey` 解密）  |

SDK 支持以下事件类型（`EventType` 枚举）：

| 类型                  | 值                      | 说明         |
| --------------------- | ----------------------- | ------------ |
| `ENTER_CHAT`          | `"enter_chat"`          | 进入会话事件 |
| `TEMPLATE_CARD_EVENT` | `"template_card_event"` | 模板卡片事件 |
| `FEEDBACK_EVENT`      | `"feedback_event"`      | 用户反馈事件 |

## 自定义日志

实现 `Logger` 协议即可自定义日志输出：

```python
class Logger:
    def debug(self, message: str, *args) -> None: ...
    def info(self, message: str, *args) -> None: ...
    def warn(self, message: str, *args) -> None: ...
    def error(self, message: str, *args) -> None: ...
```

使用示例：

```python
import logging

class MyLogger:
    def __init__(self):
        self._logger = logging.getLogger("AiBot")

    def debug(self, message, *args):
        self._logger.debug(f"{message} {' '.join(str(a) for a in args)}")

    def info(self, message, *args):
        self._logger.info(f"{message} {' '.join(str(a) for a in args)}")

    def warn(self, message, *args):
        self._logger.warning(f"{message} {' '.join(str(a) for a in args)}")

    def error(self, message, *args):
        self._logger.error(f"{message} {' '.join(str(a) for a in args)}")

ws_client = WSClient(
    bot_id="your-bot-id",
    secret="your-bot-secret",
    logger=MyLogger(),
)
```

## 项目结构

```
wecom-aibot-python-sdk/
├── src/
│   └── wecom_aibot_sdk/
│       ├── __init__.py          # 入口文件，统一导出
│       ├── client.py            # WSClient 核心客户端
│       ├── ws.py                # WebSocket 长连接管理器
│       ├── message_handler.py   # 消息解析与事件分发
│       ├── api.py               # HTTP API 客户端（文件下载）
│       ├── crypto.py            # AES-256-CBC 文件解密
│       ├── logger.py            # 默认日志实现
│       ├── utils.py             # 工具方法（generate_req_id 等）
│       └── types.py             # 类型定义
├── examples/
│   └── basic.py                 # 基础使用示例
├── .env.example                 # 环境变量示例
├── pyproject.toml               # 项目配置
└── README.md
```

## 开发

```bash
# 安装依赖
uv sync

# 安装含示例依赖
uv sync --extra examples

# 运行示例
uv run --extra examples python examples/basic.py
```

## 与 Node.js SDK 的对应关系

| Node.js                             | Python                                        | 说明                      |
| ----------------------------------- | --------------------------------------------- | ------------------------- |
| `new WSClient(options)`             | `WSClient(bot_id=..., secret=...)`            | 构造方式改为关键字参数    |
| `wsClient.connect()`                | `await ws_client.connect()`                   | 异步方法                  |
| `wsClient.on('event', handler)`     | `ws_client.on("event", handler)`              | handler 支持 sync/async   |
| `wsClient.replyStream(...)`         | `await ws_client.reply_stream(...)`           | snake_case 命名           |
| `wsClient.replyWelcome(...)`        | `await ws_client.reply_welcome(...)`          | snake_case 命名           |
| `wsClient.replyTemplateCard(...)`   | `await ws_client.reply_template_card(...)`    | snake_case 命名           |
| `wsClient.replyStreamWithCard(...)` | `await ws_client.reply_stream_with_card(...)` | 可选参数改为 keyword-only |
| `wsClient.updateTemplateCard(...)`  | `await ws_client.update_template_card(...)`   | snake_case 命名           |
| `wsClient.sendMessage(...)`         | `await ws_client.send_message(...)`           | snake_case 命名           |
| `wsClient.downloadFile(...)`        | `await ws_client.download_file(...)`          | 返回 dict 而非 object     |
| `generateReqId(prefix)`             | `generate_req_id(prefix)`                     | snake_case 命名           |

## License

MIT
