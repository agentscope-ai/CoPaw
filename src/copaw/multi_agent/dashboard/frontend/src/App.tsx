import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Activity, Users, MessageSquare, Send, RefreshCw,
  CheckCircle, Clock, XCircle, AlertCircle, Play
} from 'lucide-react'

// Types
interface Agent {
  id: string
  name: string
  role: string
  avatar: string
  status: 'idle' | 'working' | 'discussing' | 'error'
  current_task: string | null
  message: string
  last_activity: string
  capabilities: { name: string; description: string }[]
}

interface TaskStep {
  name: string
  status: string
  agent_id?: string
}

interface DiscussionMessage {
  round: number
  agent_id: string
  agent_name: string
  avatar: string
  message: string
  timestamp: string
}

interface Task {
  id: string
  request: string
  status: 'pending' | 'running' | 'discussing' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  started_at: string | null
  completed_at: string | null
  assigned_to: string | null
  participants: string[]
  steps: TaskStep[]
  discussion_history: DiscussionMessage[]
  result: any
  error: string | null
}

// Status colors
const statusColors: Record<string, string> = {
  idle: 'bg-gray-400',
  working: 'bg-blue-500',
  discussing: 'bg-orange-500',
  error: 'bg-red-500',
  pending: 'bg-gray-400',
  running: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  cancelled: 'bg-gray-500'
}

const statusLabels: Record<string, string> = {
  idle: '空闲',
  working: '工作中',
  discussing: '讨论中',
  error: '错误',
  pending: '等待',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消'
}

