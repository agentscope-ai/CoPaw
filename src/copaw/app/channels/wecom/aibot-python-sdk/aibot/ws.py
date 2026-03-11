"""
WebSocket 长连接管理器

对标 Node.js SDK src/ws.ts
负责维护与企业微信的 WebSocket 长连接，包括心跳、重连、认证、串行回复队列等。
"""

import asyncio
import json
import ssl
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    # 未安装 certifi 时回退到系统默认证书
    _SSL_CONTEXT = ssl.create_default_context()

from .types import WsCmd, WsFrame
from .utils import generate_req_id

# SDK 内置默认 WebSocket 连接地址
DEFAULT_WS_URL = "wss://openws.work.weixin.qq.com"

try:
    import websockets
    from websockets.client import WebSocketClientProtocol

    def _ws_is_open(ws) -> bool:
        """兼容 websockets 新旧版本的连接状态判断"""
        if hasattr(ws, 'open'):
            # websockets <= 13.x
            return ws.open
        elif hasattr(ws, 'state'):
            # websockets >= 14.x
            try:
                from websockets.protocol import State
                return ws.state is State.OPEN
            except ImportError:
                return ws.state.name == 'OPEN'
        return False
except ImportError:
    raise ImportError("请安装 websockets: pip install websockets>=12.0")


class _ReplyQueueItem:
    """回复队列中的单个任务项"""

    __slots__ = ("frame", "future")

    def __init__(self, frame: WsFrame, future: "asyncio.Future[WsFrame]"):
        self.frame = frame
        self.future = future


