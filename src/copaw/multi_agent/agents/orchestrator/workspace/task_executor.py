#!/usr/bin/env python3
"""
任务自动执行器
总调度·范冰冰 管理
确保任务分配后立刻执行
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

# 代理工作区根目录
AGENTS_DIR = Path("/Users/light/.copaw/agent_system/agents")

def load_agent_config(agent_id):
    """加载代理配置"""
    config_path = AGENTS_DIR / agent_id / "agent.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None

def execute_agent_task(agent_id, task_file):
    """执行代理任务"""
    agent_config = load_agent_config(agent_id)
    if not agent_config:
        print(f"[错误] 无法加载代理配置: {agent_id}")
        return False
    
    agent_name = agent_config.get('personality', {}).get('name', agent_id)
    model = agent_config.get('model', {}).get('model_id', 'qwen3.5-plus')
    
    print(f"[执行] {agent_name} ({agent_id}) 开始执行任务...")
    print(f"[模型] 使用: {model}")
    
    # 读取任务内容
    task_path = AGENTS_DIR / agent_id / "workspace" / task_file
    if not task_path.exists():
        print(f"[错误] 任务文件不存在: {task_path}")
        return False
    
    with open(task_path, 'r', encoding='utf-8') as f:
        task_content = f.read()
    
    # 构建执行命令
    # 使用 copaw 命令执行代理任务
    cmd = [
        "copaw", "run",
        "--agent", agent_id,
        "--task", str(task_path),
        "--model", model
    ]
    
    print(f"[命令] {' '.join(cmd)}")
    
    # 执行任务
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        
        if result.returncode == 0:
            print(f"[成功] {agent_name} 任务执行完成")
            return True
        else:
            print(f"[失败] {agent_name} 任务执行失败")
            print(f"[错误] {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[超时] {agent_name} 任务执行超时")
        return False
    except Exception as e:
        print(f"[异常] {agent_name} 任务执行异常: {e}")
        return False

def check_and_execute_pending_tasks():
    """检查并执行待处理任务"""
    active_tasks_file = AGENTS_DIR / "orchestrator" / "workspace" / "active_tasks.json"
    
    if not active_tasks_file.exists():
        print("[信息] 没有活跃任务")
        return
    
    with open(active_tasks_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tasks = data.get('tasks', [])
    
    for task in tasks:
        if task.get('status') == 'in_progress':
            agent_id = task.get('agent')
            # 查找代理工作区中的任务文件
            agent_workspace = AGENTS_DIR / agent_id / "workspace"
            
            # 查找最新的 .md 任务文件
            task_files = list(agent_workspace.glob("*.md"))
            if task_files:
                # 按修改时间排序，取最新的
                latest_task = max(task_files, key=lambda p: p.stat().st_mtime)
                
                print(f"\n[触发] 发现待执行任务: {task.get('name')}")
                print(f"[代理] {agent_id}")
                print(f"[文件] {latest_task.name}")
                
                # 执行任务
                success = execute_agent_task(agent_id, latest_task.name)
                
                if success:
                    # 更新任务状态
                    task['status'] = 'executing'
                    task['started_at'] = datetime.now().isoformat()
                
                # 保存更新
                with open(active_tasks_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("[🎯 总调度·范冰冰] 任务执行器启动")
    check_and_execute_pending_tasks()
