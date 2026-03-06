# Token 消耗统计实现说明

## 概述

CoPaw 在每次访问 LLM 时记录 token 消耗，并按日期、模型名区分存储。用户可通过控制台页面或主动询问 Agent 查询历史消耗。

## 实现方案选择

### 为何未采用 OpenTelemetry SpanProcessor

AgentScope 原生集成了 OpenTelemetry API。在开启 trace 时，该 API 会执行；但在与 OpenTelemetry Auto Instrumentation 共存时，为避免 Span 重复，原生 trace API 可能不执行。此时全局 `TracerProvider` 可能来自：

- AgentScope 自身
- Auto Instrumentation

因此，通过向 `TracerProvider` 注册 `SpanProcessor` 来统计 token 的方案存在不确定性：

1. **TracerProvider 来源不确定**：无法保证当前使用的 TracerProvider 与 LLM 调用链路一致
2. **Span 可能不创建**：在 Auto Instrumentation 场景下，AgentScope 的 trace 可能被跳过，导致无法通过 Span 获取 token 信息
3. **重复统计风险**：若两套 trace 同时生效，可能重复统计

### 采用的方案：模型层包装

改为在**模型调用层**直接拦截并记录 token，不依赖 OpenTelemetry：

1. **`TokenRecordingModelWrapper`**：包装 `ChatModelBase`，在每次 `__call__` 返回时从 `ChatResponse.usage` 提取 token 信息
2. **`model_factory`**：在 `create_model_and_formatter()` 中，将创建好的模型用 `TokenRecordingModelWrapper` 包装后再返回
3. **存储**：通过 `record_token_usage()` 写入 `~/.copaw/token_usage.json`，按 `日期 -> 模型名 -> 统计` 组织

该方案：

- 不依赖 OpenTelemetry 或 trace 配置
- 与 Auto Instrumentation 无冲突
- 覆盖所有通过 CoPaw Agent 发起的 LLM 调用（本地模型、远程模型均支持，只要返回 `ChatResponse` 且带 `usage`）

## 模块结构

```
src/copaw/token_usage/
├── __init__.py
├── storage.py      # 存储路径 (get_token_usage_path)
├── record.py       # 记录 (record_token_usage)
├── query.py        # 查询 (query_token_usage, get_token_usage_summary)
└── model_wrapper.py # 模型包装器 (TokenRecordingModelWrapper)
```

## 数据格式

`token_usage.json` 结构示例：

```json
{
  "2026-03-04": {
    "qwen3-max": {
      "prompt_tokens": 1200,
      "completion_tokens": 450,
      "total_tokens": 1650,
      "call_count": 5
    }
  }
}
```

## 使用方式

1. **控制台**：设置 → Token 消耗，选择日期范围查看
2. **API**：`GET /api/token-usage?start_date=...&end_date=...&model=...`
3. **Agent 工具**：用户询问「用了多少 token」时，Agent 调用 `get_token_usage` 工具
4. **SKILL**：`token_usage` 技能提供使用说明，引导 Agent 在合适场景调用该工具

## 环境变量

- `COPAW_TOKEN_USAGE_FILE`：覆盖默认存储文件名（默认 `token_usage.json`）
- 存储目录由 `COPAW_WORKING_DIR` 决定（默认 `~/.copaw`）