class WsConnectionManager:
    """
    WebSocket 长连接管理器

    负责维护与企业微信的 WebSocket 长连接，包括心跳、重连、认证等。
    """

    def __init__(
        self,
        logger: Any,
        heartbeat_interval: int = 30000,
        reconnect_base_delay: int = 1000,
        max_reconnect_attempts: int = 10,
        ws_url: Optional[str] = None,
    ):
        self._logger = logger
        self._ws_url = ws_url or DEFAULT_WS_URL
        self._heartbeat_interval = heartbeat_interval
        self._reconnect_base_delay = reconnect_base_delay
        self._max_reconnect_attempts = max_reconnect_attempts

        self._ws: Optional[WebSocketClientProtocol] = None
        self._heartbeat_task: Optional[asyncio.Task[None]] = None
        self._receive_task: Optional[asyncio.Task[None]] = None
        self._reconnect_attempts: int = 0
        self._is_manual_close: bool = False

        # 认证凭证
        self._bot_id: str = ""
        self._bot_secret: str = ""

        # 心跳相关
        self._missed_pong_count: int = 0
        self._max_missed_pong: int = 2
        self._reconnect_max_delay: int = 30000

        # 串行回复队列
        self._reply_queues: Dict[str, List[_ReplyQueueItem]] = {}
        self._pending_acks: Dict[
            str,
            Tuple["asyncio.Future[WsFrame]", Optional[asyncio.TimerHandle]],
        ] = {}
        self._reply_ack_timeout: float = 5.0  # 秒
        self._max_reply_queue_size: int = 100
        self._processing_queues: set = set()  # 正在处理的 req_id 集合

        # 回调
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_authenticated: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[str], None]] = None
        self.on_message: Optional[Callable[[WsFrame], None]] = None
        self.on_reconnecting: Optional[Callable[[int], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

    def set_credentials(self, bot_id: str, bot_secret: str) -> None:
        """设置认证凭证"""
        self._bot_id = bot_id
        self._bot_secret = bot_secret

    async def connect(self) -> None:
        """建立 WebSocket 连接"""
        self._is_manual_close = False

        # 清理旧连接
        await self._cleanup_ws()

        self._logger.info(f"Connecting to WebSocket: {self._ws_url}...")

        try:
            self._ws = await websockets.connect(
                self._ws_url,
                ssl=_SSL_CONTEXT,
                ping_interval=None,  # 我们自己管理心跳
                ping_timeout=None,
                close_timeout=5,
            )

            self._reconnect_attempts = 0
            self._missed_pong_count = 0

            self._logger.info("WebSocket connection established, sending auth...")

            # 连接建立回调
            if self.on_connected:
                self.on_connected()

            # 发送认证帧
            await self._send_auth()

            # 启动消息接收循环
            self._receive_task = asyncio.ensure_future(self._receive_loop())

        except Exception as e:
            self._logger.error(f"Failed to create WebSocket connection: {e}")
            if self.on_error:
                self.on_error(e)
            await self._schedule_reconnect()

    async def _cleanup_ws(self) -> None:
        """清理 WebSocket 连接"""
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except (asyncio.CancelledError, Exception):
                pass
            self._receive_task = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def _send_auth(self) -> None:
        """发送认证帧"""
        try:
            await self.send(
                {
                    "cmd": WsCmd.SUBSCRIBE,
                    "headers": {"req_id": generate_req_id(WsCmd.SUBSCRIBE)},
                    "body": {
                        "bot_id": self._bot_id,
                        "secret": self._bot_secret,
                    },
                }
            )
            self._logger.info("Auth frame sent")
        except Exception as e:
            self._logger.error(f"Failed to send auth frame: {e}")

    async def _receive_loop(self) -> None:
        """消息接收循环"""
        try:
            async for raw_message in self._ws:  # type: ignore
                try:
                    if isinstance(raw_message, bytes):
                        raw_message = raw_message.decode("utf-8")
                    frame: WsFrame = json.loads(raw_message)
                    self._handle_frame(frame)
                except json.JSONDecodeError as e:
                    self._logger.error(f"Failed to parse WebSocket message: {e}")
        except websockets.exceptions.ConnectionClosed as e:
            reason_str = str(e) or f"code: {e.code}"
            self._logger.warn(f"WebSocket connection closed: {reason_str}")
            self._stop_heartbeat()
            self._clear_pending_messages(f"WebSocket connection closed ({reason_str})")
            if self.on_disconnected:
                self.on_disconnected(reason_str)
            if not self._is_manual_close:
                await self._schedule_reconnect()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._logger.error(f"WebSocket error: {e}")
            if self.on_error:
                self.on_error(e)

    def _handle_frame(self, frame: WsFrame) -> None:
        """处理收到的帧数据"""
        cmd = frame.get("cmd")

        # 消息推送
        if cmd == WsCmd.CALLBACK:
            self._logger.debug(f"Received push message: {json.dumps(frame.get('body', {}))}")
            if self.on_message:
                self.on_message(frame)
            return

        # 事件推送
        if cmd == WsCmd.EVENT_CALLBACK:
            self._logger.debug(f"Received event callback: {json.dumps(frame.get('body', {}))}")
            if self.on_message:
                self.on_message(frame)
            return

        # 无 cmd 的帧：认证响应、心跳响应或回复消息回执
        headers = frame.get("headers", {})
        req_id = headers.get("req_id", "")

        # 检查是否是回复消息的回执
        if req_id in self._pending_acks:
            self._handle_reply_ack(req_id, frame)
            return

        if req_id.startswith(WsCmd.SUBSCRIBE):
            # 认证响应
            errcode = frame.get("errcode")
            if errcode != 0:
                self._logger.error(
                    f"Authentication failed: errcode={errcode}, errmsg={frame.get('errmsg')}"
                )
                if self.on_error:
                    self.on_error(
                        Exception(
                            f"Authentication failed: {frame.get('errmsg')} (code: {errcode})"
                        )
                    )
                return
            self._logger.info("Authentication successful")
            self._start_heartbeat()
            if self.on_authenticated:
                self.on_authenticated()
            return

        if req_id.startswith(WsCmd.HEARTBEAT):
            # 心跳响应
            errcode = frame.get("errcode")
            if errcode != 0:
                self._logger.warn(
                    f"Heartbeat ack error: errcode={errcode}, errmsg={frame.get('errmsg')}"
                )
                return
            self._missed_pong_count = 0
            self._logger.debug("Received heartbeat ack")
            return

        # 未知帧类型
        self._logger.warn(f"Received unknown frame: {json.dumps(frame)}")
        if self.on_message:
            self.on_message(frame)

    def _start_heartbeat(self) -> None:
        """启动心跳定时器"""
        self._stop_heartbeat()
        self._heartbeat_task = asyncio.ensure_future(self._heartbeat_loop())
        self._logger.debug(
            f"Heartbeat timer started, interval: {self._heartbeat_interval}ms"
        )

    def _stop_heartbeat(self) -> None:
        """停止心跳定时器"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
            self._logger.debug("Heartbeat timer stopped")

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        try:
            while True:
                await asyncio.sleep(self._heartbeat_interval / 1000)
                await self._send_heartbeat()
        except asyncio.CancelledError:
            pass

    async def _send_heartbeat(self) -> None:
        """发送心跳"""
        # 检查连续未收到 pong 的次数
        if self._missed_pong_count >= self._max_missed_pong:
            self._logger.warn(
                f"No heartbeat ack received for {self._missed_pong_count} consecutive pings, "
                "connection considered dead"
            )
            self._stop_heartbeat()
            # 强制关闭底层连接
            if self._ws:
                try:
                    await self._ws.close()
                except Exception:
                    pass
            return

        self._missed_pong_count += 1
        try:
            await self.send(
                {
                    "cmd": WsCmd.HEARTBEAT,
                    "headers": {"req_id": generate_req_id(WsCmd.HEARTBEAT)},
                }
            )
            extra = (
                f" (awaiting {self._missed_pong_count} pong)"
                if self._missed_pong_count > 1
                else ""
            )
            self._logger.debug(f"Heartbeat sent{extra}")
        except Exception as e:
            self._logger.error(f"Failed to send heartbeat: {e}")

    async def _schedule_reconnect(self) -> None:
        """安排重连"""
        if (
            self._max_reconnect_attempts != -1
            and self._reconnect_attempts >= self._max_reconnect_attempts
        ):
            self._logger.error(
                f"Max reconnect attempts reached ({self._max_reconnect_attempts}), giving up"
            )
            if self.on_error:
                self.on_error(Exception("Max reconnect attempts exceeded"))
            return

        self._reconnect_attempts += 1
        # 指数退避：1s, 2s, 4s, 8s … 上限 30s
        delay = min(
            self._reconnect_base_delay * (2 ** (self._reconnect_attempts - 1)),
            self._reconnect_max_delay,
        )

        self._logger.info(
            f"Reconnecting in {delay}ms (attempt {self._reconnect_attempts})..."
        )
        if self.on_reconnecting:
            self.on_reconnecting(self._reconnect_attempts)

        await asyncio.sleep(delay / 1000)
        if self._is_manual_close:
            return

        await self.connect()

    async def send(self, frame: WsFrame) -> None:
        """
        发送数据帧

        :param frame: WebSocket 帧
        :raises RuntimeError: 连接未建立时
        """
        if self._ws and _ws_is_open(self._ws):
            await self._ws.send(json.dumps(frame))
        else:
            raise RuntimeError("WebSocket not connected, unable to send data")

    async def send_reply(
        self, req_id: str, body: Any, cmd: str = WsCmd.RESPONSE
    ) -> WsFrame:
        """
        通过 WebSocket 通道发送回复消息（串行队列版本）

        同一个 req_id 的消息会被放入队列中串行发送。

        :param req_id: 透传回调中的 req_id
        :param body: 回复消息体
        :param cmd: 发送的命令类型，默认 WsCmd.RESPONSE
        :return: 回执帧
        """
        loop = asyncio.get_event_loop()
        future: asyncio.Future[WsFrame] = loop.create_future()

        frame: WsFrame = {
            "cmd": cmd,
            "headers": {"req_id": req_id},
            "body": body,
        }

        item = _ReplyQueueItem(frame, future)

        if req_id not in self._reply_queues:
            self._reply_queues[req_id] = []

        queue = self._reply_queues[req_id]

        # 防止队列无限增长
        if len(queue) >= self._max_reply_queue_size:
            self._logger.warn(
                f"Reply queue for reqId {req_id} exceeds max size ({self._max_reply_queue_size}), "
                "rejecting new message"
            )
            future.set_exception(
                RuntimeError(
                    f"Reply queue for reqId {req_id} exceeds max size ({self._max_reply_queue_size})"
                )
            )
            return await future

        queue.append(item)

        # 如果队列中只有这一条，立即开始处理
        if len(queue) == 1 and req_id not in self._processing_queues:
            asyncio.ensure_future(self._process_reply_queue(req_id))

        return await future

    async def _process_reply_queue(self, req_id: str) -> None:
        """处理指定 req_id 的回复队列"""
        self._processing_queues.add(req_id)

        try:
            while True:
                queue = self._reply_queues.get(req_id)
                if not queue:
                    self._reply_queues.pop(req_id, None)
                    break

                item = queue[0]

                try:
                    await self.send(item.frame)
                    self._logger.debug(
                        f"Reply message sent via WebSocket, reqId: {req_id}, queue length: {len(queue)}"
                    )
                except Exception as e:
                    self._logger.error(f"Failed to send reply for reqId {req_id}: {e}")
                    queue.pop(0)
                    if not item.future.done():
                        item.future.set_exception(e)
                    continue

                # 等待回执
                loop = asyncio.get_event_loop()
                ack_future: asyncio.Future[WsFrame] = loop.create_future()

                # 设置超时
                timeout_handle = loop.call_later(
                    self._reply_ack_timeout,
                    self._on_reply_ack_timeout,
                    req_id,
                    ack_future,
                )

                self._pending_acks[req_id] = (ack_future, timeout_handle)

                try:
                    ack_frame = await ack_future
                    # 成功收到回执
                    queue.pop(0)
                    if not item.future.done():
                        item.future.set_result(ack_frame)
                except Exception as e:
                    queue.pop(0)
                    if not item.future.done():
                        item.future.set_exception(e)
        finally:
            self._processing_queues.discard(req_id)

    def _on_reply_ack_timeout(
        self, req_id: str, ack_future: "asyncio.Future[WsFrame]"
    ) -> None:
        """回复回执超时回调"""
        self._logger.warn(
            f"Reply ack timeout ({self._reply_ack_timeout}s) for reqId: {req_id}"
        )
        self._pending_acks.pop(req_id, None)
        if not ack_future.done():
            ack_future.set_exception(
                TimeoutError(
                    f"Reply ack timeout ({self._reply_ack_timeout}s) for reqId: {req_id}"
                )
            )

    def _handle_reply_ack(self, req_id: str, frame: WsFrame) -> None:
        """处理回复消息的回执"""
        pending = self._pending_acks.pop(req_id, None)
        if not pending:
            return

        ack_future, timeout_handle = pending

        # 取消超时
        if timeout_handle:
            timeout_handle.cancel()

        errcode = frame.get("errcode")
        if errcode != 0:
            self._logger.warn(
                f"Reply ack error: reqId={req_id}, errcode={errcode}, errmsg={frame.get('errmsg')}"
            )
            if not ack_future.done():
                ack_future.set_exception(
                    RuntimeError(
                        f"Reply ack error: errcode={errcode}, errmsg={frame.get('errmsg')}"
                    )
                )
        else:
            self._logger.debug(f"Reply ack received for reqId: {req_id}")
            if not ack_future.done():
                ack_future.set_result(frame)

    def _clear_pending_messages(self, reason: str) -> None:
        """清理所有待处理的消息和回执"""
        for req_id, (ack_future, timeout_handle) in self._pending_acks.items():
            if timeout_handle:
                timeout_handle.cancel()
            if not ack_future.done():
                ack_future.set_exception(RuntimeError(reason))
        self._pending_acks.clear()

        for req_id, queue in self._reply_queues.items():
            for item in queue:
                if not item.future.done():
                    item.future.set_exception(
                        RuntimeError(f"{reason}, reply for reqId: {req_id} cancelled")
                    )
        self._reply_queues.clear()

    def disconnect(self) -> None:
        """主动断开连接（同步方法，安排异步关闭）"""
        self._is_manual_close = True
        self._stop_heartbeat()
        self._clear_pending_messages("Connection manually closed")

        if self._ws:
            asyncio.ensure_future(self._async_disconnect())

        self._logger.info("WebSocket connection manually closed")

    async def _async_disconnect(self) -> None:
        """异步断开连接"""
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except (asyncio.CancelledError, Exception):
                pass

        if self._ws:
            try:
                await self._ws.close(code=1000, reason="Manual disconnect")
            except Exception:
                pass
            self._ws = None

    @property
    def is_connected(self) -> bool:
        """获取当前连接状态"""
        return self._ws is not None and _ws_is_open(self._ws)
