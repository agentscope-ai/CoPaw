---
name: dc-notify
description: 长任务完成后自动推送 Discord 通知。当 CC 执行耗时较长的任务（预估>1分钟）完成后触发，向用户的 Discord 频道发送结果摘要。用于"跑完了喊我"的场景。
version: "1.0.0"
---

# DC Notify — 长任务完成通知（Discord 版）

CC 跑完长任务后，自动往用户的 Discord 频道推一条通知，不用一直盯着。

## 何时触发

CC 自动判断以下场景时，在**任务完成后**调用：
- Playwright 批量测试跑完
- 报告生成完毕（Word/Markdown）
- 批量文件操作完成
- 大量数据抓取/整理完成
- 任何用户说"跑完了通知我"的场景

**不触发的场景**：
- 日常简单对话
- 1-2 步的快速任务
- 当前通道就是 Discord 时（已经在聊天窗里了，不用重复通知）

## 使用方法

### 基础通知
```bash
python "C:\Users\giwan.CGG\.copaw\customized_skills\dc-notify\scripts\notify.py" "✅ 测试报告已生成，共发现 3 个 bug"
```

### 带标题和耗时
```bash
python "C:\Users\giwan.CGG\.copaw\customized_skills\dc-notify\scripts\notify.py" "✅ 5 个 API 全部通过" --title "API 冒烟测试" --duration "1m45s"
```

### 失败通知
```bash
python "C:\Users\giwan.CGG\.copaw\customized_skills\dc-notify\scripts\notify.py" "❌ 第3步执行失败：连接超时" --title "GGSLOT 自动化测试"
```

### 指定频道
```bash
python "C:\Users\giwan.CGG\.copaw\customized_skills\dc-notify\scripts\notify.py" "✅ 完成" --channel-id 1234567890
```

## 消息格式示例

Discord 支持 Markdown，消息格式会更好看：

```
🔔 **API 冒烟测试**
✅ 5 个 API 全部通过
⏱ 耗时: 1m45s

*— CC 自动通知*
```

## 配置

- Bot Token 从 `~/.copaw/config.json` 的 `channels.discord.bot_token` 自动读取
- Channel ID 从 `last_dispatch.session_id` 自动解析（格式 `discord:ch:xxx`）
- 也可通过 `--channel-id` 手动指定
- 无需额外配置，开箱即用
- 不依赖第三方库，纯 Python 标准库

## ⚠️ 注意事项

- 通知内容不包含敏感数据（API Key、密码等）
- 只发结果摘要，不发完整日志
- 网络不通时静默失败，不阻塞主任务
