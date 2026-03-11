#!/usr/bin/env python3
"""
Dashboard Backend - FastAPI 服务
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict
import yaml
import logging

# 切换到项目根目录
os.chdir(Path(__file__).parent.parent.parent)

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import AgentBase, Orchestrator, StateService, Task
from core.orchestrator import TaskStatus

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 加载配置
config_path = Path(__file__).parent.parent.parent / 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 创建 FastAPI 应用
app = FastAPI(title="Copaw Agent Dashboard", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局实例
orchestrator: Orchestrator = None
state_service: StateService = None


class CreateTaskRequest(BaseModel):
    request: str
    context: dict = {}


def load_agents() -> Dict[str, AgentBase]:
    """加载所有 Agent"""
    agents = {}
    agents_dir = Path(__file__).parent.parent.parent / 'agents'
    
    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir():
            try:
                agent = AgentBase(agent_dir)
                agents[agent.id] = agent
                logging.info(f"Loaded agent: {agent.name} ({agent.id})")
            except Exception as e:
                logging.warning(f"Failed to load agent from {agent_dir}: {e}")
    
    return agents


@app.on_event("startup")
async def startup():
    """启动时初始化"""
    global orchestrator, state_service
    
    # 加载 Agent
    agents = load_agents()
    if not agents:
        logging.error("No agents loaded!")
        raise RuntimeError("No agents found")
    
    # 创建 Orchestrator
    orchestrator = Orchestrator(agents, config)
    
    # 创建 StateService
    state_service = StateService(orchestrator)
    
    logging.info(f"Started with {len(agents)} agents")


# REST API

@app.get("/api/agents")
async def get_agents():
    """获取所有 Agent 状态"""
    return {"agents": orchestrator.get_agent_states()}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """获取单个 Agent 详情"""
    agent = orchestrator.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.to_dict()


@app.post("/api/tasks")
async def create_task(req: CreateTaskRequest):
    """创建新任务"""
    task = await orchestrator.submit_task(req.request, req.context)
    return {"task_id": task.id, "status": task.status.value}


@app.get("/api/tasks")
async def get_tasks():
    """获取任务列表"""
    tasks = orchestrator.get_all_tasks()
    return {"tasks": [t.to_dict() for t in tasks]}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """获取任务详情"""
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Task already finished")
    
    task.status = TaskStatus.CANCELLED
    return {"status": "cancelled"}


# WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接"""
    await websocket.accept()
    await state_service.register_client(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            await state_service.handle_client_message(websocket, data)
    except WebSocketDisconnect:
        await state_service.unregister_client(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await state_service.unregister_client(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8766)