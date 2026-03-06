---
name: token_usage
description: 通过主动询问获知过去一段时间的 LLM Token 消耗情况
metadata: { "copaw": { "emoji": "📊" } }
---

# Token 消耗查询

当用户询问关于 Token 消耗、API 用量、或「用了多少 token」时，使用 `get_token_usage` 工具查询统计数据。

## 使用场景

- 用户问：「最近用了多少 token？」
- 用户问：「这个月 API 调用花了多少？」
- 用户问：「帮我看看 token 消耗情况」
- 用户问：「各个模型分别用了多少 token？」

## 工具说明

`get_token_usage` 支持两个可选参数：

- `days`：查询过去 N 天的数据（默认 30，范围 1–365）
- `model_name`：按模型名筛选（可选）

## 示例

用户：「最近 7 天用了多少 token？」

→ 调用 `get_token_usage(days=7)`

用户：「qwen3-max 这个模型用了多少？」

→ 调用 `get_token_usage(model_name="qwen3-max")` 或 `get_token_usage(days=30, model_name="qwen3-max")`

## 注意

- 数据按日期和模型名记录，存储在 `~/.copaw/token_usage.json`
- 仅统计通过 CoPaw Agent 发起的 LLM 调用的 token
- 控制台「设置 → Token 消耗」页面可查看更详细的图表和表格
