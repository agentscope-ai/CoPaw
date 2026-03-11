"""
Agent 基类 - 所有 Agent 的基础实现
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path


class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    DISCUSSING = "discussing"
    ERROR = "error"


@dataclass
class AgentCapability:
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)


@dataclass 
class AgentState:
    agent_id: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    message: str = "Ready"


class AgentBase:
    """Agent 基类"""
    
    def __init__(self, agent_dir: Path):
        self.agent_dir = agent_dir
        self.config = self._load_config()
        self.identity = self._load_identity()
        self.id = self.config.get('id', agent_dir.name)
        self.name = self.config.get('name', self.id)
        self.role = self.config.get('role', '')
        self.avatar = self.config.get('avatar', '🤖')
        
        # 能力
        self.capabilities = [
            AgentCapability(**cap) if isinstance(cap, dict) else cap
            for cap in self.config.get('capabilities', [])
        ]
        
        # 工具
        self.tools = self.config.get('tools', [])
        
        # 状态
        self.state = AgentState(agent_id=self.id)
        
        # 记忆
        self.memory_dir = agent_dir / 'memory'
        self.memory_dir.mkdir(exist_ok=True)
        
        # 回调
        self.on_status_change: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
        
    def _load_config(self) -> dict:
        config_file = self.agent_dir / 'agent.yaml'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_identity(self) -> str:
        identity_file = self.agent_dir / 'identity.md'
        if identity_file.exists():
            return identity_file.read_text(encoding='utf-8')
        return ""
    
    async def execute(self, task: 'Task') -> dict:
        """执行任务 - 模拟执行"""
        await asyncio.sleep(1)  # 模拟处理时间
        return {
            'agent': self.id,
            'status': 'success',
            'message': f'{self.name} 完成了分配的任务',
            'data': {'processed': True}
        }
    
    async def discuss(self, topic: str, context: Dict, participants: List['AgentBase']) -> str:
        """参与讨论"""
        self.state.status = AgentStatus.DISCUSSING
        self.state.message = f"讨论中: {topic[:30]}..."
        self._notify_status_change()
        
        await asyncio.sleep(0.5)  # 模拟思考时间
        
        # 根据角色和能力生成智能回复
        response = await self._generate_discussion_response(topic, context, participants)
        
        self.state.status = AgentStatus.IDLE
        self.state.message = "Ready"
        self._notify_status_change()
        
        return response
    
    async def _generate_discussion_response(self, topic: str, context: Dict, participants: List['AgentBase']) -> str:
        """生成讨论回复 - 基于角色智能生成"""
        round_num = context.get('round', 1)
        previous_messages = context.get('previous_discussion', [])
        
        # 第一轮：介绍自己能做什么
        if round_num == 1:
            caps_str = '、'.join([c.name for c in self.capabilities[:2]])
            return f"我是{self.name}，擅长{caps_str}。根据任务需求，我可以负责{self._get_responsibility(topic)}部分的工作。"
        
        # 后续轮：根据讨论进展发言
        if len(previous_messages) > 0:
            last_msg = previous_messages[-1] if previous_messages else None
            if last_msg and last_msg.get('agent_id') != self.id:
                return f"同意{last_msg.get('agent_name', '同事')}的观点。我这边可以配合完成{self._get_responsibility(topic)}的工作，等大家准备好后我就可以开始。"
        
        return f"我准备好开始执行{self._get_responsibility(topic)}相关的工作了。"
    
    def _get_responsibility(self, topic: str) -> str:
        """根据任务主题和能力确定责任"""
        topic_lower = topic.lower()
        
        if '基金' in topic_lower or '投资' in topic_lower:
            if any('fund' in c.name.lower() or 'analysis' in c.name.lower() for c in self.capabilities):
                return "基金数据分析"
            if any('data' in c.name.lower() for c in self.capabilities):
                return "数据处理"
            if any('knowledge' in c.name.lower() for c in self.capabilities):
                return "历史数据查询"
        
        if '代码' in topic_lower or '编程' in topic_lower:
            if any('code' in c.name.lower() or 'development' in c.name.lower() for c in self.capabilities):
                return "代码开发"
            if any('debug' in c.name.lower() for c in self.capabilities):
                return "Bug修复"
        
        return "专业领域"
    
    def update_status(self, status: AgentStatus, message: str = "", task_id: str = None):
        """更新状态"""
        self.state.status = status
        self.state.message = message
        self.state.current_task = task_id
        self.state.last_activity = datetime.now()
        self._notify_status_change()
    
    def _notify_status_change(self):
        if self.on_status_change:
            self.on_status_change(self.state)
    
    def can_handle(self, task_type: str, keywords: List[str]) -> float:
        """评估是否能处理该任务，返回置信度 0-1"""
        score = 0.0
        for cap in self.capabilities:
            if task_type.lower() in cap.name.lower():
                score += 0.5
            for kw in keywords:
                if kw.lower() in cap.name.lower() or kw.lower() in [k.lower() for k in cap.keywords]:
                    score += 0.2
        return min(score, 1.0)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'avatar': self.avatar,
            'status': self.state.status.value,
            'current_task': self.state.current_task,
            'message': self.state.message,
            'last_activity': self.state.last_activity.isoformat(),
            'capabilities': [{'name': c.name, 'description': c.description} for c in self.capabilities],
            'tools': self.tools
        }