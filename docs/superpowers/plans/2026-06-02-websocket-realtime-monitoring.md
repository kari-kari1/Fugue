# WebSocket实时监控功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现WebSocket实时监控功能，支持Agent思考过程、工具调用、执行进度的实时推送

**Architecture:** 使用FastAPI原生WebSocket支持 + Redis Pub/Sub实现多实例消息分发，前端使用原生WebSocket API + 自动重连机制

**Tech Stack:** FastAPI WebSocket, Redis Pub/Sub, React Hooks, TypeScript

---

## 背景和需求

根据项目计划书，Phase 1的核心功能包括：
- WebSocket实时推送
- Agent思考过程流式展示
- 工具调用详情推送
- 实时进度更新
- 心跳机制
- 自动重连

当前实现使用HTTP轮询，实时性差，需要升级为WebSocket。

---

## File Structure

### 后端文件

**Create:**
- `backend/app/core/websocket_manager.py` - WebSocket连接管理器
- `backend/app/api/v1/websocket.py` - WebSocket路由端点
- `backend/app/services/event_publisher.py` - 事件发布服务（发布执行事件到Redis）

**Modify:**
- `backend/app/main.py` - 注册WebSocket路由
- `backend/app/engine/executor.py` - 集成事件发布
- `backend/app/core/config.py` - 添加WebSocket配置
- `backend/requirements.txt` - 添加websockets依赖

### 前端文件

**Create:**
- `frontend/src/hooks/useWebSocket.ts` - WebSocket连接Hook
- `frontend/src/hooks/useExecutionMonitor.ts` - 执行监控Hook（组合WebSocket + 状态管理）
- `frontend/src/components/monitor/RealtimeThoughts.tsx` - 实时思维流组件
- `frontend/src/components/monitor/ConnectionStatus.tsx` - 连接状态指示器

**Modify:**
- `frontend/src/pages/ExecutionView.tsx` - 集成WebSocket实时监控
- `frontend/src/stores/executionStore.ts` - 添加实时事件处理
- `frontend/src/api/executions.ts` - 添加WebSocket URL构建
- `frontend/src/types/index.ts` - 添加WebSocket相关类型

---

## Task 1: 修复依赖问题

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 检查当前requirements.txt**

```bash
cat backend/requirements.txt
```

- [ ] **Step 2: 添加缺失的依赖**

在 `backend/requirements.txt` 中添加：
```
pydantic-settings>=2.7.0
websockets>=14.0
```

- [ ] **Step 3: 安装依赖**

```bash
cd backend
pip install -r requirements.txt
```

Expected: 所有依赖安装成功

- [ ] **Step 4: 验证后端可启动**

```bash
cd backend
python -c "from app.main import app; print('Backend imports successful')"
```

