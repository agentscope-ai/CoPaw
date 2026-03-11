"""
企业微信智能机器人 SDK 类型定义

对标 Node.js SDK src/types/ 目录下的全部类型：
- common.ts  → Logger Protocol
- config.ts  → WSClientOptions dataclass
- message.ts → MessageType 枚举, BaseMessage 等消息类型
- api.ts     → WsCmd 常量, WsFrame, 各种回复/发送消息体, TemplateCard 等
- event.ts   → EventType 枚举, EventMessage 等事件类型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# ========== 通用基础类型 (common.ts) ==========


@runtime_checkable
class Logger(Protocol):
    """日志接口"""

    def debug(self, message: str, *args: Any) -> None: ...
    def info(self, message: str, *args: Any) -> None: ...
    def warn(self, message: str, *args: Any) -> None: ...
    def error(self, message: str, *args: Any) -> None: ...


# ========== 配置类型 (config.ts) ==========


@dataclass
class WSClientOptions:
    """WSClient 配置选项"""

    bot_id: str
    """机器人 ID（在企业微信后台获取）"""

    secret: str
    """机器人 Secret（在企业微信后台获取）"""

    reconnect_interval: int = 1000
    """WebSocket 重连基础延迟（毫秒），实际延迟按指数退避递增，默认 1000"""

    max_reconnect_attempts: int = 10
    """最大重连次数，默认 10，设为 -1 表示无限重连"""

    heartbeat_interval: int = 30000
    """心跳间隔（毫秒），默认 30000"""

    request_timeout: int = 10000
    """请求超时时间（毫秒），默认 10000"""

    ws_url: str = ""
    """自定义 WebSocket 连接地址，默认 wss://openws.work.weixin.qq.com"""

    logger: Optional[Any] = None
    """自定义日志函数"""


# ========== WebSocket 命令常量 (api.ts) ==========


class WsCmd:
    """WebSocket 命令类型常量"""

    # ========== 开发者 → 企业微信 ==========
    SUBSCRIBE = "aibot_subscribe"
    """认证订阅"""

    HEARTBEAT = "ping"
    """心跳"""

    RESPONSE = "aibot_respond_msg"
    """回复消息"""

    RESPONSE_WELCOME = "aibot_respond_welcome_msg"
    """回复欢迎语"""

    RESPONSE_UPDATE = "aibot_respond_update_msg"
    """更新模板卡片"""

    SEND_MSG = "aibot_send_msg"
    """主动发送消息"""

    # ========== 企业微信 → 开发者 ==========
    CALLBACK = "aibot_msg_callback"
    """消息推送回调"""

    EVENT_CALLBACK = "aibot_event_callback"
    """事件推送回调"""


# ========== 消息类型枚举 (message.ts) ==========


class MessageType(str, Enum):
    """消息类型枚举"""

    Text = "text"
    """文本消息"""

    Image = "image"
    """图片消息"""

    Mixed = "mixed"
    """图文混排消息"""

    Voice = "voice"
    """语音消息"""

    File = "file"
    """文件消息"""


# ========== 事件类型枚举 (event.ts) ==========


class EventType(str, Enum):
    """事件类型枚举"""

    EnterChat = "enter_chat"
    """进入会话事件：用户当天首次进入机器人单聊会话"""

    TemplateCardEvent = "template_card_event"
    """模板卡片事件：用户点击模板卡片按钮"""

    FeedbackEvent = "feedback_event"
    """用户反馈事件：用户对机器人回复进行反馈"""


# ========== 模板卡片类型枚举 (api.ts) ==========


class TemplateCardType(str, Enum):
    """卡片类型枚举"""

    TextNotice = "text_notice"
    """文本通知模版卡片"""

    NewsNotice = "news_notice"
    """图文展示模版卡片"""

    ButtonInteraction = "button_interaction"
    """按钮交互模版卡片"""

    VoteInteraction = "vote_interaction"
    """投票选择模版卡片"""

    MultipleInteraction = "multiple_interaction"
    """多项选择模版卡片"""


# ========== WebSocket 帧结构 (api.ts) ==========
#
# Python 中使用 dict 表示 JSON 帧，以下提供类型别名和工厂函数辅助使用。
# WsFrame 在 Python 中直接使用 Dict[str, Any]，字段:
#   cmd?: str          — 命令类型
#   headers: dict      — 请求头 { req_id: str, ... }
#   body?: Any         — 消息体
#   errcode?: int      — 响应错误码
#   errmsg?: str       — 响应错误信息

# 类型别名（用于类型提示）
WsFrame = Dict[str, Any]
"""WebSocket 帧结构，等价于 { cmd?, headers: { req_id, ... }, body?, errcode?, errmsg? }"""

WsFrameHeaders = Dict[str, Any]
"""仅包含 headers 的 WsFrame 子集，用于 reply 等方法的参数类型"""
