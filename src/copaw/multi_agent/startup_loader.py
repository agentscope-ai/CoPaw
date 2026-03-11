#!/usr/bin/env python3
"""
Copaw 启动加载器
在系统启动时自动加载特工小队规则
将此文件配置为 Copaw 启动时自动执行
"""

import os
import sys
from pathlib import Path

def load_agent_system_rules():
    """加载特工小队系统规则"""
    
    memory_file = Path("/Users/light/.copaw/MEMORY.md")
    
    if not memory_file.exists():
        print("[⚠️] MEMORY.md 不存在，跳过加载")
        return
    
    print("[🎯] 正在加载特工小队系统规则...")
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取特工小队部分
    if "## 🚨 强制加载：特工小队系统" in content:
        start = content.find("## 🚨 强制加载：特工小队系统")
        end = content.find("---", start + 1)
        if end == -1:
            end = len(content)
        
        agent_rules = content[start:end]
        
        # 设置环境变量，让 Copaw 能读取到
        os.environ['COPAW_AGENT_SYSTEM_RULES'] = agent_rules
        
        print("[✅] 特工小队规则已加载")
        print("[📋] 7个代理已就绪：")
        print("  🎯 范冰冰（总调度）")
        print("  💰 黄蓉（基金专员）")
        print("  📊 小龙女（数据专员）")
        print("  💻 赵敏（编程专员）")
        print("  🧠 王语嫣（知识库）")
        print("  ✍️ 任盈盈（小说作家）")
        print("  🔍 周芷若（纪委）")
        
    else:
        print("[⚠️] MEMORY.md 中未找到特工小队规则")

# 自动执行
load_agent_system_rules()
