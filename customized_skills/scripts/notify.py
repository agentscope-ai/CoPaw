"""
DC Notify — 长任务完成后推送 Discord 通知
用法:
    python notify.py "✅ 报告已生成"
    python notify.py "✅ 报告已生成" --title "测试报告"
    python notify.py "❌ 任务失败" --title "API测试" --duration "2m30s"
    python notify.py "✅ 完成" --channel-id 1234567890
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# 修复 Windows GBK 编码问题
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DISCORD_API_BASE = "https://discord.com/api/v10"


def load_config():
    """从 CoPaw config.json 读取 Discord 配置"""
    config_path = os.path.join(
        os.path.expanduser("~"), ".copaw", "config.json",
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    dc = config.get("channels", {}).get("discord", {})
    bot_token = dc.get("bot_token", "")

    # channel_id 从 last_dispatch 解析
    channel_id = ""
    last = config.get("last_dispatch", {})
    session_id = last.get("session_id", "")
    # 格式: discord:ch:123456 或 discord:dm:123456
    if session_id.startswith("discord:ch:"):
        channel_id = session_id.split(":", 2)[-1]
    elif session_id.startswith("discord:dm:"):
        # DM 需要先创建 DM channel，这里暂不支持
        channel_id = ""

    if not bot_token:
        print("❌ 未找到 Discord bot_token，请检查 config.json")
        sys.exit(1)

    return bot_token, channel_id


def send_message(bot_token: str, channel_id: str, text: str):
    """通过 Discord Bot API 发送消息"""
    if not channel_id:
        print("❌ 未找到 Discord channel_id，"
              "请用 --channel-id 指定或先在 Discord 通道对话过")
        sys.exit(1)

    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    payload = json.dumps({"content": text}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bot {bot_token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                print("✅ Discord 通知已发送")
            else:
                body = resp.read().decode("utf-8")
                print(f"⚠️ 发送失败 (HTTP {resp.status}): {body}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP 错误 {e.code}: {body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络错误: {e}")
        sys.exit(1)


def build_message(
    message: str,
    title: str = "",
    duration: str = "",
) -> str:
    """组装通知消息（Discord Markdown 格式）"""
    parts = []
    if title:
        parts.append(f"🔔 **{title}**")
    parts.append(message)
    if duration:
        parts.append(f"⏱ 耗时: {duration}")
    parts.append("\n*— CC 自动通知*")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="DC Notify: 发送 Discord 通知",
    )
    parser.add_argument("message", help="通知正文")
    parser.add_argument("--title", "-t", default="", help="通知标题")
    parser.add_argument("--duration", "-d", default="", help="任务耗时")
    parser.add_argument(
        "--channel-id", "-c", default="",
        help="目标频道 ID（不填则自动从 config 读取）",
    )
    args = parser.parse_args()

    bot_token, auto_channel_id = load_config()
    channel_id = args.channel_id or auto_channel_id
    text = build_message(args.message, args.title, args.duration)
    send_message(bot_token, channel_id, text)


if __name__ == "__main__":
    main()
