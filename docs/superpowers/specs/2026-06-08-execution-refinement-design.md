# 执行结果对话式迭代功能设计

**日期**: 2026-06-08
**状态**: 已批准

---

## 1. 功能概述

实现执行结果的对话式迭代功能，允许用户在工作流执行完成后提供反馈，模型基于反馈优化结果，类似于WorkBuddy/Codex的交互方式。

### 核心能力
- **双级迭代**: 支持工作流级别和任务级别的迭代
- **混合模式**: 用户可选择「重新执行」或「增量优化」
- **完整历史**: 保留所有迭代的反馈和结果
- **实时更新**: WebSocket推送迭代进度
- **无限制**: 允许无限次迭代，不限制成本

---

## 2. 架构设计

### 2.1 前端架构

```
┌────────────────────────────────────┐
│ ExecutionView 页面                  │
├────────────────────────────────────┤
│ 统计面板 (Token/费用/时长)          │
├────────────────────────────────────┤
│ Tab 1: Timeline (当前执行视图)      │
│ Tab 2: Realtime (实时监控)         │
│ Tab 3: 迭代历史 (新增)             │
├────────────────────────────────────┤
│ 任务执行列表                        │
│   ├─ 任务1 (输出/思考过程)         │
│   └─ 任务2 (输出/思考过程)         │
├────────────────────────────────────┤
│ 💬 迭代对话区 (新增)               │
│ ┌──────────────────────────────┐  │
│ │ [迭代历史 - 按时间排列]       │  │
│ │ ├─ 迭代1: 用户反馈           │  │
│ │ │         Agent优化结果       │  │
│ │ └─ 迭代2: 用户反馈           │  │
│ │           Agent新结果         │  │
│ └──────────────────────────────┘  │
│ ┌──────────────────────────────┐  │
│ │ [输入框]  [重新执行|增量优化] │  │
│ │         [提交按钮]            │  │
│ └──────────────────────────────┘  │
└────────────────────────────────────┘
```

### 2.2 后端架构

#### API端点

**POST /api/v1/executions/{id}/refine**
- 创建迭代任务
- 参数: `{ feedback: string, mode: 'reexecute' | 'incremental' }`
- 返回: `{ iteration_id: string, status: string }`

**GET /api/v1/executions/{id}/iterations**
- 获取所有迭代历史
- 返回: `[Iteration]` 数组

**GET /api/v1/executions/{id}/iterations/{iter_id}**
- 获取单个迭代详情

#### 数据模型

```sql
CREATE TABLE execution_iterations (
  id VARCHAR(36) PRIMARY KEY,
  execution_id VARCHAR(36) NOT NULL,
  iteration_number INT NOT NULL,
  feedback TEXT NOT NULL,
  mode ENUM('reexecute', 'incremental') NOT NULL,
  status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
  original_task_snapshot JSON,      -- 原始任务快照
  previous_output TEXT,             -- 上一次输出
  refined_output TEXT,              -- 优化后的输出
  tokens_used INT DEFAULT 0,
  cost_usd FLOAT DEFAULT 0.0,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  FOREIGN KEY (execution_id) REFERENCES executions(id)
);
```

### 2.3 执行流程

```
用户提交反馈
  ↓
前端调用 POST /executions/{id}/refine
  ↓
后端创建 Iteration 记录
  ↓
启动迭代任务
  ├─ 重新执行模式：完全重新执行工作流
  │   ├─ 加载原始任务上下文
  │   ├─ 加载用户反馈
  │   └─ 调用 LLM 重新生成
  │
  └─ 增量优化模式：在上次结果上优化
      ├─ 加载上一次输出
      ├─ 加载用户反馈
      └─ 调用 LLM 在上次结果上修改
  ↓
WebSocket 推送进度更新
  ├─ iteration.started
  ├─ iteration.progress
  └─ iteration.completed
  ↓
完成后更新 Iteration 记录
  ↓
前端实时显示迭代结果
```

---

## 3. 组件设计

