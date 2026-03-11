#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""企业微信 WebSocket 连接诊断工具.

用于排查企业微信 Channel 连接问题。

使用方法：
    python scripts/diagnose_wecom.py <bot_id> <secret>

或者从环境变量读取：
    export WECOM_BOT_ID="your_bot_id"
    export WECOM_SECRET="your_secret"
    python scripts/diagnose_wecom.py
"""

import asyncio
import json
import os
import sys

import websockets


async def test_wecom_connection(bot_id: str, secret: str):
    """测试企业微信 WebSocket 连接."""
    ws_url = "wss://openws.work.weixin.qq.com"

    print(f"[1/4] 测试 WebSocket 连接到: {ws_url}")
    print(f"      Bot ID: {bot_id[:8]}... (已脱敏)")
    print(f"      Secret: {secret[:8]}... (已脱敏)")
    print()

    try:
        print("[2/4] 建立 WebSocket 连接...")
        async with websockets.connect(
            ws_url,
            ping_interval=None,
            ping_timeout=None,
            open_timeout=30,
        ) as ws:
            print("      ✓ WebSocket 连接成功")
            print()

            print("[3/4] 发送订阅请求...")
            subscribe_msg = {
                "cmd": "aibot_subscribe",
                "headers": {"req_id": "test-connection"},
                "body": {
                    "bot_id": bot_id,
                    "secret": secret,
                },
            }

            await ws.send(json.dumps(subscribe_msg))
            print("      ✓ 订阅请求已发送")
            print()

            print("[4/4] 等待订阅响应...")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                resp_data = json.loads(response)

                errcode = resp_data.get("errcode")
                errmsg = resp_data.get("errmsg", "")

                if errcode == 0:
                    print("      ✓ 订阅成功！")
                    print()
                    print("=" * 60)
                    print("诊断结果：连接正常")
                    print("=" * 60)
                    return True
                else:
                    print(f"      ✗ 订阅失败: errcode={errcode}, errmsg={errmsg}")
                    print()
                    print("=" * 60)
                    print("诊断结果：订阅失败")
                    print("=" * 60)
                    print()
                    print("可能原因：")
                    print("  1. bot_id 或 secret 配置错误")
                    print("  2. 机器人未启用或已被禁用")
                    print("  3. 企业微信后台配置问题")
                    print()
                    print("解决方案：")
                    print("  1. 检查企业微信管理后台的机器人配置")
                    print("  2. 确认 bot_id 和 secret 是否正确")
                    print("  3. 确认机器人状态是否为启用")
                    return False

            except asyncio.TimeoutError:
                print("      ✗ 等待响应超时（10秒）")
                print()
                print("=" * 60)
                print("诊断结果：订阅响应超时")
                print("=" * 60)
                print()
                print("可能原因：")
                print("  1. 网络连接不稳定")
                print("  2. 企业微信服务器无响应")
                print("  3. bot_id 或 secret 错误导致服务器静默拒绝")
                return False

    except ConnectionResetError as e:
        print(f"      ✗ 连接被重置: {e}")
        print()
        print("=" * 60)
        print("诊断结果：连接被服务器重置")
        print("=" * 60)
        print()
        print("可能原因：")
        print("  1. bot_id 或 secret 配置错误，服务器主动断开连接")
        print("  2. 网络环境问题（防火墙、代理等）")
        print("  3. 企业微信服务器拒绝连接")
        print()
        print("解决方案：")
        print("  1. 仔细检查 bot_id 和 secret 配置")
        print("  2. 确认网络可以访问 openws.work.weixin.qq.com")
        print("  3. 检查是否有防火墙或代理阻止 WebSocket 连接")
        print("  4. 尝试在企业微信管理后台重新生成 secret")
        return False

    except ConnectionRefusedError as e:
        print(f"      ✗ 连接被拒绝: {e}")
        print()
        print("=" * 60)
        print("诊断结果：无法连接到服务器")
        print("=" * 60)
        print()
        print("可能原因：")
        print("  1. 网络无法访问企业微信服务器")
        print("  2. 防火墙阻止了连接")
        print("  3. DNS 解析失败")
        return False

    except Exception as e:
        print(f"      ✗ 连接失败: {e}")
        print()
        print("=" * 60)
        print("诊断结果：连接异常")
        print("=" * 60)
        print(f"错误详情: {type(e).__name__}: {e}")
        return False


def main():
    """主函数."""
    print("=" * 60)
    print("企业微信 WebSocket 连接诊断工具")
    print("=" * 60)
    print()

    # 从命令行参数或环境变量读取
    if len(sys.argv) >= 3:
        bot_id = sys.argv[1]
        secret = sys.argv[2]
    else:
        bot_id = os.getenv("WECOM_BOT_ID", "")
        secret = os.getenv("WECOM_SECRET", "")

    if not bot_id or not secret:
        print("错误：未提供 bot_id 或 secret")
        print()
        print("使用方法：")
        print("  1. 命令行参数：")
        print("     python scripts/diagnose_wecom.py <bot_id> <secret>")
        print()
        print("  2. 环境变量：")
        print("     export WECOM_BOT_ID='your_bot_id'")
        print("     export WECOM_SECRET='your_secret'")
        print("     python scripts/diagnose_wecom.py")
        sys.exit(1)

    # 运行测试
    result = asyncio.run(test_wecom_connection(bot_id, secret))

    if result:
        print()
        print("✓ 诊断完成：连接正常，可以正常使用企业微信 Channel")
        sys.exit(0)
    else:
        print()
        print("✗ 诊断完成：连接异常，请根据上述提示排查问题")
        sys.exit(1)


if __name__ == "__main__":
    main()
