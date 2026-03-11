"""
企业微信智能机器人 SDK 基本使用示例

对标 Node.js SDK examples/basic.ts
"""

import asyncio
import os
import platform
import signal
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

# 将上级目录添加到 sys.path，以便直接运行示例
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aibot import WSClient, WSClientOptions, generate_req_id

# 创建 WSClient 实例
ws_client = WSClient(
    WSClientOptions(
        bot_id="aibxt0pqaD44nP-iIW3xe3p6XPl-KCjdvxX",  # 替换为你的机器人 ID
        secret="Gi1YaQs9Y0rVKPqXIbIEv7F5eYX1lkUUuMCdEkPdGdA",  # 替换为你的机器人 Secret
    )
)

# 模板卡片示例数据
template_card = {
    "card_type": "multiple_interaction",
    "source": {
        "icon_url": "https://wework.qpic.cn/wwpic/252813_jOfDHtcISzuodLa_1629280209/0",
        "desc": "企业微信",
    },
    "main_title": {
        "title": "欢迎使用企业微信",
        "desc": "您的好友正在邀请您加入企业微信",
    },
    "select_list": [
        {
            "question_key": "question_key_one",
            "title": "选择标签1",
            "disable": False,
            "selected_id": "id_one",
            "option_list": [
                {"id": "id_one", "text": "选择器选项1"},
                {"id": "id_two", "text": "选择器选项2"},
            ],
        },
        {
            "question_key": "question_key_two",
            "title": "选择标签2",
            "selected_id": "id_three",
            "option_list": [
                {"id": "id_three", "text": "选择器选项3"},
                {"id": "id_four", "text": "选择器选项4"},
            ],
        },
    ],
    "submit_button": {"text": "提交", "key": "submit_key"},
    "task_id": f"task_id_{int(time.time() * 1000)}",
}


# ========== 连接事件 ==========


@ws_client.on("connected")
def on_connected():
    print("WebSocket 已连接")


@ws_client.on("authenticated")
def on_authenticated():
    print("认证成功")


@ws_client.on("disconnected")
def on_disconnected(reason):
    print(f"连接已断开: {reason}")


@ws_client.on("reconnecting")
def on_reconnecting(attempt):
    print(f"正在进行第 {attempt} 次重连...")


@ws_client.on("error")
def on_error(error):
    print(f"发生错误: {error}", file=sys.stderr)


# ========== 消息事件 ==========


@ws_client.on("message")
def on_message(frame):
    import json

    body_str = json.dumps(frame.get("body", {}), ensure_ascii=False)[:200]
    print(f"收到消息: {body_str}")


@ws_client.on("message.text")
async def on_text_message(frame):
    body = frame.get("body", {})
    text_content = body.get("text", {}).get("content", "")
    print(f"收到文本消息: {text_content}")

    # 生成一个流式消息 ID
    stream_id = generate_req_id("stream")

    # 发送流式中间内容
    await ws_client.reply_stream(frame, stream_id, "正在思考中...", False)

    # 模拟异步处理后发送最终结果
    await asyncio.sleep(1)
    await ws_client.reply_stream(
        frame, stream_id, f'你好！你说的是: "{text_content}"', True
    )
    print("流式回复完成")


@ws_client.on("message.image")
async def on_image_message(frame):
    body = frame.get("body", {})
    image_url = body.get("image", {}).get("url")
    print(f"收到图片消息: {image_url}")

    if not image_url:
        return

    try:
        # 下载图片并使用消息中的 aeskey 解密
        aes_key = body.get("image", {}).get("aeskey")
        buffer, filename = await ws_client.download_file(image_url, aes_key)
        print(f"图片下载成功，大小: {len(buffer)} bytes")

        # 确定文件名
        url_path = urlparse(image_url).path
        file_name = filename or os.path.basename(url_path) or f"image_{int(time.time() * 1000)}"
        save_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(save_path, "wb") as f:
            f.write(buffer)
        print(f"图片已保存到: {save_path}")
    except Exception as e:
        print(f"图片下载失败: {e}", file=sys.stderr)


@ws_client.on("message.mixed")
def on_mixed_message(frame):
    body = frame.get("body", {})
    items = body.get("mixed", {}).get("msg_item", [])
    print(f"收到图文混排消息，包含 {len(items)} 个子项")

    for index, item in enumerate(items):
        if item.get("msgtype") == "text":
            print(f"  [{index}] 文本: {item.get('text', {}).get('content', '')}")
        elif item.get("msgtype") == "image":
            print(f"  [{index}] 图片: {item.get('image', {}).get('url', '')}")


@ws_client.on("message.voice")
def on_voice_message(frame):
    body = frame.get("body", {})
    voice_content = body.get("voice", {}).get("content", "")
    print(f"收到语音消息（转文本）: {voice_content}")


@ws_client.on("message.file")
async def on_file_message(frame):
    body = frame.get("body", {})
    file_url = body.get("file", {}).get("url")
    print(f"收到文件消息: {file_url}")

    if not file_url:
        return

    try:
        aes_key = body.get("file", {}).get("aeskey")
        buffer, filename = await ws_client.download_file(file_url, aes_key)
        print(f"文件下载成功，大小: {len(buffer)} bytes")

        url_path = urlparse(file_url).path
        file_name = filename or os.path.basename(url_path) or f"file_{int(time.time() * 1000)}"
        save_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(save_path, "wb") as f:
            f.write(buffer)
        print(f"文件已保存到: {save_path}")
    except Exception as e:
        print(f"文件下载失败: {e}", file=sys.stderr)


# ========== 事件回调 ==========


@ws_client.on("event.enter_chat")
async def on_enter_chat(frame):
    print("用户进入会话")
    await ws_client.reply_welcome(
        frame,
        {
            "msgtype": "text",
            "text": {"content": "您好！我是智能助手，有什么可以帮您的吗？"},
        },
    )


@ws_client.on("event.template_card_event")
def on_template_card_event(frame):
    body = frame.get("body", {})
    event = body.get("event", {})
    print(f"收到模板卡片事件: {event.get('event_key', '')}")


@ws_client.on("event.feedback_event")
def on_feedback_event(frame):
    import json

    body = frame.get("body", {})
    event = body.get("event", {})
    print(f"收到用户反馈事件: {json.dumps(event, ensure_ascii=False)}")


# ========== 启动 ==========


def main():
    """启动机器人"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 注册优雅退出（Windows 不支持 add_signal_handler）
    if platform.system() != "Windows":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: _shutdown(loop))

    try:
        loop.run_until_complete(ws_client.connect())
        loop.run_forever()
    except KeyboardInterrupt:
        _shutdown(loop)
    finally:
        ws_client.disconnect()
        loop.close()


def _shutdown(loop: asyncio.AbstractEventLoop):
    print("\n正在停止机器人...")
    ws_client.disconnect()
    loop.stop()


if __name__ == "__main__":
    main()