function App() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [newTaskRequest, setNewTaskRequest] = useState('')
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8766/ws')
    
    ws.onopen = () => {
      setConnected(true)
      ws.send(JSON.stringify({ type: 'get_agents' }))
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch (data.type) {
        case 'initial_state':
        case 'agent_list':
          setAgents(data.data.agents || data.data)
          break
        case 'agent_status':
          setAgents(prev => prev.map(a => 
            a.id === data.data.agent_id 
              ? { ...a, ...data.data }
              : a
          ))
          break
        case 'task_list':
          setTasks(data.data)
          break
        case 'task_update':
          setTasks(prev => {
            const exists = prev.find(t => t.id === data.data.id)
            if (exists) {
              return prev.map(t => t.id === data.data.id ? data.data : t)
            }
            return [data.data, ...prev]
          })
          if (selectedTask?.id === data.data.id) {
            setSelectedTask(data.data)
          }
          break
        case 'discussion_message':
          if (selectedTask?.id === data.data.task_id) {
            setSelectedTask(prev => prev ? {
              ...prev,
              discussion_history: [...prev.discussion_history, data.data.message]
            } : null)
          }
          break
      }
    }
    
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    
    wsRef.current = ws
    
    // Fetch initial data via REST
    fetch('/api/tasks')
      .then(r => r.json())
      .then(data => setTasks(data.tasks || []))
    
    return () => ws.close()
  }, [])

  const createTask = async () => {
    if (!newTaskRequest.trim()) return
    
    await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request: newTaskRequest })
    })
    
    setNewTaskRequest('')
  }

  const getProgress = (task: Task) => {
    if (task.steps.length === 0) return 0
    const completed = task.steps.filter(s => s.status === 'completed').length
    return Math.round((completed / task.steps.length) * 100)
  }

  return (
    <div className="min-h-screen bg-apple-gray p-6">
      {/* Header */}
      <header className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold text-apple-dark">Copaw Agent System</h1>
          <span className={`px-2 py-1 rounded-full text-xs ${connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {connected ? '🟢 已连接' : '🔴 未连接'}
          </span>
        </div>
        <button 
          onClick={() => wsRef.current?.send(JSON.stringify({ type: 'get_agents' }))}
          className="p-2 rounded-full hover:bg-white/50 transition"
        >
          <RefreshCw className="w-5 h-5 text-apple-secondary" />
        </button>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        
        {/* Agent Status Panel */}
        <div className="col-span-4">
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Users className="w-5 h-5" />
              Agent 状态
            </h2>
            
            <div className="space-y-3">
              {agents.map(agent => (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 bg-white/50 rounded-xl hover:bg-white/80 transition cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{agent.avatar}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{agent.name}</span>
                        <span className={`status-dot ${agent.status}`} />
                      </div>
                      <div className="text-sm text-apple-secondary">{agent.role}</div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      agent.status === 'idle' ? 'bg-gray-100 text-gray-600' :
                      agent.status === 'working' ? 'bg-blue-100 text-blue-600' :
                      agent.status === 'discussing' ? 'bg-orange-100 text-orange-600' :
                      'bg-red-100 text-red-600'
                    }`}>
                      {statusLabels[agent.status]}
                    </span>
                  </div>
                  {agent.current_task && (
                    <div className="mt-2 text-sm text-apple-secondary">
                      📋 {agent.message}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>

          {/* Create Task */}
          <div className="card p-6 mt-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Send className="w-5 h-5" />
              创建任务
            </h2>
            <div className="flex gap-2">
              <input
                type="text"
                value={newTaskRequest}
                onChange={(e) => setNewTaskRequest(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && createTask()}
                placeholder="输入任务描述..."
                className="flex-1 px-4 py-2 rounded-xl bg-white/50 border-0 focus:ring-2 focus:ring-apple-blue outline-none"
              />
              <button
                onClick={createTask}
                className="px-4 py-2 bg-apple-blue text-white rounded-xl hover:bg-blue-600 transition"
              >
                发送
              </button>
            </div>
          </div>
        </div>

        {/* Tasks Panel */}
        <div className="col-span-8">
          {/* Task List */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              任务列表
            </h2>
            
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {tasks.length === 0 ? (
                <div className="text-center py-8 text-apple-secondary">
                  暂无任务，创建一个新任务开始吧！
                </div>
              ) : (
                tasks.slice(0, 10).map(task => (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    onClick={() => setSelectedTask(task)}
                    className={`p-4 rounded-xl cursor-pointer transition ${
                      selectedTask?.id === task.id 
                        ? 'bg-apple-blue/10 ring-2 ring-apple-blue' 
                        : 'bg-white/50 hover:bg-white/80'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium truncate">{task.request}</div>
                        <div className="text-sm text-apple-secondary mt-1">
                          {task.participants.length > 0 && (
                            <span>参与: {task.participants.join(', ')} · </span>
                          )}
                          <span>{new Date(task.created_at).toLocaleString('zh-CN')}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {task.status === 'running' && (
                          <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="progress-bar h-full" 
                              style={{ width: `${getProgress(task)}%` }}
                            />
                          </div>
                        )}
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          statusColors[task.status]
                        } text-white`}>
                          {statusLabels[task.status]}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </div>

          {/* Task Detail */}
          {selectedTask && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-6 mt-6"
            >
              <h2 className="text-lg font-semibold mb-4">任务详情</h2>
              
              {/* Task Info */}
              <div className="p-4 bg-white/50 rounded-xl mb-4">
                <div className="font-medium">{selectedTask.request}</div>
                <div className="flex items-center gap-4 mt-2 text-sm text-apple-secondary">
                  <span>状态: {statusLabels[selectedTask.status]}</span>
                  <span>参与者: {selectedTask.participants.join(', ') || '无'}</span>
                </div>
              </div>

              {/* Steps */}
              {selectedTask.steps.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-medium mb-2">执行步骤</h3>
                  <div className="space-y-2">
                    {selectedTask.steps.map((step, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 bg-white/30 rounded-lg">
                        {step.status === 'completed' ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : step.status === 'running' ? (
                          <Play className="w-5 h-5 text-blue-500" />
                        ) : step.status === 'failed' ? (
                          <XCircle className="w-5 h-5 text-red-500" />
                        ) : (
                          <Clock className="w-5 h-5 text-gray-400" />
                        )}
                        <span className="flex-1">{step.name}</span>
                        {step.agent_id && (
                          <span className="text-sm text-apple-secondary">{step.agent_id}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Discussion */}
              {selectedTask.discussion_history.length > 0 && (
                <div>
                  <h3 className="font-medium mb-2 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    协作讨论
                  </h3>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    <AnimatePresence>
                      {selectedTask.discussion_history.map((msg, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="discussion-message p-3 bg-white/50 rounded-xl"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span>{msg.avatar}</span>
                            <span className="font-medium">{msg.agent_name}</span>
                            <span className="text-xs text-apple-secondary">
                              第 {msg.round} 轮
                            </span>
                          </div>
                          <p className="text-sm text-apple-dark">{msg.message}</p>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                </div>
              )}

              {/* Result */}
              {selectedTask.result && (
                <div className="mt-4 p-4 bg-green-50 rounded-xl">
                  <h3 className="font-medium text-green-700 mb-2">执行结果</h3>
                  <pre className="text-sm overflow-auto max-h-40">
                    {JSON.stringify(selectedTask.result, null, 2)}
                  </pre>
                </div>
              )}

              {/* Error */}
              {selectedTask.error && (
                <div className="mt-4 p-4 bg-red-50 rounded-xl">
                  <h3 className="font-medium text-red-700 mb-2">错误信息</h3>
                  <p className="text-sm text-red-600">{selectedTask.error}</p>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App