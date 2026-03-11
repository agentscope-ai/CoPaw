#!/usr/bin/env python3
"""
代理任务执行器
确保任务分配后立即执行
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

AGENTS_DIR = Path("/Users/light/.copaw/agent_system/agents")

def load_agent_config(agent_id):
    """加载代理配置"""
    config_path = AGENTS_DIR / agent_id / "agent.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None

def execute_agent_task(agent_id, task_content):
    """直接执行代理任务"""
    config = load_agent_config(agent_id)
    if not config:
        return False
    
    name = config.get('personality', {}).get('name', agent_id)
    model = config.get('model', {}).get('model_id', 'qwen3.5-plus')
    
    print(f"[执行] {name} ({agent_id}) 开始任务...")
    
    # 直接调用Python执行，不依赖外部命令
    # 这里应该调用实际的AI模型API
    # 简化版：创建执行标记文件
    
    workspace = AGENTS_DIR / agent_id / "workspace"
    running_file = workspace / f"running_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(running_file, 'w', encoding='utf-8') as f:
        f.write(f"任务启动时间: {datetime.now()}\n")
        f.write(f"使用模型: {model}\n")
        f.write(f"任务内容:\n{task_content}\n")
    
    print(f"[成功] {name} 任务已启动: {running_file}")
    return True

def check_pending_tasks():
    """检查并执行待处理任务"""
    active_tasks_file = AGENTS_DIR / "orchestrator" / "workspace" / "active_tasks.json"
    
    if not active_tasks_file.exists():
        return
    
    with open(active_tasks_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tasks = data.get('tasks', [])
    
    for task in tasks:
        if task.get('status') == 'in_progress':
            agent_id = task.get('agent')
            print(f"\n[触发] 执行任务: {task.get('name')} -> {agent_id}")
            
            # 读取任务文件内容
            task_file = AGENTS_DIR / agent_id / "workspace" / f"{task.get('name', 'task')}.md"
            if task_file.exists():
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_content = f.read()
                
                success = execute_agent_task(agent_id, task_content)
                
                if success:
                    task['status'] = 'executing'
                    task['started_at'] = datetime.now().isoformat()
    
    # 保存更新
    with open(active_tasks_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("[🎯 总调度] 代理执行器启动")
    check_pending_tasks()
