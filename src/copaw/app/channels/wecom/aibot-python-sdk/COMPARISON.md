# Node.js vs Python SDK 对比文档

本文档对比 `@wecom/aibot-node-sdk`（Node.js）与 `wecom-aibot-sdk`（Python）两个版本的实现差异。

## 📁 代码结构映射

| Node.js (src/) | Python (aibot/) | 说明 |
| --- | --- | --- |
| `index.ts` | `__init__.py` | SDK 入口，统一导出 |
| `client.ts` | `client.py` | 核心客户端 WSClient |
| `ws.ts` | `ws.py` | WebSocket 长连接管理器 |
| `message-handler.ts` | `message_handler.py` | 消息解析与事件分发 |
| `api.ts` | `api.py` | HTTP API 客户端（文件下载） |
| `crypto.ts` | `crypto_utils.py` | AES-256-CBC 文件解密 |
| `logger.ts` | `logger.py` | 默认日志实现 |
| `utils.ts` | `utils.py` | 工具方法 |
| `types/` (6 个文件) | `types.py` (1 个文件) | 类型定义 |
| `examples/basic.ts` | `examples/basic.py` | 基础使用示例 |

**行数对比：**

| 模块 | Node.js | Python | 说明 |
| --- | --- | --- | --- |
| 核心客户端 | ~384 行 | ~280 行 | Python 更简洁（无显式类型标注冗余） |
| WS 管理器 | ~512 行 | ~380 行 | asyncio 原语减少了回调嵌套 |
| 消息处理器 | ~105 行 | ~80 行 | 逻辑一致 |
| API 客户端 | ~59 行 | ~60 行 | 基本等量 |
| 加解密 | ~59 行 | ~55 行 | 基本等量 |
| 类型定义 | ~820 行 (6文件) | ~160 行 (1文件) | Python 使用 dict 替代复杂接口 |
| 日志 | ~34 行 | ~45 行 | Python 略多（Protocol 定义） |
| 工具函数 | ~30 行 | ~30 行 | 等量 |

## 📚 依赖库对标

| 功能 | Node.js 依赖 | Python 依赖 | 说明 |
| --- | --- | --- | --- |
| WebSocket 客户端 | `ws` (^8.16.0) | `websockets` (>=12.0) | 均为各语言最流行的 WS 库 |
| HTTP 客户端 | `axios` (^1.6.7) | `aiohttp` (>=3.9) | Python 版使用异步 HTTP |
| 事件发射器 | `eventemitter3` (^5.0.1) | `pyee` (>=11.0) | API 风格高度一致（on/emit/once） |
| 加解密 | `crypto` (Node.js 内置) | `cryptography` (>=42.0) | Python 版需额外安装 |
| 类型系统 | TypeScript | `dataclasses` + `typing` + `enum` | 均为语言内置 |
| 构建工具 | Rollup + TypeScript | setuptools + pyproject.toml | 各语言标准构建链 |

## 🔄 异步编程模型差异

### Node.js: 事件循环 + 回调/Promise

```typescript
// Node.js 天然单线程事件循环
wsClient.connect();  // 同步启动，内部异步

// 事件回调
wsClient.on('message.text', (frame) => {
  // 同步回调，返回 Promise
  wsClient.replyStream(frame, streamId, content, true);
});

// Promise 链式调用
wsClient.replyStream(frame, streamId, '内容', true)
  .then(ack => console.log('回执:', ack))
  .catch(err => console.error(err));
```

### Python: asyncio + async/await

```python
# Python 需要显式管理事件循环
await ws_client.connect()  # async 方法

# 事件回调支持协程
@ws_client.on('message.text')
async def on_text(frame):
    # async 回调，使用 await
    await ws_client.reply_stream(frame, stream_id, content, True)

# async/await 风格
try:
    ack = await ws_client.reply_stream(frame, stream_id, '内容', True)
    print('回执:', ack)
except Exception as e:
    print(f'错误: {e}')
```

### 关键差异