### 3.1 IterationChat 组件

**文件**: `frontend/src/components/monitor/IterationChat.tsx`

**职责**: 显示迭代历史和输入框

**Props**:
```typescript
interface IterationChatProps {
  executionId: string;
  iterations: Iteration[];
  onRefine: (feedback: string, mode: 'reexecute' | 'incremental') => void;
  isRefining: boolean;
  executionStatus: string;
}
```

**状态**:
- `feedback`: 用户输入的反馈文本
- `mode`: 选择的迭代模式 ('reexecute' | 'incremental')
- `showHistory`: 是否显示完整历史

**核心功能**:
- 显示迭代历史列表
- 提供反馈输入框
- 模式选择（重新执行/增量优化）
- 提交按钮
- 加载状态指示

### 3.2 IterationMessage 组件

**文件**: `frontend/src/components/monitor/IterationMessage.tsx`

**职责**: 显示单个迭代的反馈和结果

**Props**:
```typescript
interface IterationMessageProps {
  iteration: Iteration;
  isLatest: boolean;
}
```

**显示内容**:
- 用户反馈
- 迭代模式标签 (重新执行/增量)
- Agent输出
- Token消耗和成本
- 完成时间
- 状态指示器 (pending/running/completed)

### 3.3 RefineControls 组件

**文件**: `frontend/src/components/monitor/RefineControls.tsx`

**职责**: 迭代控制按钮

**Props**:
```typescript
interface RefineControlsProps {
  mode: 'reexecute' | 'incremental';
  onModeChange: (mode: 'reexecute' | 'incremental') => void;
  onSubmit: () => void;
  isDisabled: boolean;
}
```

**控件**:
- 模式选择下拉框
- 提交按钮
- 加载状态

---

## 4. API 设计

### 4.1 创建迭代

**POST** `/api/v1/executions/{execution_id}/refine`

**请求**:
```json
{
  "feedback": "这个结果需要更详细，特别是第2部分",
  "mode": "incremental"
}
```

**响应**:
```json
{
  "iteration_id": "iter_abc123",
  "status": "running",
  "estimated_tokens": 1500,
  "estimated_cost": 0.03
}
```

**验证规则**:
- execution_id 必须存在
- execution 必须属于当前用户
- execution.status 必须为 'completed' 或 'failed'
- feedback 不能为空
- mode 必须为 'reexecute' 或 'incremental'

### 4.2 获取迭代列表

**GET** `/api/v1/executions/{execution_id}/iterations`

**响应**:
```json
[
  {
    "id": "iter_abc123",
    "iteration_number": 1,
    "feedback": "这个结果需要更详细",
    "mode": "incremental",
    "status": "completed",
    "refined_output": "优化后的完整输出...",
    "tokens_used": 1234,
    "cost_usd": 0.02,
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:30:15Z"
  }
]
```

### 4.3 获取单个迭代

**GET** `/api/v1/executions/{execution_id}/iterations/{iteration_id}`

**响应**: 完整的Iteration对象

---

## 5. 组件实现

### 5.1 IterationChat

```typescript
// frontend/src/components/monitor/IterationChat.tsx

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, RefreshCw, Zap, Send } from 'lucide-react';
import { IterationMessage } from './IterationMessage';
import { RefineControls } from './RefineControls';

interface Iteration {
  id: string;
  iteration_number: number;
  feedback: string;
  mode: 'reexecute' | 'incremental';
  status: string;
  refined_output: string;
  tokens_used: number;
  cost_usd: number;
  created_at: string;
  completed_at?: string;
}

export const IterationChat: React.FC<{
  executionId: string;
  iterations: Iteration[];
  onRefine: (feedback: string, mode: 'reexecute' | 'incremental') => void;
  isRefining: boolean;
  executionStatus: string;
}> = ({ executionId, iterations, onRefine, isRefining, executionStatus }) => {
  const [feedback, setFeedback] = useState('');
  const [mode, setMode] = useState<'reexecute' | 'incremental'>('incremental');
  const [showHistory, setShowHistory] = useState(true);

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
      {showHistory && iterations.length > 0 && (
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

### 5.2 IterationMessage

```typescript
// frontend/src/components/monitor/IterationMessage.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, Zap, Clock } from 'lucide-react';

