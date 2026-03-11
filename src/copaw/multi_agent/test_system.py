#!/usr/bin/env python3
"""
Copaw Agent System - 测试脚本
验证核心功能是否正常
"""
import sys
import asyncio
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from core import AgentBase, Orchestrator, Task, TaskStatus
from core.orchestrator import TaskStatus


async def test_system():
    print("🧪 测试 Copaw Agent System\n")
    
    # 1. 加载 Agents
    print("1️⃣ 加载 Agents...")
    agents_dir = Path(__file__).parent / 'agents'
    agents = {}
    
    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir():
            agent = AgentBase(agent_dir)
            agents[agent.id] = agent
            print(f"   ✅ {agent.avatar} {agent.name} ({agent.id})")
    
    assert len(agents) > 0, "No agents loaded!"
    print(f"   共加载 {len(agents)} 个 Agent\n")
    
    # 2. 创建 Orchestrator
    print("2️⃣ 创建 Orchestrator...")
    config = {'discussion': {'max_rounds': 3}}
    orchestrator = Orchestrator(agents, config)
    print("   ✅ Orchestrator 创建成功\n")
    
    # 3. 测试任务分析
    print("3️⃣ 测试任务分析...")
    analysis = await orchestrator._analyze_task("分析我的基金组合", {})
    print(f"   任务类型: {analysis['task_types']}")
    print(f"   复杂度: {analysis['complexity']}")
    print(f"   需要协作: {analysis['needs_collaboration']}\n")
    
    # 4. 测试 Agent 选择
    print("4️⃣ 测试 Agent 选择...")
    for task_type in ['fund_analysis', 'coding', 'data_processing', 'knowledge_query']:
        best = orchestrator._select_best_agent([task_type])
        if best:
            print(f"   {task_type} → {best.avatar} {best.name}")
    
    # 5. 测试协作任务
    print("\n5️⃣ 测试协作任务...")
    task = await orchestrator.submit_task("分析基金组合并生成报告", {
        'fund_codes': ['000001', '110022']
    })
    print(f"   任务 ID: {task.id}")
    print(f"   状态: {task.status.value}")
    
    # 等待任务完成
    for _ in range(10):
        await asyncio.sleep(0.5)
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            break
    
    print(f"   最终状态: {task.status.value}")
    print(f"   参与者: {task.participants}")
    print(f"   步骤数: {len(task.steps)}")
    
    if task.discussion_history:
        print(f"   讨论消息数: {len(task.discussion_history)}")
        for msg in task.discussion_history[:3]:
            print(f"      [{msg['agent_name']}]: {msg['message'][:50]}...")
    
    print("\n✅ 测试完成!")
    return True


if __name__ == '__main__':
    asyncio.run(test_system())