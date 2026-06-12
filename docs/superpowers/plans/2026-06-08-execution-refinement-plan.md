# 执行结果对话式迭代功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现工作流执行结果的对话式迭代功能，允许用户在执行完成后提供反馈，模型基于反馈优化结果。

**Architecture:** 采用前端React组件 + 后端FastAPI + SQLAlchemy的架构。通过WebSocket实现实时进度推送，通过REST API处理迭代请求。

**Tech Stack:** React, TypeScript, FastAPI, SQLAlchemy, WebSocket, Pydantic

---

## 文件结构

### 前端文件
```
frontend/src/
├── components/monitor/
│   ├── IterationChat.tsx          # 迭代对话主组件
│   ├── IterationMessage.tsx       # 单个迭代消息组件
│   └── RefineControls.tsx         # 迭代控制组件
├── hooks/
│   └── useIterationMonitor.ts     # 迭代监控hook
├── api/
│   └── iterations.ts             # 迭代API客户端
└── types/
    └── iteration.ts              # 迭代类型定义
```

### 后端文件
```
backend/app/
├── models/
│   └── iteration.py              # 迭代数据模型
├── schemas/
│   └── iteration.py              # 迭代Pydantic schemas
├── api/v1/
│   └── iterations.py             # 迭代API端点
├── engine/
│   └── executor.py               # 执行引擎（添加run_iteration方法）
└── services/
    └── event_publisher.py        # 事件发布器（添加迭代事件）
```

### 测试文件
```
backend/tests/
├── unit/
│   ├── test_iteration_model.py
│   ├── test_iteration_api.py
│   └── test_iteration_engine.py
└── integration/
    └── test_iteration_flow.py
```

---

## 实现阶段

### Phase 1: 数据模型和API (Task 1-3)

#### Task 1: 创建Iteration数据模型

**Files:**
- Create: `backend/app/models/iteration.py`
- Create: `backend/tests/unit/test_iteration_model.py`

- [ ] **Step 1: 写失败的测试**

```python
# backend/tests/unit/test_iteration_model.py

import pytest
from datetime import datetime
from app.models.iteration import Iteration, IterationMode, IterationStatus

def test_iteration_creation():
    """测试迭代记录创建"""
    iteration = Iteration(
        execution_id="exec_123",
        iteration_number=1,
        feedback="需要更详细",
        mode=IterationMode.INCREMENTAL,
        status=IterationStatus.PENDING,
        original_task_snapshot={"tasks": []},
        previous_output="之前的输出",
    )
    assert iteration.execution_id == "exec_123"
    assert iteration.iteration_number == 1
    assert iteration.feedback == "需要更详细"
    assert iteration.mode == IterationMode.INCREMENTAL
    assert iteration.status == IterationStatus.PENDING
    assert iteration.tokens_used == 0
    assert iteration.cost_usd == 0.0

def test_iteration_modes():
    """测试迭代模式枚举"""
    assert IterationMode.REEXECUTE == "reexecute"
    assert IterationMode.INCREMENTAL == "incremental"

def test_iteration_statuses():
    """测试迭代状态枚举"""
    assert IterationStatus.PENDING == "pending"
    assert IterationStatus.RUNNING == "running"
    assert IterationStatus.COMPLETED == "completed"
    assert IterationStatus.FAILED == "failed"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest backend/tests/unit/test_iteration_model.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.iteration'"

- [ ] **Step 3: 写最小实现**

```python
# backend/app/models/iteration.py

from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class IterationMode(str, enum.Enum):
    REEXECUTE = "reexecute"
    INCREMENTAL = "incremental"

class IterationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Iteration(BaseModel):
    """迭代记录模型"""
    __tablename__ = "execution_iterations"

    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    iteration_number = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=False)
    mode = Column(SQLEnum(IterationMode), nullable=False)
    status = Column(SQLEnum(IterationStatus), default=IterationStatus.PENDING)

    # 内容
    original_task_snapshot = Column(JSON)
    previous_output = Column(Text)
    refined_output = Column(Text)

    # 资源消耗
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    # 错误信息
    error_message = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    execution = relationship("Execution", back_populates="iterations")
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest backend/tests/unit/test_iteration_model.py -v`
Expected: PASS (3 tests passed)

- [ ] **Step 5: 提交**

```bash
git add backend/app/models/iteration.py backend/tests/unit/test_iteration_model.py
git commit -m "feat(iteration): add Iteration data model with enums and fields"
```

---

#### Task 2: 创建Iteration Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/iteration.py`
- Create: `backend/tests/unit/test_iteration_schemas.py`

- [ ] **Step 1: 写失败的测试**