| 方面 | Node.js | Python |
| --- | --- | --- |
| 事件循环 | 内置，自动启动 | 需要 `asyncio.run()` 或 `loop.run_forever()` |
| 连接方法 | `connect()` — 同步调用 | `await connect()` — 必须在 async 上下文 |
| 回复方法 | 返回 `Promise<WsFrame>` | 返回 `Coroutine → WsFrame`（需 await） |
| 定时器 | `setInterval` / `setTimeout` | `asyncio.create_task` + `asyncio.sleep` |
| 回调风格 | `(frame) => { ... }` | `async def handler(frame): ...` |
| 便捷启动 | 直接运行 | `ws_client.run()` 或手动管理循环 |
| 断开连接 | `disconnect()` — 同步 | `disconnect()` — 同步（内部调度异步关闭） |

## 🏷️ 类型系统差异

### Node.js: TypeScript 接口

```typescript
// 丰富的接口定义（编译期类型安全）
interface WsFrame<T = any> {
  cmd?: string;
  headers: { req_id: string; [key: string]: any };
  body?: T;
  errcode?: number;
  errmsg?: string;
}

// 泛型消息帧
type TextFrame = WsFrame<TextMessage>;
```

### Python: dataclass + dict

```python
# 配置类使用 dataclass（运行时类型安全）
@dataclass
class WSClientOptions:
    bot_id: str
    secret: str
    reconnect_interval: int = 1000
    ...

# 消息帧直接使用 dict（运行时灵活）
WsFrame = Dict[str, Any]
# 访问：frame.get('body', {}).get('text', {}).get('content')
```

### 类型策略对比

| 方面 | Node.js (TypeScript) | Python |
| --- | --- | --- |
| 帧结构 | `WsFrame<T>` 泛型接口 | `Dict[str, Any]` 类型别名 |
| 消息类型 | 独立接口（TextMessage 等） | dict 访问，无独立类型 |
| 配置选项 | `WSClientOptions` 接口 | `WSClientOptions` dataclass |
| 枚举 | TypeScript `enum` | Python `enum.Enum`（str 继承） |
| 模板卡片 | 20+ 子接口精确定义 | `Dict[str, Any]`（运行时灵活） |
| 类型检查 | 编译期（tsc） | 运行时 + 可选静态检查（mypy） |

**设计选择说明**：Python 版本选择使用 `dict` 而非为每种消息定义 TypedDict，原因是：
1. 企业微信协议字段较多，JSON 结构直接映射为 dict 更自然
2. 减少了大量样板类型定义代码
3. Python 生态中 dict 访问模式更为常见和惯用
4. 保持 SDK 轻量，降低维护成本

## 📛 命名规范转换

| Node.js (camelCase) | Python (snake_case) | 说明 |
| --- | --- | --- |
| `replyStream()` | `reply_stream()` | 方法名 |
| `replyWelcome()` | `reply_welcome()` | 方法名 |
| `replyTemplateCard()` | `reply_template_card()` | 方法名 |
| `replyStreamWithCard()` | `reply_stream_with_card()` | 方法名 |
| `updateTemplateCard()` | `update_template_card()` | 方法名 |
| `sendMessage()` | `send_message()` | 方法名 |
| `downloadFile()` | `download_file()` | 方法名 |
| `generateReqId()` | `generate_req_id()` | 工具函数 |
| `generateRandomString()` | `generate_random_string()` | 工具函数 |
| `isConnected` | `is_connected` | 属性 |
| `botId` | `bot_id` | 配置项 |
| `heartbeatInterval` | `heartbeat_interval` | 配置项 |
| `maxReconnectAttempts` | `max_reconnect_attempts` | 配置项 |
| `reconnectInterval` | `reconnect_interval` | 配置项 |
| `requestTimeout` | `request_timeout` | 配置项 |
| `wsUrl` | `ws_url` | 配置项 |
| `WSClient` | `WSClient` | 类名保持 PascalCase |
| `WsCmd.SUBSCRIBE` | `WsCmd.SUBSCRIBE` | 常量保持 UPPER_SNAKE_CASE |

## 📊 API 方法对照表

