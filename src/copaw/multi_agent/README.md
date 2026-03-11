# Copaw Agent System

一个独立运行的多 Agent 协作系统，支持 Agent 间讨论与协作。

## 快速启动

```bash
cd ~/.copaw/agent_system
./start.sh
```

- Dashboard: http://localhost:3000
- API: http://localhost:8766

## 架构

```
┌─────────────────────────────────────────────┐
│                 Dashboard                    │
│              (React + Vite)                  │
└──────────────────┬──────────────────────────┘
                   │ WebSocket + REST
┌──────────────────▼──────────────────────────┐
│              State Service                   │
│            (状态收集与推送)                   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              Orchestrator                    │
│            (任务调度中心)                     │
└──────────────────┬──────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌───────┐    ┌───────┐    ┌───────┐
│ Agent │    │ Agent │    │ Agent │
│   💰  │    │   💻  │    │   📊  │
└───────┘    └───────┘    └───────┘
```

## Agent 协作模式

### 单 Agent 执行
简单任务直接分发给最合适的 Agent 执行。

### 协作讨论
复杂任务会启动多轮讨论：
1. Orchestrator 分析任务复杂度
2. 选择相关 Agent 参与
3. Agent 轮流发言讨论分工
4. 按讨论结果分工执行
5. 汇总结果返回

## API

### REST
- `GET /api/agents` - 获取所有 Agent 状态
- `GET /api/agents/{id}` - 获取单个 Agent 详情
- `POST /api/tasks` - 创建新任务
- `GET /api/tasks` - 获取任务列表
- `GET /api/tasks/{id}` - 获取任务详情

### WebSocket
连接 `ws://localhost:8766/ws`，接收实时状态更新。

消息类型：
- `agent_status` - Agent 状态变化
- `task_update` - 任务状态更新
- `discussion_message` - 讨论消息