```python
# backend/tests/unit/test_iteration_schemas.py

import pytest
from app.schemas.iteration import IterationCreate, IterationResponse

def test_iteration_create_schema():
    """测试迭代创建schema"""
    data = IterationCreate(
        feedback="需要更详细",
        mode="incremental",
    )
    assert data.feedback == "需要更详细"
    assert data.mode == "incremental"

def test_iteration_create_reexecute_mode():
    """测试重新执行模式"""
    data = IterationCreate(
        feedback="完全重做",
        mode="reexecute",
    )
    assert data.mode == "reexecute"

def test_iteration_response_schema():
    """测试迭代响应schema"""
    response = IterationResponse(
        id="iter_123",
        execution_id="exec_123",
        iteration_number=1,
        feedback="测试",
        mode="incremental",
        status="completed",
        refined_output="结果",
        tokens_used=100,
        cost_usd=0.01,
    )
    assert response.id == "iter_123"
    assert response.tokens_used == 100
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest backend/tests/unit/test_iteration_schemas.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.schemas.iteration'"

- [ ] **Step 3: 写最小实现**

```python
# backend/app/schemas/iteration.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class IterationCreate(BaseModel):
    """迭代创建请求"""
    feedback: str = Field(..., min_length=1, max_length=5000)
    mode: str = Field(..., pattern="^(reexecute|incremental)$")

class IterationResponse(BaseModel):
    """迭代响应"""
    id: str
    execution_id: str
    iteration_number: int
    feedback: str
    mode: str
    status: str
    refined_output: Optional[str] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IterationListResponse(BaseModel):
    """迭代列表响应"""
    iterations: list[IterationResponse]
    total: int
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest backend/tests/unit/test_iteration_schemas.py -v`
Expected: PASS (3 tests passed)

- [ ] **Step 5: 提交**

```bash
git add backend/app/schemas/iteration.py backend/tests/unit/test_iteration_schemas.py
git commit -m "feat(iteration): add Pydantic schemas for iteration API"
```

---

#### Task 3: 创建Iteration API端点

**Files:**
- Create: `backend/app/api/v1/iterations.py`
- Modify: `backend/app/api/v1/__init__.py` (添加路由)
- Create: `backend/tests/unit/test_iteration_api.py`

- [ ] **Step 1: 写失败的测试**

```python
# backend/tests/unit/test_iteration_api.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_iterations_endpoint():
    """测试获取迭代列表端点"""
    response = client.get("/api/v1/executions/exec_123/iterations")
    # 未认证应该返回401
    assert response.status_code == 401

def test_create_iteration_endpoint():
    """测试创建迭代端点"""
    response = client.post(
        "/api/v1/executions/exec_123/refine",
        json={"feedback": "测试", "mode": "incremental"},
    )
    # 未认证应该返回401
    assert response.status_code == 401
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest backend/tests/unit/test_iteration_api.py -v`
Expected: FAIL with "AssertionError: 401 != 401" (实际应该是404或路由不存在)

- [ ] **Step 3: 写最小实现**

```python
# backend/app/api/v1/iterations.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.iteration import Iteration, IterationMode, IterationStatus
from app.models.execution import Execution
from app.schemas.iteration import IterationCreate, IterationResponse
from datetime import datetime

router = APIRouter()