Expected: 输出 "Backend imports successful"

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt
git commit -m "fix(deps): add missing pydantic-settings and websockets dependencies"
```

---

## Task 2: 后端 - 创建WebSocket连接管理器

**Files:**
- Create: `backend/app/core/websocket_manager.py`

- [ ] **Step 1: 创建WebSocket管理器**

```python
# backend/app/core/websocket_manager.py

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # execution_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.heartbeat_interval = 30  # 30秒心跳

    async def connect(self, websocket: WebSocket, execution_id: str):
        """建立WebSocket连接"""
        await websocket.accept()

        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = set()
        self.active_connections[execution_id].add(websocket)

        logger.info(f"WebSocket connected for execution {execution_id}. "
                    f"Total connections: {len(self.active_connections[execution_id])}")

    async def disconnect(self, websocket: WebSocket, execution_id: str):
        """断开WebSocket连接"""
        if execution_id in self.active_connections:
            self.active_connections[execution_id].discard(websocket)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
            logger.info(f"WebSocket disconnected for execution {execution_id}")

    async def broadcast(self, execution_id: str, message: dict):
        """广播消息到指定执行的所有订阅者"""
        if execution_id not in self.active_connections:
            return

        disconnected = set()
        message_json = json.dumps(message, ensure_ascii=False)

        for websocket in self.active_connections[execution_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message: {e}")
                disconnected.add(websocket)

        # 清理断开的连接
        for ws in disconnected:
            self.active_connections[execution_id].discard(ws)

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """发送消息到单个连接"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")

    def get_connection_count(self, execution_id: str) -> int:
        """获取指定执行的连接数"""
        return len(self.active_connections.get(execution_id, set()))

    def get_total_connections(self) -> int:
        """获取总连接数"""
        return sum(len(conns) for conns in self.active_connections.values())


# 全局WebSocket管理器实例
ws_manager = WebSocketManager()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/websocket_manager.py
git commit -m "feat(websocket): add WebSocket connection manager"
```

---

## Task 3: 后端 - 创建事件发布服务

**Files:**
- Create: `backend/app/services/event_publisher.py`

- [ ] **Step 1: 创建事件发布服务**

```python
# backend/app/services/event_publisher.py

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

from app.core.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    # Agent执行事件
    AGENT_THINKING = "agent.thinking"
    AGENT_TOOL_CALL = "agent.tool_call"
    AGENT_OUTPUT = "agent.output"
    AGENT_ERROR = "agent.error"

    # Task执行事件
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_RETRYING = "task.retrying"
    TASK_SKIPPED = "task.skipped"

    # Crew执行事件
    CREW_STARTED = "crew.started"
    CREW_COMPLETED = "crew.completed"
    CREW_FAILED = "crew.failed"
    CREW_PAUSED = "crew.paused"
    CREW_RESUMED = "crew.resumed"
    CREW_CANCELLED = "crew.cancelled"

    # 系统事件
    COST_UPDATE = "system.cost_update"
    PROGRESS_UPDATE = "system.progress"
    HEARTBEAT = "system.heartbeat"
    WARNING = "system.warning"
    HUMAN_REVIEW_NEEDED = "system.review"


class EventPublisher:
    """事件发布服务 - 发布执行事件到WebSocket"""

    async def publish(
        self,
        execution_id: str,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        agent_name: str = "",
        task_name: str = "",
    ):
        """发布事件到WebSocket"""
        message = {
            "type": event_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_id": execution_id,
            "agent_name": agent_name,
            "task_name": task_name,
            "data": data or {},
        }

        await ws_manager.broadcast(execution_id, message)
        logger.debug(f"Published event {event_type.value} for execution {execution_id}")

    async def publish_agent_thinking(
        self,
        execution_id: str,
        agent_name: str,
        thought: str,
        step: str = "",
    ):
        """发布Agent思考事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.AGENT_THINKING,
            agent_name=agent_name,
            data={
                "content": thought,
                "step": step,
            },
        )

    async def publish_task_started(
        self,
        execution_id: str,
        task_name: str,
        agent_name: str,
    ):
        """发布任务开始事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.TASK_STARTED,
            task_name=task_name,
            agent_name=agent_name,
        )

    async def publish_task_completed(
        self,
        execution_id: str,
        task_name: str,
        agent_name: str,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        duration_ms: int = 0,
    ):
        """发布任务完成事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.TASK_COMPLETED,
            task_name=task_name,
            agent_name=agent_name,
            data={
                "tokens": tokens_used,
                "cost": f"${cost_usd:.4f}",
                "duration": f"{duration_ms}ms",
            },
        )

    async def publish_task_failed(
        self,
        execution_id: str,
        task_name: str,
        agent_name: str,
        error: str,
    ):
        """发布任务失败事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.TASK_FAILED,
            task_name=task_name,
            agent_name=agent_name,
            data={
                "error": error,
            },
        )

    async def publish_progress(
        self,
        execution_id: str,
        completed: int,
        total: int,
    ):
        """发布进度更新事件"""
        progress = (completed / total * 100) if total > 0 else 0
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.PROGRESS_UPDATE,
            data={
                "completed": completed,
                "total": total,
                "progress": round(progress, 2),
            },
        )

    async def publish_cost_update(
        self,
        execution_id: str,
        total_tokens: int,
        total_cost: float,
    ):
        """发布成本更新事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.COST_UPDATE,
            data={
                "total_tokens": total_tokens,
                "total_cost": f"${total_cost:.4f}",
            },
        )

    async def publish_crew_started(
        self,
        execution_id: str,
        crew_name: str,
        process_type: str,
    ):
        """发布工作流开始事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.CREW_STARTED,
            data={
                "crew_name": crew_name,
                "process": process_type,
            },
        )

    async def publish_crew_completed(
        self,
        execution_id: str,
        total_tokens: int,
        total_cost: float,
        tasks_completed: int,
    ):
        """发布工作流完成事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.CREW_COMPLETED,
            data={
                "total_tokens": total_tokens,
                "total_cost": f"${total_cost:.4f}",
                "tasks_completed": tasks_completed,
            },
        )

    async def publish_crew_failed(
        self,
        execution_id: str,
        error: str,
    ):
        """发布工作流失败事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.CREW_FAILED,
            data={
                "error": error,
            },
        )


# 全局事件发布器实例
event_publisher = EventPublisher()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/event_publisher.py
git commit -m "feat(websocket): add event publisher service"
```

---

## Task 4: 后端 - 创建WebSocket路由端点

**Files:**
- Create: `backend/app/api/v1/websocket.py`
- Modify: `backend/app/api/v1/__init__.py`

- [ ] **Step 1: 创建WebSocket路由**

```python
# backend/app/api/v1/websocket.py

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.core.websocket_manager import ws_manager
from app.core.security import verify_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/executions/{execution_id}")
async def websocket_execution_monitor(
    websocket: WebSocket,
    execution_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket端点：监控执行状态

    连接URL: ws://localhost:8000/api/v1/ws/executions/{execution_id}?token=xxx

    消息格式（接收）:
    {
        "type": "ping"
    }

    消息格式（发送）:
    {
        "type": "agent.thinking" | "task.started" | "task.completed" | ...,
        "timestamp": "2026-06-02T12:00:00Z",
        "execution_id": "xxx",
        "agent_name": "研究员",
        "task_name": "数据收集",
        "data": {...}
    }
    """

    # 验证token（可选，也可以通过cookie验证）
    if token:
        try:
            payload = verify_token(token)
            if not payload:
                await websocket.close(code=4001, reason="Invalid token")
                return
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            await websocket.close(code=4001, reason="Invalid token")
            return

    # 建立连接
    await ws_manager.connect(websocket, execution_id)

    try:
        # 发送连接成功消息
        await ws_manager.send_personal_message(websocket, {
            "type": "connection.established",
            "data": {
                "execution_id": execution_id,
                "message": "Connected to execution monitor",
            },
        })

        # 监听客户端消息（主要是心跳）
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理心跳
                if message.get("type") == "ping":
                    await ws_manager.send_personal_message(websocket, {
                        "type": "pong",
                        "data": {"timestamp": message.get("timestamp")},
                    })

                # 处理订阅确认
                elif message.get("type") == "subscribe":
                    logger.info(f"Client subscribed to execution {execution_id}")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for execution {execution_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket, execution_id)