| 功能 | Node.js | Python |
| --- | --- | --- |
| 创建实例 | `new WSClient(options)` | `WSClient(options)` |
| 建立连接 | `wsClient.connect()` → `this` | `await ws_client.connect()` → `WSClient` |
| 断开连接 | `wsClient.disconnect()` | `ws_client.disconnect()` |
| 通用回复 | `wsClient.reply(frame, body, cmd?)` → `Promise<WsFrame>` | `await ws_client.reply(frame, body, cmd?)` → `WsFrame` |
| 流式回复 | `wsClient.replyStream(frame, id, content, finish?, items?, fb?)` → `Promise<WsFrame>` | `await ws_client.reply_stream(frame, id, content, finish?, items?, fb?)` → `WsFrame` |
| 欢迎语 | `wsClient.replyWelcome(frame, body)` → `Promise<WsFrame>` | `await ws_client.reply_welcome(frame, body)` → `WsFrame` |
| 模板卡片 | `wsClient.replyTemplateCard(frame, card, fb?)` → `Promise<WsFrame>` | `await ws_client.reply_template_card(frame, card, fb?)` → `WsFrame` |
| 流式+卡片 | `wsClient.replyStreamWithCard(frame, id, content, finish?, opts?)` → `Promise<WsFrame>` | `await ws_client.reply_stream_with_card(frame, id, content, finish?, ...)` → `WsFrame` |
| 更新卡片 | `wsClient.updateTemplateCard(frame, card, userids?)` → `Promise<WsFrame>` | `await ws_client.update_template_card(frame, card, userids?)` → `WsFrame` |
| 主动发送 | `wsClient.sendMessage(chatid, body)` → `Promise<WsFrame>` | `await ws_client.send_message(chatid, body)` → `WsFrame` |
| 下载文件 | `wsClient.downloadFile(url, aesKey?)` → `Promise<{buffer, filename?}>` | `await ws_client.download_file(url, aes_key?)` → `tuple[bytes, str\|None]` |
| 监听事件 | `wsClient.on('event', handler)` | `@ws_client.on('event')` 或 `ws_client.on('event', handler)` |

## 🔧 内部实现差异

### 心跳机制

| 方面 | Node.js | Python |
| --- | --- | --- |
| 定时器 | `setInterval()` | `asyncio.create_task()` + `while` + `asyncio.sleep()` |
| 停止 | `clearInterval()` | `task.cancel()` |
| 超时判定 | 连续 2 次无 pong → `terminate()` | 连续 2 次无 pong → `ws.close()` |

### 串行回复队列

| 方面 | Node.js | Python |
| --- | --- | --- |
| 队列存储 | `Map<string, ReplyQueueItem[]>` | `dict[str, list[_ReplyQueueItem]]` |
| 等待回执 | `Promise` + `resolve/reject` | `asyncio.Future` + `set_result/set_exception` |
| 超时 | `setTimeout()` | `loop.call_later()` |
| 处理方式 | 递归调用 `processReplyQueue()` | `async while` 循环 |

### 重连策略

两个版本完全一致：
- 指数退避：1s → 2s → 4s → 8s → 16s → 30s（上限）
- 最大重连次数：默认 10，-1 表示无限重连
- 手动断开后不自动重连

### AES 解密

| 方面 | Node.js | Python |
| --- | --- | --- |
| 库 | `crypto`（内置） | `cryptography`（需安装） |
| 算法 | `createDecipheriv('aes-256-cbc', key, iv)` | `Cipher(algorithms.AES(key), modes.CBC(iv))` |
| Padding | 手动 PKCS#7（32 字节 block） | 手动 PKCS#7（32 字节 block） |
| IV | `key.subarray(0, 16)` | `key[:16]` |

## 🏗️ 构建与发布

| 方面 | Node.js | Python |
| --- | --- | --- |
| 包名 | `@wecom/aibot-node-sdk` | `wecom-aibot-sdk` |
| 包管理 | npm / yarn | pip |
| 构建工具 | Rollup | setuptools |
| 配置文件 | `package.json` + `rollup.config.mjs` + `tsconfig.json` | `pyproject.toml` |
| 输出格式 | CJS + ESM + .d.ts | 源码直接分发（.py） |
| 类型声明 | `.d.ts` 文件 | 内联类型注解 + `py.typed` |
| 注册中心 | npmjs.com | pypi.org |