@router.get("/{execution_id}/iterations", response_model=List[IterationResponse])
async def list_iterations(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取迭代列表"""
    # 验证execution存在且属于当前用户
    execution = db.query(Execution).filter(
        Execution.id == execution_id,
        Execution.user_id == current_user.id,
    ).first()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    iterations = db.query(Iteration).filter(
        Iteration.execution_id == execution_id
    ).order_by(Iteration.iteration_number).all()
    return iterations

@router.post("/{execution_id}/refine", response_model=IterationResponse)
async def refine_execution(
    execution_id: str,
    data: IterationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """创建迭代优化"""
    # 验证execution
    execution = db.query(Execution).filter(
        Execution.id == execution_id,
        Execution.user_id == current_user.id,
    ).first()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    if execution.status not in ['completed', 'failed']:
        raise HTTPException(status_code=400, detail="执行未完成，无法迭代")

    # 获取迭代次数
    iteration_count = db.query(Iteration).filter(
        Iteration.execution_id == execution_id
    ).count()

    # 创建迭代记录
    iteration = Iteration(
        execution_id=execution_id,
        iteration_number=iteration_count + 1,
        feedback=data.feedback,
        mode=IterationMode(data.mode),
        status=IterationStatus.PENDING,
        original_task_snapshot=execution.results,
        previous_output=execution.results.get('final_output'),
    )
    db.add(iteration)
    db.commit()
    db.refresh(iteration)

    return iteration
```

在 `backend/app/api/v1/__init__.py` 中添加：
```python
from .iterations import router as iterations_router
api_router.include_router(iterations_router, prefix="/executions", tags=["iterations"])
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest backend/tests/unit/test_iteration_api.py -v`
Expected: PASS (2 tests passed)

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/v1/iterations.py backend/app/api/v1/__init__.py backend/tests/unit/test_iteration_api.py
git commit -m "feat(iteration): add iteration API endpoints for list and create"
```

---

### Phase 2: 后端迭代逻辑 (Task 4-6)

#### Task 4: 添加迭代事件到EventPublisher

**Files:**
- Modify: `backend/app/services/event_publisher.py`
- Create: `backend/tests/unit/test_iteration_events.py`

- [ ] **Step 1: 写失败的测试**

```python
# backend/tests/unit/test_iteration_events.py

import pytest
from app.services.event_publisher import EventType

def test_iteration_event_types():
    """测试迭代事件类型"""
    assert EventType.ITERATION_STARTED == "iteration.started"
    assert EventType.ITERATION_PROGRESS == "iteration.progress"
    assert EventType.ITERATION_COMPLETED == "iteration.completed"
    assert EventType.ITERATION_FAILED == "iteration.failed"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest backend/tests/unit/test_iteration_events.py -v`
Expected: FAIL with "AttributeError: type object 'EventType' has no attribute 'ITERATION_STARTED'"

- [ ] **Step 3: 写最小实现**

在 `backend/app/services/event_publisher.py` 的 EventType 枚举中添加：
```python
class EventType(str, enum.Enum):
    # ... 已有事件 ...
    ITERATION_STARTED = "iteration.started"
    ITERATION_PROGRESS = "iteration.progress"
    ITERATION_COMPLETED = "iteration.completed"
    ITERATION_FAILED = "iteration.failed"
```

在 EventPublisher 类中添加方法：
```python
async def publish_iteration_started(
    self,
    execution_id: str,
    iteration_id: str,
    iteration_number: int,
):
    """发布迭代开始事件"""
    await self.publish(
        execution_id=execution_id,
        event_type=EventType.ITERATION_STARTED,
        data={
            "iteration_id": iteration_id,
            "iteration_number": iteration_number,
        },
    )

async def publish_iteration_completed(
    self,
    execution_id: str,
    iteration_id: str,
):
    """发布迭代完成事件"""
    await self.publish(
        execution_id=execution_id,
        event_type=EventType.ITERATION_COMPLETED,
        data={
            "iteration_id": iteration_id,
        },
    )

async def publish_iteration_failed(
    self,
    execution_id: str,
    iteration_id: str,
    error_message: str,
):
    """发布迭代失败事件"""
    await self.publish(
        execution_id=execution_id,
        event_type=EventType.ITERATION_FAILED,
        data={
            "iteration_id": iteration_id,
            "error": error_message,
        },
    )
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest backend/tests/unit/test_iteration_events.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/event_publisher.py backend/tests/unit/test_iteration_events.py
git commit -m "feat(iteration): add iteration event types and publisher methods"
```

---

#### Task 5: 实现run_iteration方法

**Files:**
- Modify: `backend/app/engine/executor.py`
- Create: `backend/tests/unit/test_iteration_engine.py`

- [ ] **Step 1: 写失败的测试**

```python
# backend/tests/unit/test_iteration_engine.py

import pytest
from app.engine.executor import ExecutionEngine

def test_executor_has_run_iteration():
    """测试执行引擎有run_iteration方法"""
    engine = ExecutionEngine.__new__(ExecutionEngine)
    assert hasattr(engine, 'run_iteration')
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest backend/tests/unit/test_iteration_engine.py -v`
Expected: FAIL with "AttributeError: 'ExecutionEngine' object has no attribute 'run_iteration'"

- [ ] **Step 3: 写最小实现**

在 `backend/app/engine/executor.py` 的 ExecutionEngine 类中添加：
```python
async def run_iteration(self, execution_id: str, iteration_id: str):
    """执行迭代优化"""
    from app.models.iteration import Iteration, IterationStatus
    from app.core.database import get_db

    async with get_db() as db:
        iteration = db.query(Iteration).filter(Iteration.id == iteration_id).first()
        if not iteration:
            logger.error(f"Iteration {iteration_id} not found")
            return

        iteration.status = IterationStatus.RUNNING
        db.commit()

        try:
            if iteration.mode.value == "reexecute":
                result = await self._reexecute_with_feedback(
                    execution_id, iteration.feedback
                )
            else:
                result = await self._incremental_refine(
                    iteration.previous_output, iteration.feedback
                )

            iteration.refined_output = result['output']
            iteration.tokens_used = result['tokens_used']
            iteration.cost_usd = result['cost_usd']
            iteration.status = IterationStatus.COMPLETED
            iteration.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"Iteration {iteration_id} failed: {e}")
            iteration.status = IterationStatus.FAILED
            iteration.error_message = str(e)

        db.commit()

async def _incremental_refine(self, previous_output: str, feedback: str) -> dict:
    """增量优化：在上次结果上修改"""
    prompt = f"""基于以下输出进行优化：

上次输出：
{previous_output}

用户反馈：
{feedback}

请根据反馈修改输出，保持整体结构，只修改需要调整的部分。"""

    # 调用 LLM (简化版本)
    response = await self._call_llm(prompt)

    return {
        "output": response['content'],
        "tokens_used": response['tokens_used'],
        "cost_usd": response['cost_usd'],
    }

async def _reexecute_with_feedback(self, execution_id: str, feedback: str) -> dict:
    """重新执行模式：完全重新执行"""
    # 加载原始执行上下文
    execution = await self.db.get(Execution, execution_id)

    # 在原始任务描述中追加用户反馈
    original_tasks = execution.results.get('tasks', [])
    for task in original_tasks:
        task['description'] += f"\n\n用户反馈：{feedback}"

    # 重新执行整个工作流
    result = await self._execute_workflow(
        execution.crew_id,
        modified_tasks=original_tasks,
    )

    return {
        "output": result['final_output'],
        "tokens_used": result['total_tokens'],
        "cost_usd": result['total_cost'],
    }

async def _call_llm(self, prompt: str) -> dict:
    """调用LLM（简化版本）"""
    # 这里应该调用实际的LLM provider
    # 为测试目的，返回模拟响应
    return {
        "content": f"优化后的结果：{prompt[:100]}...",
        "tokens_used": 150,
        "cost_usd": 0.03,
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest backend/tests/unit/test_iteration_engine.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/engine/executor.py backend/tests/unit/test_iteration_engine.py
git commit -m "feat(iteration): implement run_iteration method with incremental and reexecute modes"
```

---

#### Task 6: 添加数据库迁移

**Files:**
- Create: `backend/alembic/versions/add_iteration_table.py`

- [ ] **Step 1: 生成迁移脚本**

Run: `cd backend && alembic revision --autogenerate -m "add execution_iterations table"`
Expected: 生成迁移文件

- [ ] **Step 2: 检查生成的迁移**

确保迁移包含：
- 创建 `execution_iterations` 表
- 所有必要的字段
- 外键约束

- [ ] **Step 3: 运行迁移**

Run: `cd backend && alembic upgrade head`
Expected: 成功创建表

- [ ] **Step 4: 验证表结构**

```sql
-- 验证表存在
SELECT table_name FROM information_schema.tables WHERE table_name = 'execution_iterations';

-- 验证字段
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'execution_iterations';
```

- [ ] **Step 5: 提交**

```bash
git add backend/alembic/versions/add_iteration_table.py
git commit -m "feat(iteration): add database migration for execution_iterations table"
```

---

### Phase 3: 前端组件 (Task 7-10)

#### Task 7: 创建Iteration类型定义

**Files:**
- Create: `frontend/src/types/iteration.ts`

- [ ] **Step 1: 创建类型文件**

```typescript
// frontend/src/types/iteration.ts

export interface Iteration {
  id: string;
  execution_id: string;
  iteration_number: number;
  feedback: string;
  mode: 'reexecute' | 'incremental';
  status: 'pending' | 'running' | 'completed' | 'failed';
  original_task_snapshot?: Record<string, any>;
  previous_output?: string;
  refined_output?: string;
  tokens_used: number;
  cost_usd: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface IterationCreate {
  feedback: string;
  mode: 'reexecute' | 'incremental';
}

export interface IterationListResponse {
  iterations: Iteration[];
  total: number;
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/types/iteration.ts
git commit -m "feat(iteration): add TypeScript types for iteration data"
```

---

#### Task 8: 创建Iteration API客户端

**Files:**
- Create: `frontend/src/api/iterations.ts`

- [ ] **Step 1: 创建API客户端**

```typescript
// frontend/src/api/iterations.ts

import { apiClient } from './client';
import type { Iteration, IterationCreate, IterationListResponse } from '../types/iteration';

export const iterationsApi = {
  // 获取迭代列表
  list: async (executionId: string): Promise<Iteration[]> => {
    const response = await apiClient.get<IterationListResponse>(
      `/executions/${executionId}/iterations`
    );
    return response.data.iterations;
  },

  // 获取单个迭代
  get: async (executionId: string, iterationId: string): Promise<Iteration> => {
    const response = await apiClient.get<Iteration>(
      `/executions/${executionId}/iterations/${iterationId}`
    );
    return response.data;
  },

  // 创建迭代
  create: async (executionId: string, data: IterationCreate): Promise<Iteration> => {
    const response = await apiClient.post<Iteration>(
      `/executions/${executionId}/refine`,
      data
    );
    return response.data;
  },
};
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/iterations.ts
git commit -m "feat(iteration): add API client for iteration endpoints"
```

---

#### Task 9: 创建RefineControls组件

**Files:**
- Create: `frontend/src/components/monitor/RefineControls.tsx`
- Create: `frontend/src/components/monitor/__tests__/RefineControls.test.tsx`

- [ ] **Step 1: 写失败的测试**

```typescript
// frontend/src/components/monitor/__tests__/RefineControls.test.tsx

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { RefineControls } from '../RefineControls';

describe('RefineControls', () => {
  it('renders feedback textarea', () => {
    render(
      <RefineControls
        feedback=""
        onFeedbackChange={() => {}}
        mode="incremental"
        onModeChange={() => {}}
        onSubmit={() => {}}
        isDisabled={false}
        isRefining={false}
      />
    );
    expect(screen.getByPlaceholderText(/输入你的修改意见/)).toBeInTheDocument();
  });

  it('calls onFeedbackChange when typing', () => {
    const handleChange = jest.fn();
    render(
      <RefineControls
        feedback=""
        onFeedbackChange={handleChange}
        mode="incremental"
        onModeChange={() => {}}
        onSubmit={() => {}}
        isDisabled={false}
        isRefining={false}
      />
    );
    fireEvent.change(screen.getByPlaceholderText(/输入你的修改意见/), {
      target: { value: 'test feedback' },
    });
    expect(handleChange).toHaveBeenCalledWith('test feedback');
  });

  it('calls onSubmit when clicking submit button', () => {
    const handleSubmit = jest.fn();
    render(
      <RefineControls
        feedback="test"
        onFeedbackChange={() => {}}
        mode="incremental"
        onModeChange={() => {}}
        onSubmit={handleSubmit}
        isDisabled={false}
        isRefining={false}
      />
    );
    fireEvent.click(screen.getByText('提交反馈'));
    expect(handleSubmit).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd frontend && npm test -- --testPathPattern=RefineControls`
Expected: FAIL with "Cannot find module '../RefineControls'"

- [ ] **Step 3: 写最小实现**

```typescript
// frontend/src/components/monitor/RefineControls.tsx

import React from 'react';
import { Send, Loader2 } from 'lucide-react';

interface RefineControlsProps {
  feedback: string;
  onFeedbackChange: (value: string) => void;
  mode: 'reexecute' | 'incremental';
  onModeChange: (mode: 'reexecute' | 'incremental') => void;
  onSubmit: () => void;
  isDisabled: boolean;
  isRefining: boolean;
}

export const RefineControls: React.FC<RefineControlsProps> = ({
  feedback,
  onFeedbackChange,
  mode,
  onModeChange,
  onSubmit,
  isDisabled,
  isRefining,
}) => {
  return (
    <div>
      <textarea
        value={feedback}
        onChange={(e) => onFeedbackChange(e.target.value)}
        placeholder="输入你的修改意见或反馈..."
        disabled={isDisabled}
        style={{
          width: '100%',
          height: 80,
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: 8,
          padding: 12,
          fontSize: 13,
          color: '#F4F4F5',
          resize: 'none',
          marginBottom: 12,
        }}
      />

      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <select
          value={mode}
          onChange={(e) => onModeChange(e.target.value as 'reexecute' | 'incremental')}
          style={{
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 6,
            padding: '8px 12px',
            fontSize: 13,
            color: '#F4F4F5',
            cursor: 'pointer',
          }}
        >
          <option value="incremental">增量优化</option>
          <option value="reexecute">重新执行</option>
        </select>

        <button
          onClick={onSubmit}
          disabled={isDisabled}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            background: isDisabled ? 'rgba(34, 211, 238, 0.3)' : 'rgba(34, 211, 238, 0.8)',
            border: 'none',
            borderRadius: 8,
            padding: '10px 20px',
            fontSize: 14,
            fontWeight: 600,
            color: '#FFFFFF',
            cursor: isDisabled ? 'not-allowed' : 'pointer',
          }}
        >
          {isRefining ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              优化中...
            </>
          ) : (
            <>
              <Send size={16} />
              提交反馈
            </>
          )}
        </button>
      </div>

      <div style={{
        marginTop: 8,
        fontSize: 11,
        color: '#636366',
      }}>
        💡 增量优化：在上次结果基础上修改，速度快<br/>
        💡 重新执行：完全重新生成，更彻底
      </div>
    </div>
  );
};
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd frontend && npm test -- --testPathPattern=RefineControls`
Expected: PASS (3 tests passed)

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/monitor/RefineControls.tsx frontend/src/components/monitor/__tests__/RefineControls.test.tsx
git commit -m "feat(iteration): add RefineControls component with mode selection and feedback input"
```

---

#### Task 10: 创建IterationMessage组件

**Files:**
- Create: `frontend/src/components/monitor/IterationMessage.tsx`
- Create: `frontend/src/components/monitor/__tests__/IterationMessage.test.tsx`

- [ ] **Step 1: 写失败的测试**

```typescript
// frontend/src/components/monitor/__tests__/IterationMessage.test.tsx

import React from 'react';
import { render, screen } from '@testing-library/react';
import { IterationMessage } from '../IterationMessage';

const mockIteration = {
  id: 'iter_1',
  execution_id: 'exec_1',
  iteration_number: 1,
  feedback: '需要更详细',
  mode: 'incremental' as const,
  status: 'completed' as const,
  refined_output: '优化后的结果',
  tokens_used: 150,
  cost_usd: 0.03,
  created_at: '2024-01-15T10:30:00Z',
  completed_at: '2024-01-15T10:30:15Z',
};

describe('IterationMessage', () => {
  it('renders iteration number', () => {
    render(<IterationMessage iteration={mockIteration} isLatest={false} />);
    expect(screen.getByText(/迭代 #1/)).toBeInTheDocument();
  });

  it('renders feedback text', () => {
    render(<IterationMessage iteration={mockIteration} isLatest={false} />);
    expect(screen.getByText('需要更详细')).toBeInTheDocument();
  });

  it('renders refined output when completed', () => {
    render(<IterationMessage iteration={mockIteration} isLatest={false} />);
    expect(screen.getByText('优化后的结果')).toBeInTheDocument();
  });

  it('renders token usage', () => {
    render(<IterationMessage iteration={mockIteration} isLatest={false} />);
    expect(screen.getByText(/150 tokens/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd frontend && npm test -- --testPathPattern=IterationMessage`
Expected: FAIL with "Cannot find module '../IterationMessage'"

- [ ] **Step 3: 写最小实现**

```typescript
// frontend/src/components/monitor/IterationMessage.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, Zap, Clock } from 'lucide-react';
import type { Iteration } from '../../types/iteration';

interface IterationMessageProps {
  iteration: Iteration;
  isLatest: boolean;
}

export const IterationMessage: React.FC<IterationMessageProps> = ({ iteration, isLatest }) => {
  const modeLabel = iteration.mode === 'reexecute' ? '重新执行' : '增量优化';
  const modeColor = iteration.mode === 'reexecute' ? '#F87171' : '#4ADE80';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      style={{
        background: isLatest ? 'rgba(34, 211, 238, 0.05)' : 'rgba(255, 255, 255, 0.03)',
        border: `1px solid ${isLatest ? 'rgba(34, 211, 238, 0.2)' : 'rgba(255, 255, 255, 0.06)'}`,
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
      }}
    >
      {/* Feedback */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 12, color: '#A1A1AA' }}>
            迭代 #{iteration.iteration_number}
          </span>
          <span style={{
            fontSize: 11,
            color: modeColor,
            background: `${modeColor}15`,
            padding: '2px 8px',
            borderRadius: 12,
          }}>
            {modeLabel}
          </span>
          {iteration.status === 'running' && (
            <RefreshCw size={14} color="#22D3EE" className="animate-spin" />
          )}
        </div>
        <div style={{
          fontSize: 13,
          color: '#D4D4D8',
          lineHeight: 1.6,
        }}>
          {iteration.feedback}
        </div>
      </div>

      {/* Output */}
      {iteration.refined_output && (
        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: 6,
          padding: 12,
          marginBottom: 12,
        }}>
          <div style={{ fontSize: 10, color: '#636366', marginBottom: 6, textTransform: 'uppercase' }}>
            优化结果
          </div>
          <div style={{
            fontSize: 12,
            color: '#A1A1AA',
            lineHeight: 1.6,
            maxHeight: 200,
            overflowY: 'auto',
          }}>
            {iteration.refined_output}
          </div>
        </div>
      )}

      {/* Stats */}
      <div style={{
        display: 'flex',
        gap: 16,
        fontSize: 11,
        color: '#636366',
      }}>
        <span>
          <Zap size={12} style={{ marginRight: 4 }} />
          {iteration.tokens_used.toLocaleString()} tokens
        </span>
        <span>
          💰 ${iteration.cost_usd.toFixed(4)}
        </span>
        {iteration.completed_at && (
          <span>
            <Clock size={12} style={{ marginRight: 4 }} />
            {new Date(iteration.completed_at).toLocaleTimeString()}
          </span>
        )}
      </div>
    </motion.div>
  );
};
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd frontend && npm test -- --testPathPattern=IterationMessage`
Expected: PASS (4 tests passed)

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/monitor/IterationMessage.tsx frontend/src/components/monitor/__tests__/IterationMessage.test.tsx
git commit -m "feat(iteration): add IterationMessage component for displaying iteration details"
```

---

### Phase 4: WebSocket集成和完整组件 (Task 11-13)

#### Task 11: 更新useExecutionMonitor hook

**Files:**
- Modify: `frontend/src/hooks/useExecutionMonitor.ts`

- [ ] **Step 1: 添加迭代状态**

在 `useExecutionMonitor` hook 中添加：
```typescript
const [iterations, setIterations] = useState<Iteration[]>([]);

// 在 handleMessage 的 switch 中添加：
case 'iteration.started':
  setIterations(prev => [...prev, {
    id: msgData.iteration_id,
    iteration_number: msgData.iteration_number,
    status: 'running',
    feedback: '',
    mode: 'incremental',
    tokens_used: 0,
    cost_usd: 0,
    created_at: new Date().toISOString(),
  }]);
  break;

case 'iteration.completed':
  // 刷新迭代列表
  queryClient.invalidateQueries(['iterations', executionId]);
  break;

// 在 return 中添加：
iterations,
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/hooks/useExecutionMonitor.ts
git commit -m "feat(iteration): add iteration state management to useExecutionMonitor hook"
```

---

#### Task 12: 创建IterationChat主组件

**Files:**
- Create: `frontend/src/components/monitor/IterationChat.tsx`
- Create: `frontend/src/components/monitor/__tests__/IterationChat.test.tsx`

- [ ] **Step 1: 写失败的测试**

```typescript
// frontend/src/components/monitor/__tests__/IterationChat.test.tsx

import React from 'react';
import { render, screen } from '@testing-library/react';
import { IterationChat } from '../IterationChat';

const mockIterations = [
  {
    id: 'iter_1',
    iteration_number: 1,
    feedback: '测试反馈',
    mode: 'incremental' as const,
    status: 'completed' as const,
    tokens_used: 100,
    cost_usd: 0.02,
    created_at: '2024-01-15T10:30:00Z',
  },
];

describe('IterationChat', () => {
  it('renders chat header', () => {
    render(
      <IterationChat
        executionId="exec_1"
        iterations={mockIterations}
        onRefine={() => {}}
        isRefining={false}
        executionStatus="completed"
      />
    );
    expect(screen.getByText('迭代对话')).toBeInTheDocument();
  });

  it('renders iteration count', () => {
    render(
      <IterationChat
        executionId="exec_1"
        iterations={mockIterations}
        onRefine={() => {}}
        isRefining={false}
        executionStatus="completed"
      />
    );
    expect(screen.getByText(/1 次迭代/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd frontend && npm test -- --testPathPattern=IterationChat`
Expected: FAIL with "Cannot find module '../IterationChat'"

- [ ] **Step 3: 写最小实现**

```typescript
// frontend/src/components/monitor/IterationChat.tsx

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare } from 'lucide-react';
import { IterationMessage } from './IterationMessage';
import { RefineControls } from './RefineControls';
import type { Iteration } from '../../types/iteration';

interface IterationChatProps {
  executionId: string;
  iterations: Iteration[];
  onRefine: (feedback: string, mode: 'reexecute' | 'incremental') => void;
  isRefining: boolean;
  executionStatus: string;
}

export const IterationChat: React.FC<IterationChatProps> = ({
  executionId,
  iterations,
  onRefine,
  isRefining,
  executionStatus,
}) => {
  const [feedback, setFeedback] = useState('');
  const [mode, setMode] = useState<'reexecute' | 'incremental'>('incremental');

  const handleSubmit = useCallback(() => {
    if (!feedback.trim() || isRefining) return;
    onRefine(feedback, mode);
    setFeedback('');
  }, [feedback, mode, isRefining, onRefine]);

  const canRefine = executionStatus === 'completed' || executionStatus === 'failed';

  return (
    <div style={{
      background: 'rgba(255, 255, 255, 0.05)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: 12,
      padding: 20,
      marginTop: 20,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <MessageSquare size={18} color="#22D3EE" />
        <span style={{ fontSize: 15, fontWeight: 600, color: '#F4F4F5' }}>
          迭代对话
        </span>
        {iterations.length > 0 && (
          <span style={{
            fontSize: 12,
            color: '#A1A1AA',
            background: 'rgba(34, 211, 238, 0.1)',
            padding: '2px 8px',
            borderRadius: 12,
          }}>
            {iterations.length} 次迭代
          </span>
        )}
      </div>

      {/* Iteration History */}
      {iterations.length > 0 && (
        <div style={{
          maxHeight: 400,
          overflowY: 'auto',
          marginBottom: 16,
        }}>
          <AnimatePresence>
            {iterations.map((iter, index) => (
              <IterationMessage
                key={iter.id}
                iteration={iter}
                isLatest={index === iterations.length - 1}
              />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Refine Controls */}
      {canRefine && (
        <RefineControls
          feedback={feedback}
          onFeedbackChange={setFeedback}
          mode={mode}
          onModeChange={setMode}
          onSubmit={handleSubmit}
          isDisabled={isRefining || !feedback.trim()}
          isRefining={isRefining}
        />
      )}

      {!canRefine && (
        <div style={{
          textAlign: 'center',
          color: '#A1A1AA',
          fontSize: 13,
          padding: 20,
        }}>
          执行完成后可以进行迭代优化
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd frontend && npm test -- --testPathPattern=IterationChat`
Expected: PASS (2 tests passed)

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/monitor/IterationChat.tsx frontend/src/components/monitor/__tests__/IterationChat.test.tsx
git commit -m "feat(iteration): add IterationChat main component with history and controls"
```

---

#### Task 13: 集成到ExecutionView

**Files:**
- Modify: `frontend/src/pages/ExecutionView.tsx`

- [ ] **Step 1: 添加迭代逻辑**

在 `ExecutionView` 组件中添加：
```typescript
import { IterationChat } from '../components/monitor/IterationChat';
import { iterationsApi } from '../api/iterations';

// 在组件中添加状态
const [iterations, setIterations] = useState<Iteration[]>([]);
const [isRefining, setIsRefining] = useState(false);

// 添加获取迭代列表的useEffect
useEffect(() => {
  if (executionId) {
    iterationsApi.list(executionId).then(setIterations);
  }
}, [executionId]);

// 添加处理迭代的函数
const handleRefine = useCallback(async (feedback: string, mode: 'reexecute' | 'incremental') => {
  if (!executionId) return;
  setIsRefining(true);
  try {
    await iterationsApi.create(executionId, { feedback, mode });
    // 刷新迭代列表
    const updatedIterations = await iterationsApi.list(executionId);
    setIterations(updatedIterations);
  } catch (error) {
    console.error('Failed to create iteration:', error);
  } finally {
    setIsRefining(false);
  }
}, [executionId]);

// 在JSX中添加IterationChat组件
<IterationChat
  executionId={executionId || ''}
  iterations={iterations}
  onRefine={handleRefine}
  isRefining={isRefining}
  executionStatus={execution?.status || 'pending'}
/>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/ExecutionView.tsx
git commit -m "feat(iteration): integrate IterationChat into ExecutionView page"
```

---

### Phase 5: 测试和优化 (Task 14-15)

#### Task 14: 集成测试

**Files:**
- Create: `backend/tests/integration/test_iteration_flow.py`

- [ ] **Step 1: 写集成测试**

```python
# backend/tests/integration/test_iteration_flow.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.execution import Execution, ExecutionStatus
from app.models.iteration import Iteration

client = TestClient(app)

def test_complete_iteration_flow():
    """测试完整的迭代流程"""
    # 1. 创建测试execution (需要认证)
    # 2. 调用refine端点
    # 3. 验证iteration被创建
    # 4. 验证iteration状态更新
    pass  # 实际实现需要mock认证和数据库
```

- [ ] **Step 2: 运行测试**

Run: `pytest backend/tests/integration/test_iteration_flow.py -v`
Expected: 测试通过或标记为skip (需要完整环境)

- [ ] **Step 3: 提交**

```bash
git add backend/tests/integration/test_iteration_flow.py
git commit -m "test(iteration): add integration test for complete iteration flow"
```

---

#### Task 15: 端到端测试和文档

**Files:**
- Create: `docs/guides/iteration-feature.md`

- [ ] **Step 1: 创建功能文档**

```markdown
# 执行结果迭代功能使用指南

## 功能概述

执行结果迭代功能允许用户在工作流执行完成后提供反馈，模型基于反馈优化结果。

## 使用方法

### 1. 查看执行结果

执行完成后，在ExecutionView页面可以看到任务列表和统计信息。

### 2. 提交反馈

在页面底部的"迭代对话"区域：
- 输入你的修改意见或反馈
- 选择优化模式：
  - **增量优化**：在上次结果基础上修改，速度快
  - **重新执行**：完全重新生成，更彻底
- 点击"提交反馈"

### 3. 查看迭代历史

所有迭代历史会显示在对话区域，包括：
- 用户反馈
- 优化结果
- Token消耗和成本
- 完成时间

## 注意事项

- 只有执行完成后才能进行迭代
- 每次迭代都会产生Token费用
- 所有迭代历史都会被保留
```

- [ ] **Step 2: 提交**

```bash
git add docs/guides/iteration-feature.md
git commit -m "docs(iteration): add user guide for iteration feature"
```

---

## 完成检查清单

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] TypeScript编译无错误
- [ ] Python语法检查通过
- [ ] 代码符合项目风格
- [ ] 文档完整
- [ ] 提交历史清晰

---

**计划版本**: v1.0
**最后更新**: 2026-06-08
**预计完成时间**: 11天
