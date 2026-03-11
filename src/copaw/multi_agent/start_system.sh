#!/bin/bash
# 多代理系统启动脚本

echo "[🎯 总调度] 启动多代理系统..."

# 1. 检查环境
echo "[检查] 检查代理配置..."
for agent in orchestrator fund_manager data_processor coding_master knowledge_base novel_writer discipline_inspector; do
    if [ -f "/Users/light/.copaw/agent_system/agents/$agent/agent.yaml" ]; then
        echo "  ✅ $agent 配置存在"
    else
        echo "  ❌ $agent 配置缺失"
    fi
done

# 2. 启动任务执行器
echo "[启动] 任务执行器..."
python3 /Users/light/.copaw/agent_system/agent_runner.py

# 3. 启动纪委监控
echo "[启动] 纪委监控系统..."
python3 /Users/light/.copaw/agent_system/agents/discipline_inspector/workspace/inspector_daemon.py

# 4. 显示状态
echo ""
echo "[状态] 系统启动完成"
echo "代理数量: 7"
echo "纪委监控: 已启动"
echo "定时任务: 已配置"
echo ""
echo "[🎯 总调度] 系统就绪，等待指令！"
