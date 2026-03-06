"""
Send Image — 向 Telegram 或 Discord 发送图片
用法:
    python send_image.py "screenshot.png"
    python send_image.py "screenshot.png" --caption "首页截图"
    python send_image.py "https://example.com/img.png" --channel telegram
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

TG_API = "https://api.telegram.org"
DC_API = "https://discord.com/api/v10"


def load_config():
    """读取 CoPaw config.json"""
    config_path = os.path.join(
        os.path.expanduser("~"), ".copaw", "config.json",
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_channel(config):
    """自动检测当前活跃通道"""
    last = config.get("last_dispatch", {})
    ch = last.get("channel", "")
    if ch in ("telegram", "discord"):
        return ch
    # console 时优先 TG
    tg = config.get("channels", {}).get("telegram", {})
    if tg.get("enabled") and tg.get("bot_token"):
        return "telegram"
    dc = config.get("channels", {}).get("discord", {})
    if dc.get("enabled") and dc.get("bot_token"):
        return "discord"
    return ""


def _scan_sessions_for(channel_prefix):
    """从 sessions 目录扫描指定通道的 session 文件，提取目标 ID"""
    sessions_dir = os.path.join(
        os.path.expanduser("~"), ".copaw", "sessions",
    )
    if not os.path.isdir(sessions_dir):
        return ""
    for fname in os.listdir(sessions_dir):
        if channel_prefix in fname and fname.endswith(".json"):
            # telegram--7135633051 → 7135633051
            # discord--ch--123456 → ch:123456
            # discord--dm--123456 → dm:123456
            parts = fname.replace(".json", "").split("_", 1)
            if len(parts) >= 2:
                session_part = parts[1].replace("--", ":")
                return session_part
    return ""


def get_tg_chat_id(config):
    """获取 TG chat_id"""
    # 优先从 last_dispatch
    last = config.get("last_dispatch", {})
    sid = last.get("session_id", "")
    if sid.startswith("telegram:"):
        return sid.split(":", 1)[-1]
    # 从 sessions 目录扫描
    session_key = _scan_sessions_for("telegram--")
    if session_key.startswith("telegram:"):
        return session_key.split(":", 1)[-1]
    # 兜底用 user_id
    uid = last.get("user_id", "")
    if uid and not uid.startswith("discord"):
        return uid
    return ""


def get_dc_channel_id(config):
    """获取 DC channel_id（优先频道，DM 作为兜底）"""
    last = config.get("last_dispatch", {})
    sid = last.get("session_id", "")
    # 1. last_dispatch 是频道
    if sid.startswith("discord:ch:"):
        return sid.split(":", 2)[-1]
    # 2. sessions 里扫描频道 session
    session_key = _scan_sessions_for("discord--ch--")
    if session_key.startswith("discord:ch:"):
        return session_key.split(":", 2)[-1]
    # 3. 扫描 discord--u-- 格式（频道 session）
    channel_id = _scan_dc_u_session()
    if channel_id:
        return channel_id
    # 4. 兜底：DM
    if sid.startswith("discord:dm:"):
        dm_id = _create_dc_dm(config, sid.split(":", 2)[-1])
        if dm_id:
            return dm_id
    session_key = _scan_sessions_for("discord--dm--")
    if session_key.startswith("discord:dm:"):
        dm_id = _create_dc_dm(config, session_key.split(":", 2)[-1])
        if dm_id:
            return dm_id
    return ""


def _scan_dc_u_session():
    """扫描 discord--u--xxx--yyy 格式的 session，提取频道 ID"""
    sessions_dir = os.path.join(
        os.path.expanduser("~"), ".copaw", "sessions",
    )
    if not os.path.isdir(sessions_dir):
        return ""
    for fname in sorted(os.listdir(sessions_dir), reverse=True):
        # 格式: {user}_discord--u--{user}--{channel}.json
        if "discord--u--" in fname and fname.endswith(".json"):
            # 取最后一个 -- 后面的部分作为 channel_id
            base = fname.replace(".json", "")
            parts = base.split("--")
            if len(parts) >= 4:
                return parts[-1]
    return ""


def _create_dc_dm(config, user_id):
    """通过 Discord API 创建 DM channel 并返回 channel_id"""
    token = config["channels"]["discord"]["bot_token"]
    url = f"{DC_API}/users/@me/channels"
    payload = json.dumps({"recipient_id": user_id}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bot {token}",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("id", "")
    except Exception as e:
        print(f"❌ 创建 DM channel 失败: {e}")
        return ""


def is_url(s):
    return s.startswith("http://") or s.startswith("https://")


def download_url_to_temp(url):
    """下载网络图片到临时文件"""
    try:
        suffix = Path(url.split("?")[0]).suffix or ".png"
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, prefix="copaw_img_",
        )
        req = urllib.request.Request(url, headers={
            "User-Agent": "CoPaw/1.0",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            tmp.write(resp.read())
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"❌ 下载图片失败: {e}")
        return None


def send_tg_photo(config, image_path, caption=""):
    """通过 Telegram Bot API 发送图片"""
    token = config["channels"]["telegram"]["bot_token"]
    chat_id = get_tg_chat_id(config)
    if not chat_id:
        print("❌ 未找到 TG chat_id")
        return False

    url = f"{TG_API}/bot{token}/sendPhoto"
    boundary = "----CoPawBoundary"
    body = b""

    # chat_id 字段
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
    body += f"{chat_id}\r\n".encode()

    # caption 字段
    if caption:
        body += f"--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="caption"\r\n\r\n'
        body += f"{caption}\r\n".encode()

    # photo 字段
    fname = Path(image_path).name
    body += f"--{boundary}\r\n".encode()
    body += (
        f'Content-Disposition: form-data; name="photo"; '
        f'filename="{fname}"\r\n'
    ).encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    with open(image_path, "rb") as f:
        body += f.read()
    body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                print("✅ TG 图片已发送")
                return True
            print(f"⚠️ TG 发送失败: {result}")
            return False
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"❌ TG HTTP 错误 {e.code}: {err}")
        return False
    except Exception as e:
        print(f"❌ TG 发送失败: {e}")
        return False


def send_dc_photo(config, image_path, caption=""):
    """通过 Discord Bot API + aiohttp 发送图片"""
    import asyncio
    try:
        import aiohttp
    except ImportError:
        print("❌ 需要 aiohttp 库: pip install aiohttp")
        return False

    token = config["channels"]["discord"]["bot_token"]
    channel_id = get_dc_channel_id(config)
    if not channel_id:
        print("❌ 未找到 DC channel_id")
        return False

    async def _send():
        url = f"{DC_API}/channels/{channel_id}/messages"
        form = aiohttp.FormData()
        if caption:
            form.add_field(
                "payload_json", json.dumps({"content": caption}),
            )
        fname = Path(image_path).name
        # 简单推断 content_type
        suffix = Path(image_path).suffix.lower()
        ct_map = {
            ".png": "image/png", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", ".gif": "image/gif",
            ".webp": "image/webp",
        }
        ct = ct_map.get(suffix, "application/octet-stream")
        form.add_field(
            "files[0]",
            open(image_path, "rb"),
            filename=fname,
            content_type=ct,
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, data=form,
                headers={"Authorization": f"Bot {token}"},
            ) as resp:
                if resp.status in (200, 201):
                    print("✅ DC 图片已发送")
                    return True
                body = await resp.text()
                print(f"❌ DC 发送失败 (HTTP {resp.status}): {body[:200]}")
                return False

    return asyncio.run(_send())


def main():
    parser = argparse.ArgumentParser(
        description="Send Image: 向 TG/DC 发送图片",
    )
    parser.add_argument(
        "image", help="本地图片路径或网络 URL",
    )
    parser.add_argument(
        "--caption", "-c", default="", help="图片说明文字",
    )
    parser.add_argument(
        "--channel", "-ch", default="",
        choices=["telegram", "discord", ""],
        help="指定通道（不填则自动检测）",
    )
    args = parser.parse_args()

    config = load_config()
    channel = args.channel or detect_channel(config)
    if not channel:
        print("❌ 无可用通道（TG/DC 均未启用）")
        sys.exit(1)

    # 处理图片来源
    tmp_file = None
    if is_url(args.image):
        image_path = download_url_to_temp(args.image)
        if not image_path:
            sys.exit(1)
        tmp_file = image_path
    else:
        image_path = args.image
        if not Path(image_path).exists():
            print(f"❌ 文件不存在: {image_path}")
            sys.exit(1)

    try:
        if channel == "telegram":
            ok = send_tg_photo(config, image_path, args.caption)
        else:
            ok = send_dc_photo(config, image_path, args.caption)
        if not ok:
            sys.exit(1)
    finally:
        # 清理临时文件
        if tmp_file:
            try:
                os.unlink(tmp_file)
            except Exception:
                pass


if __name__ == "__main__":
    main()
