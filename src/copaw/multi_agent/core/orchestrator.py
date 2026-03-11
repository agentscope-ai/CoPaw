"""
Orchestrator - 任务调度与协作中心
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
from pathlib import Path

from .agent_base import AgentBase, AgentStatus


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DISCUSSING = "discussing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    name: str
    status: str = "pending"
    agent_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Task:
    id: str
    request: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 执行信息
    assigned_to: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    steps: List[TaskStep] = field(default_factory=list)
    
    # 讨论
    discussion_history: List[Dict] = field(default_factory=list)
    
    # 结果
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    # 指标
    metrics: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'request': self.request,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'assigned_to': self.assigned_to,
            'participants': self.participants,
            'steps': [{'name': s.name, 'status': s.status, 'agent_id': s.agent_id} for s in self.steps],
            'discussion_history': self.discussion_history,
            'result': self.result,
            'error': self.error,
            'metrics': self.metrics
        }


class Orchestrator:
    """调度中心 - 负责任务分发、协作协调、讨论管理"""
    
    def __init__(self, agents: Dict[str, AgentBase], config: dict):
        self.agents = agents
        self.config = config
        self.tasks: Dict[str, Task] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # 回调
        self.on_task_update: Optional[callable] = None
        self.on_discussion_message: Optional[callable] = None
        
    async def submit_task(self, request: str, context: dict = None) -> Task:
        """提交新任务"""
        task_id = f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        task = Task(
            id=task_id,
            request=request
        )
        
        self.tasks[task_id] = task
        self._notify_task_update(task)
        
        # 异步执行
        asyncio.create_task(self._execute_task(task, context or {}))
        
        return task
    
    async def _execute_task(self, task: Task, context: dict):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._notify_task_update(task)
        
        try:
            # 1. 分析任务
            analysis = await self._analyze_task(task.request, context)
            task.metrics['analysis'] = analysis
            
            # 2. 选择最佳 Agent 或启动讨论
            if analysis.get('complexity') == 'high' or analysis.get('needs_collaboration'):
                await self._collaborative_execution(task, analysis, context)
            else:
                await self._single_agent_execution(task, analysis, context)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
        
        self._notify_task_update(task)
    
    async def _analyze_task(self, request: str, context: dict) -> dict:
        """分析任务类型和复杂度"""
        # 简单的关键词分析 (实际会用 LLM)
        request_lower = request.lower()
        
        # 判断任务类型
        task_types = []
        if any(kw in request_lower for kw in ['基金', '投资', '净值', '股票']):
            task_types.append('fund_analysis')
        if any(kw in request_lower for kw in ['代码', '编程', '开发', '调试', 'bug']):
            task_types.append('coding')
        if any(kw in request_lower for kw in ['数据', '处理', '分析', '报表']):
            task_types.append('data_processing')
        if any(kw in request_lower for kw in ['查询', '搜索', '知识', '文档']):
            task_types.append('knowledge_query')
        
        # 判断复杂度
        complexity = 'low'
        if len(task_types) > 1 or any(kw in request_lower for kw in ['复杂', '综合', '协作', '一起']):
            complexity = 'high'
        elif len(request) > 100 or '详细' in request_lower:
            complexity = 'medium'
        
        return {
            'task_types': task_types,
            'complexity': complexity,
            'needs_collaboration': len(task_types) > 1 or complexity == 'high'
        }
    
    async def _single_agent_execution(self, task: Task, analysis: dict, context: dict):
        """单 Agent 执行"""
        # 选择最佳 Agent
        best_agent = self._select_best_agent(analysis['task_types'])
        if not best_agent:
            raise Exception("No suitable agent found")
        
        task.assigned_to = best_agent.id
        task.participants = [best_agent.id]
        
        # 添加步骤
        task.steps = [TaskStep(name="执行任务", status="running", agent_id=best_agent.id)]
        self._notify_task_update(task)
        
        # 执行
        best_agent.update_status(AgentStatus.WORKING, f"执行: {task.request[:30]}...", task.id)
        result = await best_agent.execute(task)
        
        task.steps[0].status = "completed"
        task.result = result
        best_agent.update_status(AgentStatus.IDLE, "Ready")
    
    async def _collaborative_execution(self, task: Task, analysis: dict, context: dict):
        """协作执行 - Agent 之间讨论并协作"""
        task.status = TaskStatus.DISCUSSING
        self._notify_task_update(task)
        
        # 选择参与者
        participants = self._select_participants(analysis['task_types'])
        task.participants = [p.id for p in participants]
        
        # 为每个参与者设置状态
        for agent in participants:
            agent.update_status(AgentStatus.DISCUSSING, "参与协作讨论", task.id)
        
        # Step 1: 讨论阶段 - 让 Agent 们讨论如何分工
        task.steps.append(TaskStep(name="协作讨论", status="running"))
        self._notify_task_update(task)
        
        discussion_topic = f"如何协作完成: {task.request}"
        
        # 多轮讨论
        max_rounds = self.config.get('discussion', {}).get('max_rounds', 5)
        for round_num in range(max_rounds):
            round_messages = []
            
            for agent in participants:
                # 每个 Agent 发表意见
                msg = await agent.discuss(
                    topic=discussion_topic,
                    context={
                        'round': round_num + 1,
                        'task': task.request,
                        'previous_discussion': task.discussion_history,
                        'other_participants': [p.id for p in participants if p.id != agent.id]
                    },
                    participants=participants
                )
                
                message = {
                    'round': round_num + 1,
                    'agent_id': agent.id,
                    'agent_name': agent.name,
                    'avatar': agent.avatar,
                    'message': msg,
                    'timestamp': datetime.now().isoformat()
                }
                
                round_messages.append(message)
                task.discussion_history.append(message)
                self._notify_task_update(task)
                
                # 通知讨论消息
                if self.on_discussion_message:
                    self.on_discussion_message(task.id, message)
            
            # 检查是否达成共识 (简化：两轮后继续)
            if round_num >= 1:
                break
        
        task.steps[0].status = "completed"
        
        # Step 2: 分工执行
        task.status = TaskStatus.RUNNING
        task.steps.append(TaskStep(name="分工执行", status="running"))
        self._notify_task_update(task)
        
        # 根据讨论结果分配子任务
        subtasks = self._divide_task(task, analysis, participants)
        results = {}
        
        for i, subtask in enumerate(subtasks):
            agent = subtask['agent']
            step = TaskStep(
                name=subtask['name'],
                status="running",
                agent_id=agent.id
            )
            task.steps.append(step)
            self._notify_task_update(task)
            
            agent.update_status(AgentStatus.WORKING, f"执行: {subtask['name']}", task.id)
            result = await agent.execute(task)
            
            step.status = "completed"
            results[agent.id] = result
            agent.update_status(AgentStatus.IDLE, "Ready")
            self._notify_task_update(task)
        
        # Step 3: 汇总结果
        task.steps.append(TaskStep(name="汇总结果", status="completed"))
        task.result = {
            'collaboration': True,
            'participants': [p.id for p in participants],
            'subtask_results': results,
            'discussion_summary': task.discussion_history[-3:] if task.discussion_history else []
        }
        
        for agent in participants:
            agent.update_status(AgentStatus.IDLE, "Ready")
    
    def _select_best_agent(self, task_types: List[str]) -> Optional[AgentBase]:
        """选择最佳 Agent"""
        if not task_types:
            return list(self.agents.values())[0] if self.agents else None
        
        scores = {}
        for agent_id, agent in self.agents.items():
            score = agent.can_handle(task_types[0], task_types)
            scores[agent_id] = score
        
        best_id = max(scores, key=scores.get) if scores else None
        return self.agents.get(best_id)
    
    def _select_participants(self, task_types: List[str]) -> List[AgentBase]:
        """选择协作参与者"""
        participants = []
        for task_type in task_types:
            agent = self._select_best_agent([task_type])
            if agent and agent not in participants:
                participants.append(agent)
        
        # 至少包含 2 个参与者
        if len(participants) < 2:
            for agent in self.agents.values():
                if agent not in participants:
                    participants.append(agent)
                    if len(participants) >= 2:
                        break
        
        return participants
    
    def _divide_task(self, task: Task, analysis: dict, participants: List[AgentBase]) -> List[dict]:
        """根据任务类型和参与者分配子任务"""
        subtasks = []
        
        for i, agent in enumerate(participants):
            # 根据 agent 能力分配子任务
            capability = agent.capabilities[0].name if agent.capabilities else "通用任务"
            subtasks.append({
                'name': f"{capability}处理",
                'agent': agent,
                'description': f"负责{capability}相关的工作"
            })
        
        return subtasks
    
    def _notify_task_update(self, task: Task):
        if self.on_task_update:
            self.on_task_update(task)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())
    
    def get_agent_states(self) -> List[dict]:
        return [agent.to_dict() for agent in self.agents.values()]