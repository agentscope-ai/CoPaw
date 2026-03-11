#!/usr/bin/env python3
"""
纪委监控守护进程
每日自动检查所有代理
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta

AGENTS_DIR = Path("/Users/light/.copaw/agent_system/agents")
INSPECTOR_DIR = AGENTS_DIR / "discipline_inspector" / "workspace"

class InspectorDaemon:
    def __init__(self):
        self.name = "周芷若"
        self.agents = [
            "fund_manager",
            "data_processor", 
            "coding_master",
            "knowledge_base",
            "novel_writer"
        ]
        
    def log(self, message):
        print(f"[🔍 纪委·{self.name}] {message}")
        
    def check_agent_status(self, agent_id):
        """检查单个代理状态"""
        workspace = AGENTS_DIR / agent_id / "workspace"
        
        # 检查最近修改的文件
        recent_files = []
        for f in workspace.glob("*.md"):
            stat = f.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)
            recent_files.append({
                'file': f.name,
                'modified': modified,
                'size': stat.st_size
            })
        
        # 按时间排序
        recent_files.sort(key=lambda x: x['modified'], reverse=True)
        
        # 检查是否有running标记
        running_files = list(workspace.glob("running_*.txt"))
        
        return {
            'agent': agent_id,
            'recent_files': recent_files[:3],
            'running_tasks': len(running_files),
            'status': 'active' if recent_files else 'idle'
        }
        
    def generate_daily_report(self):
        """生成每日监察报告"""
        self.log("开始每日检查...")
        
        report = {
            'date': datetime.now().isoformat(),
            'inspector': self.name,
            'agents_status': []
        }
        
        for agent_id in self.agents:
            status = self.check_agent_status(agent_id)
            report['agents_status'].append(status)
            
            # 简单判断
            if status['status'] == 'idle':
                self.log(f"⚠️ {agent_id} 处于空闲状态")
            else:
                self.log(f"✅ {agent_id} 正常工作中")
        
        # 保存报告
        report_file = INSPECTOR_DIR / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"报告已保存: {report_file}")
        return report
        
    def run(self):
        """运行检查"""
        self.log("纪委监控系统启动")
        report = self.generate_daily_report()
        self.log("每日检查完成")
        return report

if __name__ == "__main__":
    inspector = InspectorDaemon()
    inspector.run()
