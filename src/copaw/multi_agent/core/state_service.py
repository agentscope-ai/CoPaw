"""
状态服务 - 管理 WebSocket 连接和状态推送
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class StateService:
    """状态服务 - 收集和推送状态"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.websocket_clients: Set = set()
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置回调"""
        # Agent 状态变化
        for agent in self.orchestrator.agents.values():
            agent.on_status_change = self._on_agent_status_change
        
        # 任务更新
        self.orchestrator.on_task_update = self._on_task_update
        
        # 讨论消息
        self.orchestrator.on_discussion_message = self._on_discussion_message
    
    async def register_client(self, websocket):
        """注册 WebSocket 客户端"""
        self.websocket_clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.websocket_clients)}")
        
        # 发送初始状态
        await self._send_initial_state(websocket)
    
    async def unregister_client(self, websocket):
        """注销客户端"""
        self.websocket_clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.websocket_clients)}")
    
    async def _send_initial_state(self, websocket):
        """发送初始状态"""
        state = {
            'type': 'initial_state',
            'data': {
                'agents': self.orchestrator.get_agent_states(),
                'tasks': [t.to_dict() for t in self.orchestrator.get_all_tasks()[-20:]],  # 最近20个任务
                'timestamp': datetime.now().isoformat()
            }
        }
        await websocket.send_json(state)
    
    def _on_agent_status_change(self, agent_state):
        """Agent 状态变化回调"""
        asyncio.create_task(self._broadcast({
            'type': 'agent_status',
            'data': {
                'agent_id': agent_state.agent_id,
                'status': agent_state.status.value,
                'message': agent_state.message,
                'current_task': agent_state.current_task,
                'last_activity': agent_state.last_activity.isoformat()
            }
        }))
    
    def _on_task_update(self, task):
        """任务更新回调"""
        asyncio.create_task(self._broadcast({
            'type': 'task_update',
            'data': task.to_dict()
        }))
    
    def _on_discussion_message(self, task_id: str, message: dict):
        """讨论消息回调"""
        asyncio.create_task(self._broadcast({
            'type': 'discussion_message',
            'data': {
                'task_id': task_id,
                'message': message
            }
        }))
    
    async def _broadcast(self, message: dict):
        """广播消息给所有客户端"""
        if not self.websocket_clients:
            return
        
        dead_clients = set()
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                dead_clients.add(client)
        
        # 清理断开的客户端
        self.websocket_clients -= dead_clients
    
    async def handle_client_message(self, websocket, message: dict):
        """处理客户端消息"""
        msg_type = message.get('type')
        
        if msg_type == 'create_task':
            # 创建新任务
            request = message.get('request', '')
            context = message.get('context', {})
            task = await self.orchestrator.submit_task(request, context)
            await websocket.send_json({
                'type': 'task_created',
                'data': {'task_id': task.id}
            })
        
        elif msg_type == 'get_task':
            task_id = message.get('task_id')
            task = self.orchestrator.get_task(task_id)
            if task:
                await websocket.send_json({
                    'type': 'task_detail',
                    'data': task.to_dict()
                })
        
        elif msg_type == 'list_tasks':
            tasks = self.orchestrator.get_all_tasks()
            await websocket.send_json({
                'type': 'task_list',
                'data': [t.to_dict() for t in tasks]
            })
        
        elif msg_type == 'get_agents':
            await websocket.send_json({
                'type': 'agent_list',
                'data': self.orchestrator.get_agent_states()
            })