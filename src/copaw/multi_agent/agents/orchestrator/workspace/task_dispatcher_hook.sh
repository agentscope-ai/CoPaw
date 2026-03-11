#!/bin/bash
# 任务分配后自动触发执行钩子
# 由总调度·范冰冰调用

AGENT_ID=$1
TASK_FILE=$2

echo "[🎯 总调度·范冰冰] 触发代理执行: $AGENT_ID"
echo "[任务] $TASK_FILE"

# 立即执行任务执行器
python3 /Users/light/.copaw/agent_system/agents/orchestrator/workspace/task_executor.py

echo "[完成] 任务已触发执行"