interface Iteration {
  id: string;
  iteration_number: number;
  feedback: string;
  mode: 'reexecute' | 'incremental';
  status: string;
  refined_output: string;
  tokens_used: number;
  cost_usd: number;
  created_at: string;
  completed_at?: string;
}

export const IterationMessage: React.FC<{
  iteration: Iteration;
  isLatest: boolean;
}> = ({ iteration, isLatest }) => {
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

### 5.3 RefineControls

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

---

## 6. 后端实现

### 6.1 数据模型

```python
# backend/app/models/iteration.py

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
    original_task_snapshot = Column(JSON)  # 原始任务快照
    previous_output = Column(Text)         # 上一次输出
    refined_output = Column(Text)          # 优化后的输出

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

### 6.2 API 端点

```python
# backend/app/api/v1/iterations.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.iteration import Iteration, IterationMode, IterationStatus
from app.schemas.iteration import IterationCreate, IterationResponse
from app.engine.executor import ExecutionEngine

router = APIRouter()

@router.post("/{execution_id}/refine", response_model=IterationResponse)
async def refine_execution(
    execution_id: str,
    data: IterationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """创建迭代优化"""
    # 验证 execution
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问")
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

    # 启动迭代任务
    engine = ExecutionEngine()
    asyncio.create_task(
        engine.run_iteration(execution_id, iteration.id)
    )

    return iteration

@router.get("/{execution_id}/iterations", response_model=List[IterationResponse])
async def list_iterations(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取迭代列表"""
    iterations = db.query(Iteration).filter(
        Iteration.execution_id == execution_id
    ).order_by(Iteration.iteration_number).all()
    return iterations
```

### 6.3 执行引擎

```python
# backend/app/engine/executor.py

async def run_iteration(self, execution_id: str, iteration_id: str):
    """执行迭代优化"""
    async with get_db_session() as db:
        iteration = await db.get(Iteration, iteration_id)
        iteration.status = IterationStatus.RUNNING
        await db.commit()

        try:
            if iteration.mode == IterationMode.REEXECUTE:
                # 重新执行模式
                result = await self._reexecute_with_feedback(
                    execution_id, iteration.feedback
                )
            else:
                # 增量优化模式
                result = await self._incremental_refine(
                    iteration.previous_output, iteration.feedback
                )

            iteration.refined_output = result['output']
            iteration.tokens_used = result['tokens_used']
            iteration.cost_usd = result['cost_usd']
            iteration.status = IterationStatus.COMPLETED
            iteration.completed_at = datetime.utcnow()

        except Exception as e:
            iteration.status = IterationStatus.FAILED
            iteration.error_message = str(e)

        await db.commit()

        # WebSocket 推送完成事件
        await event_publisher.publish_iteration_completed(
            execution_id, iteration.id
        )

async def _incremental_refine(self, previous_output: str, feedback: str) -> dict:
    """增量优化：在上次结果上修改"""
    prompt = f"""基于以下输出进行优化：

上次输出：
{previous_output}

用户反馈：
{feedback}

请根据反馈修改输出，保持整体结构，只修改需要调整的部分。"""

    # 调用 LLM
    response = await self.llm.chat(
        messages=[{"role": "user", "content": prompt}],
        model=self.model,
    )

    return {
        "output": response.content,
        "tokens_used": response.tokens_used,
        "cost_usd": response.cost_usd,
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
```

---

## 7. WebSocket 事件

### 7.1 迭代事件

```python
# backend/app/services/event_publisher.py

class EventType(str, enum.Enum):
    # ... 已有事件 ...
    ITERATION_STARTED = "iteration.started"
    ITERATION_PROGRESS = "iteration.progress"
    ITERATION_COMPLETED = "iteration.completed"
    ITERATION_FAILED = "iteration.failed"

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
```

### 7.2 前端接收

```typescript
// frontend/src/hooks/useExecutionMonitor.ts

case 'iteration.started':
  // 显示迭代开始提示
  setIterations(prev => [...prev, {
    id: msgData.iteration_id,
    iteration_number: msgData.iteration_number,
    status: 'running',
  }]);
  break;

case 'iteration.completed':
  // 刷新迭代列表
  queryClient.invalidateQueries(['iterations', executionId]);
  break;
```

---

## 8. UI/UX 设计

### 8.1 布局

```
┌─ 统计面板 ─────────────────────────┐
│ Token: 5,432 | 费用: $0.15 | 时长: 45s │
└─────────────────────────────────────┘

┌─ Tab 切换 ─────────────────────────┐
│ [Timeline] [实时监控] [迭代历史]  │
└─────────────────────────────────────┘

┌─ 任务列表 (Timeline) ─────────────┐
│ ● Task 1: 数据分析... ✅          │
│ ○ Task 2: 生成报告... 🔄          │
└─────────────────────────────────────┘

┌─ 迭代对话区 ──────────────────────┐
│ 💬 迭代历史 (2次)                 │
│ ├─ 迭代1: "需要更详细"           │
│ │         ↓ 已优化                │
│ └─ 迭代2: "调整格式"             │
│           ↓ 已优化                │
├─────────────────────────────────────┤
│ 📝 输入新反馈                      │
│ ┌──────────────────────────────┐   │
│ │ 在这里输入你的修改意见...     │   │
│ └──────────────────────────────┘   │
│ [增量优化 ▼] [提交]               │
└─────────────────────────────────────┘
```

### 8.2 交互流程

1. **提交反馈**
   - 用户输入反馈文本
   - 选择模式 (重新执行/增量)
   - 点击"提交"
   - 显示加载状态

2. **迭代执行**
   - 显示 "Agent 正在优化..."
   - 实时显示思考过程
   - WebSocket 推送进度

3. **结果展示**
   - 新结果以新卡片形式出现
   - 高亮显示变化
   - 显示成本和Token

4. **历史管理**
   - 点击"迭代历史"Tab
   - 看到所有迭代的完整列表
   - 可以对比不同版本

---

## 9. 安全性设计

1. **权限验证** — 只能迭代自己的执行
2. **成本追踪** — 记录每次迭代的Token和成本
3. **内容过滤** — 防止恶意输入
4. **日志记录** — 记录所有迭代操作

---

## 10. 测试策略

### 10.1 单元测试
- 迭代逻辑
- API端点
- 数据模型

### 10.2 集成测试
- 完整的迭代流程
- WebSocket事件
- 权限验证

### 10.3 性能测试
- 多次迭代的性能
- 并发迭代
- 数据库查询优化

### 10.4 用户测试
- 实际用户反馈
- 易用性测试
- 错误处理测试

---

## 11. 实现阶段

### Phase 1: 数据模型和API (2天)
- 创建 Iteration 数据模型
- 实现 POST /refine API
- 实现 GET /iterations API

### Phase 2: 后端迭代逻辑 (3天)
- 实现 run_iteration 方法
- 实现增量优化逻辑
- 实现重新执行逻辑

### Phase 3: 前端组件 (3天)
- 实现 IterationChat 组件
- 实现 IterationMessage 组件
- 实现 RefineControls 组件

### Phase 4: WebSocket集成 (1天)
- 迭代事件推送
- 实时进度更新

### Phase 5: 测试和优化 (2天)
- 单元测试
- 集成测试
- 性能优化

**总计: 11天**

---

## 12. 成功指标

1. **功能完整性** — 能成功进行迭代优化
2. **用户体验** — 交互直观，易于使用
3. **性能** — 迭代响应时间 < 30秒
4. **稳定性** — 无崩溃，错误处理完善
5. **可扩展性** — 易于添加新功能

---

**文档版本**: v1.0
**最后更新**: 2026-06-08