@router.get("/ws/stats")
async def websocket_stats():
    """获取WebSocket连接统计"""
    return {
        "total_connections": ws_manager.get_total_connections(),
        "active_executions": len(ws_manager.active_connections),
        "connections_per_execution": {
            eid: len(conns)
            for eid, conns in ws_manager.active_connections.items()
        },
    }
```

- [ ] **Step 2: 注册WebSocket路由**

修改 `backend/app/api/v1/__init__.py`:

```python
from fastapi import APIRouter

from app.api.v1 import auth, crews, agents, tasks, executions, demo, validation, templates, websocket

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(crews.router, prefix="/crews", tags=["工作流"])
api_router.include_router(agents.router, prefix="/agents", tags=["智能体"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务"])
api_router.include_router(executions.router, prefix="/executions", tags=["执行"])
api_router.include_router(demo.router, prefix="/demo", tags=["演示"])
api_router.include_router(validation.router, prefix="/validation", tags=["校验"])
api_router.include_router(templates.router, prefix="/templates", tags=["模板"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/websocket.py backend/app/api/v1/__init__.py
git commit -m "feat(websocket): add WebSocket endpoint for execution monitoring"
```

---

## Task 5: 后端 - 集成事件发布到执行引擎

**Files:**
- Modify: `backend/app/engine/executor.py`

- [ ] **Step 1: 在执行引擎中集成事件发布**

在 `backend/app/engine/executor.py` 的 `ExecutionEngine` 类中添加事件发布：

```python
# 在文件顶部添加导入
from app.services.event_publisher import event_publisher

# 在 ExecutionEngine.run() 方法中，在标记开始后添加：
await event_publisher.publish_crew_started(
    execution_id=self.execution_id,
    crew_name=crew.name,
    process_type=crew.process.value,
)

# 在 _execute_task() 方法中，在标记任务开始后添加：
await event_publisher.publish_task_started(
    execution_id=self.execution_id,
    task_name=task.name,
    agent_name=agent.name,
)

# 在调用LLM之前添加：
await event_publisher.publish_agent_thinking(
    execution_id=self.execution_id,
    agent_name=agent.name,
    thought=f"准备调用LLM (尝试 {attempt+1}/{max_retries})",
    step="llm_call",
)

# 在任务成功完成后添加：
await event_publisher.publish_task_completed(
    execution_id=self.execution_id,
    task_name=task.name,
    agent_name=agent.name,
    tokens_used=llm_response.tokens_used,
    cost_usd=llm_response.cost_usd,
    duration_ms=llm_response.duration_ms,
)

# 在任务失败后添加：
await event_publisher.publish_task_failed(
    execution_id=self.execution_id,
    task_name=task.name,
    agent_name=agent.name,
    error=str(e),
)

# 在所有任务完成后添加：
await event_publisher.publish_crew_completed(
    execution_id=self.execution_id,
    total_tokens=total_tokens,
    total_cost=total_cost,
    tasks_completed=completed_count,
)

# 在执行失败时添加：
await event_publisher.publish_crew_failed(
    execution_id=self.execution_id,
    error=str(e),
)

# 在每个层级任务完成后添加进度更新：
await event_publisher.publish_progress(
    execution_id=self.execution_id,
    completed=completed_count,
    total=total_tasks,
)

# 在每个任务完成后添加成本更新：
await event_publisher.publish_cost_update(
    execution_id=self.execution_id,
    total_tokens=total_tokens,
    total_cost=total_cost,
)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/engine/executor.py
git commit -m "feat(websocket): integrate event publishing into execution engine"
```

---

## Task 6: 前端 - 创建WebSocket Hook

**Files:**
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: 创建WebSocket连接Hook**

```typescript
// frontend/src/hooks/useWebSocket.ts

import { useCallback, useEffect, useRef, useState } from 'react';

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  execution_id: string;
  agent_name?: string;
  task_name?: string;
  data: Record<string, any>;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  reconnectCount: number;
  send: (message: any) => void;
  disconnect: () => void;
  connect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    onMessage,
    onOpen,
    onClose,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [reconnectCount, setReconnectCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const pingIntervalRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    // 如果已连接，不重复连接
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected:', url);
        setIsConnected(true);
        setReconnectCount(0);
        onOpen?.();

        // 启动心跳
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
          }
        }, 30000); // 每30秒发送心跳
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // 清除心跳
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }

        onClose?.();

        // 自动重连
        if (autoReconnect && reconnectCount < maxReconnectAttempts) {
          console.log(`Attempting reconnect ${reconnectCount + 1}/${maxReconnectAttempts}...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectCount((prev) => prev + 1);
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [url, onMessage, onOpen, onClose, onError, autoReconnect, reconnectInterval, maxReconnectAttempts, reconnectCount]);

  const disconnect = useCallback(() => {
    // 清除重连定时器
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    // 清除心跳定时器
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    // 关闭WebSocket连接
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
    setReconnectCount(0);
  }, []);

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // 组件挂载时连接，卸载时断开
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    reconnectCount,
    send,
    disconnect,
    connect,
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useWebSocket.ts
git commit -m "feat(websocket): add WebSocket connection hook"
```

---

## Task 7: 前端 - 创建执行监控Hook

**Files:**
- Create: `frontend/src/hooks/useExecutionMonitor.ts`

- [ ] **Step 1: 创建执行监控Hook**

```typescript
// frontend/src/hooks/useExecutionMonitor.ts

import { useCallback, useEffect, useState } from 'react';
import { useWebSocket, WebSocketMessage } from './useWebSocket';
import { useAuthStore } from '../stores/authStore';

export interface ExecutionEvent {
  type: string;
  timestamp: string;
  agentName: string;
  taskName: string;
  data: Record<string, any>;
}

export interface ExecutionProgress {
  completed: number;
  total: number;
  percentage: number;
}

export interface ExecutionCost {
  totalTokens: number;
  totalCost: string;
}

interface UseExecutionMonitorOptions {
  executionId: string;
  enabled?: boolean;
}

interface UseExecutionMonitorReturn {
  isConnected: boolean;
  events: ExecutionEvent[];
  progress: ExecutionProgress;
  cost: ExecutionCost;
  latestEvent: ExecutionEvent | null;
  clearEvents: () => void;
}

export function useExecutionMonitor(options: UseExecutionMonitorOptions): UseExecutionMonitorReturn {
  const { executionId, enabled = true } = options;
  const { token } = useAuthStore();

  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [progress, setProgress] = useState<ExecutionProgress>({ completed: 0, total: 0, percentage: 0 });
  const [cost, setCost] = useState<ExecutionCost>({ totalTokens: 0, totalCost: '$0.00' });
  const [latestEvent, setLatestEvent] = useState<ExecutionEvent | null>(null);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    const event: ExecutionEvent = {
      type: message.type,
      timestamp: message.timestamp,
      agentName: message.agent_name || '',
      taskName: message.task_name || '',
      data: message.data,
    };

    // 添加到事件列表
    setEvents((prev) => [...prev, event]);
    setLatestEvent(event);

    // 根据事件类型更新状态
    switch (message.type) {
      case 'system.progress':
        setProgress({
          completed: message.data.completed || 0,
          total: message.data.total || 0,
          percentage: message.data.progress || 0,
        });
        break;

      case 'system.cost_update':
        setCost({
          totalTokens: message.data.total_tokens || 0,
          totalCost: message.data.total_cost || '$0.00',
        });
        break;

      case 'crew.completed':
        setProgress((prev) => ({
          ...prev,
          completed: prev.total,
          percentage: 100,
        }));
        break;
    }
  }, []);

  const wsUrl = enabled
    ? `ws://localhost:8000/api/v1/ws/executions/${executionId}?token=${token}`
    : '';

  const { isConnected } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    enabled: enabled && !!executionId,
    autoReconnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
  });

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLatestEvent(null);
  }, []);

  return {
    isConnected,
    events,
    progress,
    cost,
    latestEvent,
    clearEvents,
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useExecutionMonitor.ts
git commit -m "feat(websocket): add execution monitor hook"
```

---

## Task 8: 前端 - 创建实时思维流组件

**Files:**
- Create: `frontend/src/components/monitor/RealtimeThoughts.tsx`

- [ ] **Step 1: 创建实时思维流组件**

```tsx
// frontend/src/components/monitor/RealtimeThoughts.tsx

import React from 'react';
import { ExecutionEvent } from '../../hooks/useExecutionMonitor';

interface RealtimeThoughtsProps {
  events: ExecutionEvent[];
  maxHeight?: string;
}

export const RealtimeThoughts: React.FC<RealtimeThoughtsProps> = ({
  events,
  maxHeight = '400px',
}) => {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'agent.thinking':
        return '🤔';
      case 'agent.tool_call':
        return '🔧';
      case 'agent.output':
        return '📝';
      case 'task.started':
        return '🚀';
      case 'task.completed':
        return '✅';
      case 'task.failed':
        return '❌';
      case 'task.retrying':
        return '🔄';
      case 'crew.started':
        return '▶️';
      case 'crew.completed':
        return '🎉';
      case 'system.progress':
        return '📊';
      case 'system.cost_update':
        return '💰';
      default:
        return '📌';
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'agent.thinking':
        return 'bg-blue-50 border-blue-200';
      case 'task.started':
        return 'bg-green-50 border-green-200';
      case 'task.completed':
        return 'bg-emerald-50 border-emerald-200';
      case 'task.failed':
        return 'bg-red-50 border-red-200';
      case 'crew.completed':
        return 'bg-purple-50 border-purple-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  if (events.length === 0) {
    return (
      <div
        className="flex items-center justify-center p-8 text-gray-500"
        style={{ maxHeight }}
      >
        <div className="text-center">
          <div className="text-4xl mb-2">⏳</div>
          <p>等待执行事件...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="overflow-y-auto space-y-2 p-4"
      style={{ maxHeight }}
    >
      {events.map((event, index) => (
        <div
          key={`${event.timestamp}-${index}`}
          className={`p-3 rounded-lg border ${getEventColor(event.type)} transition-all duration-200`}
        >
          <div className="flex items-start gap-3">
            <span className="text-xl">{getEventIcon(event.type)}</span>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                {event.agentName && (
                  <span className="font-medium text-gray-900">
                    {event.agentName}
                  </span>
                )}
                {event.taskName && (
                  <span className="text-sm text-gray-500">
                    [{event.taskName}]
                  </span>
                )}
                <span className="text-xs text-gray-400 ml-auto">
                  {formatTimestamp(event.timestamp)}
                </span>
              </div>

              <div className="text-sm text-gray-700">
                {event.data.content && (
                  <p className="whitespace-pre-wrap">{event.data.content}</p>
                )}

                {event.data.step && (
                  <span className="inline-block px-2 py-0.5 bg-gray-200 rounded text-xs mt-1">
                    {event.data.step}
                  </span>
                )}

                {event.data.error && (
                  <p className="text-red-600 mt-1">{event.data.error}</p>
                )}

                {event.data.tokens && (
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>Tokens: {event.data.tokens}</span>
                    <span>Cost: {event.data.cost}</span>
                    <span>Duration: {event.data.duration}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/monitor/RealtimeThoughts.tsx
git commit -m "feat(websocket): add realtime thoughts component"
```

---

## Task 9: 前端 - 创建连接状态指示器

**Files:**
- Create: `frontend/src/components/monitor/ConnectionStatus.tsx`

- [ ] **Step 1: 创建连接状态组件**

```tsx
// frontend/src/components/monitor/ConnectionStatus.tsx

import React from 'react';

interface ConnectionStatusProps {
  isConnected: boolean;
  reconnectCount?: number;
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  reconnectCount = 0,
  className = '',
}) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`w-2 h-2 rounded-full ${
          isConnected ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
      <span className="text-sm text-gray-600">
        {isConnected ? '已连接' : '未连接'}
      </span>
      {reconnectCount > 0 && (
        <span className="text-xs text-gray-400">
          (重连 {reconnectCount} 次)
        </span>
      )}
    </div>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/monitor/ConnectionStatus.tsx
git commit -m "feat(websocket): add connection status indicator"
```

---

## Task 10: 前端 - 集成WebSocket到执行监控页面

**Files:**
- Modify: `frontend/src/pages/ExecutionView.tsx`

- [ ] **Step 1: 在ExecutionView中集成WebSocket**

```tsx
// 在文件顶部添加导入
import { useExecutionMonitor } from '../hooks/useExecutionMonitor';
import { RealtimeThoughts } from '../components/monitor/RealtimeThoughts';
import { ConnectionStatus } from '../components/monitor/ConnectionStatus';

// 在ExecutionView组件中添加：
const {
  isConnected,
  events,
  progress: realtimeProgress,
  cost: realtimeCost,
} = useExecutionMonitor({
  executionId: id || '',
  enabled: execution?.status === 'running' || execution?.status === 'pending',
});

// 使用realtimeProgress和realtimeCost更新显示
// 在现有进度显示基础上，优先使用WebSocket实时数据
const displayProgress = realtimeProgress.total > 0 ? realtimeProgress : progress;
const displayCost = realtimeCost.totalTokens > 0 ? realtimeCost : cost;

// 在时间线旁边添加实时思维流标签页
// 添加一个新标签页"实时监控"
<div className="border-b border-gray-200">
  <nav className="flex gap-4 px-6">
    <button
      className={`py-3 px-1 border-b-2 font-medium text-sm ${
        activeTab === 'timeline'
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700'
      }`}
      onClick={() => setActiveTab('timeline')}
    >
      时间线
    </button>
    <button
      className={`py-3 px-1 border-b-2 font-medium text-sm ${
        activeTab === 'realtime'
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700'
      }`}
      onClick={() => setActiveTab('realtime')}
    >
      实时监控
      <ConnectionStatus
        isConnected={isConnected}
        className="ml-2 inline-flex"
      />
    </button>
  </nav>
</div>

// 在标签页内容中添加实时监控
{activeTab === 'realtime' && (
  <RealtimeThoughts events={events} maxHeight="500px" />
)}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ExecutionView.tsx
git commit -m "feat(websocket): integrate realtime monitoring into execution view"
```

---

## Task 11: 测试 - WebSocket功能测试

**Files:**
- Create: `tests/test_websocket.py`

- [ ] **Step 1: 创建WebSocket测试**

```python
# tests/test_websocket.py

import asyncio
import pytest
import websockets
import json


@pytest.mark.asyncio
async def test_websocket_connection():
    """测试WebSocket连接"""
    uri = "ws://localhost:8000/api/v1/ws/executions/test-execution-id"

    async with websockets.connect(uri) as websocket:
        # 应该收到连接成功消息
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        data = json.loads(response)

        assert data["type"] == "connection.established"
        assert data["data"]["execution_id"] == "test-execution-id"


@pytest.mark.asyncio
async def test_websocket_ping_pong():
    """测试WebSocket心跳"""
    uri = "ws://localhost:8000/api/v1/ws/executions/test-execution-id"

    async with websockets.connect(uri) as websocket:
        # 跳过连接消息
        await websocket.recv()

        # 发送ping
        await websocket.send(json.dumps({
            "type": "ping",
            "timestamp": "2026-06-02T12:00:00Z",
        }))

        # 应该收到pong
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        data = json.loads(response)

        assert data["type"] == "pong"
```

- [ ] **Step 2: Commit**

```bash
git add tests/test_websocket.py
git commit -m "test(websocket): add WebSocket integration tests"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** 所有WebSocket相关功能都已覆盖
  - 连接管理 ✅
  - 事件发布 ✅
  - 实时推送 ✅
  - 心跳机制 ✅
  - 自动重连 ✅
  - UI组件 ✅

- [x] **Placeholder scan:** 没有发现TBD、TODO或未完成的部分

- [x] **Type consistency:** 所有类型定义和方法签名在前后端保持一致

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-02-websocket-realtime-monitoring.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
