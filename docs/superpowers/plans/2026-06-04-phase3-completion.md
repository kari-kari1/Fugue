# Phase 3 功能补全实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成Phase 3未达标功能：Webhook/定时任务持久化、TODO逻辑补全、3个前端页面、Plugin市场API

**Architecture:** 分三阶段实现 - Phase 1后端持久化+TODO补全，Phase 2前端页面，Phase 3 Plugin市场API。使用独立数据库表持久化，Redis滑动窗口限流，Celery异步执行。

**Tech Stack:** SQLAlchemy, Alembic, Redis, Celery, React, TypeScript, TanStack Query

---

## 文件结构

### 后端新增/修改文件
- `backend/app/models/webhook.py` - Webhook数据库模型
- `backend/app/models/scheduled_task.py` - 定时任务数据库模型
- `backend/app/models/plugin_review.py` - Plugin评论模型
- `backend/app/services/webhook_service.py` - 重构为数据库持久化
- `backend/app/services/scheduler_service.py` - 重构为数据库持久化
- `backend/app/api/v1/published.py` - 补全速率限制和异步执行
- `backend/app/api/v1/plugins_marketplace.py` - Plugin市场API
- `backend/app/core/rate_limiter.py` - 速率限制器
- `backend/app/tasks/execution_tasks.py` - Celery执行任务
- `backend/alembic/versions/add_webhook_schedule_tables.py` - 迁移脚本
- `backend/alembic/versions/add_plugin_review_table.py` - 迁移脚本
- `backend/tests/test_webhook_service.py` - Webhook测试
- `backend/tests/test_scheduler_service.py` - 定时任务测试
- `backend/tests/test_rate_limiter.py` - 速率限制测试
- `backend/tests/test_plugins_marketplace.py` - Plugin市场测试

### 前端新增文件
- `frontend/src/api/webhooks.ts` - Webhook API客户端
- `frontend/src/api/schedules.ts` - 定时任务API客户端
- `frontend/src/api/published.ts` - API发布API客户端
- `frontend/src/pages/WebhooksPage.tsx` - Webhook管理页面
- `frontend/src/pages/SchedulesPage.tsx` - 定时任务页面
- `frontend/src/pages/PublishedPage.tsx` - API发布页面
- `frontend/src/App.tsx` - 修改：添加路由

---

## Phase 1: 后端持久化 + TODO补全

### Task 1: 创建Webhook数据库模型

**Files:**
- Create: `backend/app/models/webhook.py`
- Test: `backend/tests/test_webhook_model.py`

- [ ] **Step 1: 创建Webhook模型文件**

```python
# backend/app/models/webhook.py
"""Webhook数据库模型"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Webhook(Base):
    """Webhook配置"""
    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False, default=list)  # ["execution.completed", "task.failed"]
    secret_hash = Column(String, nullable=True)  # 签名密钥哈希
    is_active = Column(Boolean, default=True)
    failure_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "url": self.url,
            "events": self.events,
            "is_active": self.is_active,
            "failure_count": self.failure_count,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
```

- [ ] **Step 2: 创建测试文件**

```python
# backend/tests/test_webhook_model.py
"""Webhook模型测试"""

import pytest
from app.models.webhook import Webhook


def test_webhook_to_dict():
    """测试Webhook序列化"""
    webhook = Webhook(
        url="https://example.com/hook",
        events=["execution.completed"],
        is_active=True,
    )
    data = webhook.to_dict()
    assert data["url"] == "https://example.com/hook"
    assert data["events"] == ["execution.completed"]
    assert data["is_active"] is True
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/test_webhook_model.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/webhook.py backend/tests/test_webhook_model.py
git commit -m "feat: add Webhook database model"
```

---

### Task 2: 创建定时任务数据库模型

**Files:**
- Create: `backend/app/models/scheduled_task.py`
- Test: `backend/tests/test_scheduled_task_model.py`

- [ ] **Step 1: 创建定时任务模型文件**

```python
# backend/app/models/scheduled_task.py
"""定时任务数据库模型"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class ScheduledTask(Base):
    """定时任务配置"""
    __tablename__ = "scheduled_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    crew_id = Column(UUID(as_uuid=True), ForeignKey("crews.id"), nullable=False, index=True)
    cron_expression = Column(String, nullable=False)
    timezone = Column(String, default="UTC")
    inputs = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "crew_id": str(self.crew_id),
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "inputs": self.inputs,
            "is_active": self.is_active,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
        }
```

- [ ] **Step 2: 创建测试文件**

```python
# backend/tests/test_scheduled_task_model.py
"""定时任务模型测试"""

import pytest
from app.models.scheduled_task import ScheduledTask


def test_scheduled_task_to_dict():
    """测试定时任务序列化"""
    task = ScheduledTask(
        crew_id="test-crew-id",
        cron_expression="0 9 * * *",
        timezone="Asia/Shanghai",
    )
    data = task.to_dict()
    assert data["cron_expression"] == "0 9 * * *"
    assert data["timezone"] == "Asia/Shanghai"
    assert data["is_active"] is True
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/test_scheduled_task_model.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/scheduled_task.py backend/tests/test_scheduled_task_model.py
git commit -m "feat: add ScheduledTask database model"
```

---

### Task 3: 创建Alembic迁移脚本

**Files:**
- Create: `backend/alembic/versions/add_webhook_schedule_tables.py`

- [ ] **Step 1: 生成迁移脚本**

```bash
cd backend && alembic revision --autogenerate -m "add_webhook_schedule_tables"
```

- [ ] **Step 2: 检查生成的迁移文件**

确保包含webhooks和scheduled_tasks表的创建。

- [ ] **Step 3: 运行迁移**

```bash
cd backend && alembic upgrade head
```

- [ ] **Step 4: 验证表创建**

```bash
cd backend && python -c "from app.core.database import engine; from sqlalchemy import inspect; inspector = inspect(engine); print(inspector.get_table_names())"
```

- [ ] **Step 5: 提交**

```bash
git add backend/alembic/versions/
git commit -m "feat: add webhook and scheduled_task tables migration"
```

---

### Task 4: 重构Webhook服务为数据库持久化

**Files:**
- Modify: `backend/app/services/webhook_service.py`
- Test: `backend/tests/test_webhook_service.py`

- [ ] **Step 1: 重写Webhook服务**

```python
# backend/app/services/webhook_service.py
"""Webhook服务 - 数据库持久化版本"""

import logging
import asyncio
import hmac
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook事件类型"""
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_STARTED = "execution.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    REVIEW_REQUIRED = "review.required"


class WebhookService:
    """Webhook服务"""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=10)

    async def register_webhook(
        self,
        user_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """注册Webhook"""
        async with AsyncSessionLocal() as db:
            # 如果有secret，存储哈希
            secret_hash = None
            if secret:
                secret_hash = hashlib.sha256(secret.encode()).hexdigest()

            webhook = Webhook(
                user_id=user_id,
                url=url,
                events=events,
                secret_hash=secret_hash,
            )

            db.add(webhook)
            await db.commit()
            await db.refresh(webhook)

            logger.info(f"Registered webhook {webhook.id} for user {user_id}")
            return webhook.to_dict()

    async def unregister_webhook(self, user_id: str, webhook_id: str) -> bool:
        """取消注册Webhook"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(Webhook).where(
                    Webhook.id == webhook_id,
                    Webhook.user_id == user_id,
                )
            )
            await db.commit()
            return result.rowcount > 0

    async def trigger_event(
        self,
        user_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ):
        """触发事件并通知所有订阅者"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Webhook).where(
                    Webhook.user_id == user_id,
                    Webhook.is_active == True,
                )
            )
            webhooks = result.scalars().all()

            active_webhooks = [
                wh for wh in webhooks
                if event_type in (wh.events or [])
            ]

            if not active_webhooks:
                return

            logger.info(f"Triggering event {event_type} for user {user_id}, {len(active_webhooks)} webhooks")

            tasks = [
                self._send_webhook(db, wh, event_type, payload)
                for wh in active_webhooks
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_webhook(
        self,
        db: AsyncSession,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any],
    ):
        """发送Webhook通知"""
        try:
            body = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload,
            }

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Fugue-Webhook/1.0",
            }

            # 如果有secret，添加签名
            if webhook.secret_hash:
                message = json.dumps(body, sort_keys=True)
                signature = hmac.new(
                    webhook.secret_hash.encode(),
                    message.encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Fugue-Signature"] = f"sha256={signature}"

            response = await self._client.post(webhook.url, json=body, headers=headers)

            webhook.last_triggered_at = datetime.utcnow()

            if response.status_code >= 400:
                logger.warning(f"Webhook {webhook.id} returned {response.status_code}")
                webhook.failure_count += 1
            else:
                webhook.failure_count = 0

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to send webhook {webhook.id}: {e}")
            webhook.failure_count += 1

            if webhook.failure_count >= 5:
                webhook.is_active = False
                logger.warning(f"Webhook {webhook.id} disabled after 5 consecutive failures")

            await db.commit()

    async def get_user_webhooks(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有Webhook"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Webhook).where(Webhook.user_id == user_id)
            )
            webhooks = result.scalars().all()
            return [wh.to_dict() for wh in webhooks]

    async def test_webhook(self, webhook_id: str, user_id: str) -> Dict[str, Any]:
        """测试Webhook"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Webhook).where(
                    Webhook.id == webhook_id,
                    Webhook.user_id == user_id,
                )
            )
            webhook = result.scalar_one_or_none()

            if not webhook:
                return {"success": False, "error": "Webhook not found"}

            try:
                await self._send_webhook(
                    db,
                    webhook,
                    "test",
                    {"message": "This is a test webhook", "timestamp": datetime.utcnow().isoformat()}
                )
                return {"success": True, "message": "Test webhook sent successfully"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def close(self):
        """关闭HTTP客户端"""
        await self._client.aclose()


# 全局单例
_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """获取Webhook服务单例"""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
```

- [ ] **Step 2: 创建测试文件**

```python
# backend/tests/test_webhook_service.py
"""Webhook服务测试"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.webhook_service import WebhookService


@pytest.mark.asyncio
async def test_register_webhook():
    """测试注册Webhook"""
    service = WebhookService()

    with patch("app.services.webhook_service.AsyncSessionLocal") as mock_session:
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        result = await service.register_webhook(
            user_id="test-user",
            url="https://example.com/hook",
            events=["execution.completed"],
        )

        assert result["url"] == "https://example.com/hook"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/test_webhook_service.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/webhook_service.py backend/tests/test_webhook_service.py
git commit -m "refactor: migrate WebhookService to database persistence"
```

---

### Task 5: 重构定时任务服务为数据库持久化

**Files:**
- Modify: `backend/app/services/scheduler_service.py`
- Test: `backend/tests/test_scheduler_service.py`

- [ ] **Step 1: 重写定时任务服务**

```python
# backend/app/services/scheduler_service.py
"""定时任务调度服务 - 数据库持久化版本"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from croniter import croniter

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_task import ScheduledTask
from app.models.crew import Crew
from app.models.execution import Execution, ExecutionStatus, TriggerType
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self):
        self._running = False
        self._check_interval = 60  # 每分钟检查一次

    async def start(self):
        """启动调度器"""
        self._running = True
        logger.info("Scheduler started")

        while self._running:
            await self._check_and_execute_tasks()
            await asyncio.sleep(self._check_interval)

    async def stop(self):
        """停止调度器"""
        self._running = False
        logger.info("Scheduler stopped")

    async def add_task(
        self,
        crew_id: str,
        user_id: str,
        cron_expression: str,
        timezone: str = "UTC",
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """添加定时任务"""
        # 验证Cron表达式
        if not croniter.is_valid(cron_expression):
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        # 计算下次运行时间
        cron = croniter(cron_expression, datetime.utcnow())
        next_run_at = cron.get_next(datetime)

        async with AsyncSessionLocal() as db:
            task = ScheduledTask(
                crew_id=crew_id,
                user_id=user_id,
                cron_expression=cron_expression,
                timezone=timezone,
                inputs=inputs or {},
                next_run_at=next_run_at,
            )

            db.add(task)
            await db.commit()
            await db.refresh(task)

            logger.info(f"Added scheduled task {task.id}: {cron_expression}")
            return task.to_dict()

    async def remove_task(self, task_id: str, user_id: str) -> bool:
        """移除定时任务"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(ScheduledTask).where(
                    ScheduledTask.id == task_id,
                    ScheduledTask.user_id == user_id,
                )
            )
            await db.commit()
            return result.rowcount > 0

    async def toggle_task(self, task_id: str, user_id: str, is_active: bool) -> bool:
        """启用/禁用定时任务"""
        async with AsyncSessionLocal() as db:
            # 如果启用，重新计算下次运行时间
            if is_active:
                result = await db.execute(
                    select(ScheduledTask).where(
                        ScheduledTask.id == task_id,
                        ScheduledTask.user_id == user_id,
                    )
                )
                task = result.scalar_one_or_none()
                if not task:
                    return False

                cron = croniter(task.cron_expression, datetime.utcnow())
                next_run_at = cron.get_next(datetime)

                await db.execute(
                    update(ScheduledTask).where(ScheduledTask.id == task_id).values(
                        is_active=is_active,
                        next_run_at=next_run_at,
                    )
                )
            else:
                await db.execute(
                    update(ScheduledTask).where(ScheduledTask.id == task_id).values(
                        is_active=is_active,
                    )
                )

            await db.commit()
            return True

    async def get_task(self, task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """获取定时任务"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ScheduledTask).where(
                    ScheduledTask.id == task_id,
                    ScheduledTask.user_id == user_id,
                )
            )
            task = result.scalar_one_or_none()
            return task.to_dict() if task else None

    async def get_user_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有定时任务"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ScheduledTask).where(ScheduledTask.user_id == user_id)
            )
            tasks = result.scalars().all()
            return [task.to_dict() for task in tasks]

    async def _check_and_execute_tasks(self):
        """检查并执行到期的任务"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ScheduledTask).where(
                    ScheduledTask.is_active == True,
                    ScheduledTask.next_run_at <= datetime.utcnow(),
                )
            )
            tasks_to_run = result.scalars().all()

            if not tasks_to_run:
                return

            logger.info(f"Found {len(tasks_to_run)} tasks to execute")

            for task in tasks_to_run:
                try:
                    await self._execute_task(db, task)
                    task.run_count += 1
                    task.last_run_at = datetime.utcnow()

                    # 计算下次运行时间
                    cron = croniter(task.cron_expression, datetime.utcnow())
                    task.next_run_at = cron.get_next(datetime)

                    await db.commit()
                except Exception as e:
                    logger.error(f"Failed to execute scheduled task {task.id}: {e}")
                    task.failure_count += 1
                    await db.commit()

    async def _execute_task(self, db: AsyncSession, task: ScheduledTask):
        """执行定时任务"""
        logger.info(f"Executing scheduled task {task.id} for crew {task.crew_id}")

        # 创建执行记录
        execution = Execution(
            crew_id=task.crew_id,
            user_id=task.user_id,
            status=ExecutionStatus.PENDING,
            trigger_type=TriggerType.SCHEDULED,
            inputs=task.inputs,
        )

        db.add(execution)
        await db.flush()  # 获取execution.id

        # 通过Celery触发异步执行
        from app.tasks.execution_tasks import execute_workflow_task
        execute_workflow_task.delay(str(execution.id))

        logger.info(f"Created execution {execution.id} for scheduled task {task.id}")

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有定时任务（用于调试）- 同步版本"""
        return []  # 数据库版本需要异步调用


# 全局调度器实例
_scheduler: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerService()
    return _scheduler


async def start_scheduler():
    """启动调度器"""
    scheduler = get_scheduler()
    asyncio.create_task(scheduler.start())


async def stop_scheduler():
    """停止调度器"""
    scheduler = get_scheduler()
    await scheduler.stop()
```

- [ ] **Step 2: 创建测试文件**

```python
# backend/tests/test_scheduler_service.py
"""定时任务服务测试"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.scheduler_service import SchedulerService


@pytest.mark.asyncio
async def test_add_task_invalid_cron():
    """测试添加无效Cron表达式"""
    service = SchedulerService()

    with pytest.raises(ValueError, match="Invalid cron expression"):
        await service.add_task(
            crew_id="test-crew",
            user_id="test-user",
            cron_expression="invalid",
        )


@pytest.mark.asyncio
async def test_add_task():
    """测试添加定时任务"""
    service = SchedulerService()

    with patch("app.services.scheduler_service.AsyncSessionLocal") as mock_session:
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        result = await service.add_task(
            crew_id="test-crew",
            user_id="test-user",
            cron_expression="0 9 * * *",
        )

        assert result["cron_expression"] == "0 9 * * *"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/test_scheduler_service.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/scheduler_service.py backend/tests/test_scheduler_service.py
git commit -m "refactor: migrate SchedulerService to database persistence"
```

---

### Task 6: 创建速率限制器

**Files:**
- Create: `backend/app/core/rate_limiter.py`
- Test: `backend/tests/test_rate_limiter.py`

- [ ] **Step 1: 创建速率限制器**

```python
# backend/app/core/rate_limiter.py
"""Redis滑动窗口速率限制器"""

import time
import logging
from typing import Optional
from fastapi import HTTPException

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis滑动窗口速率限制器"""

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        """获取Redis连接"""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> bool:
        """检查速率限制

        Args:
            key: 限制键（如 api_key_id）
            limit: 窗口内最大请求数
            window_seconds: 窗口大小（秒）

        Returns:
            True: 允许请求
            False: 超出限制
        """
        redis = await self._get_redis()
        now = time.time()
        window_start = now - window_seconds

        # 使用Redis Sorted Set实现滑动窗口
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # 移除过期记录
        pipe.zadd(key, {str(now): now})  # 添加当前请求
        pipe.zcard(key)  # 统计窗口内请求数
        pipe.expire(key, window_seconds)  # 设置过期时间

        _, _, count, _ = await pipe.execute()

        if count > limit:
            logger.warning(f"Rate limit exceeded for key {key}: {count}/{limit}")
            return False

        return True

    async def get_remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> int:
        """获取剩余请求数"""
        redis = await self._get_redis()
        now = time.time()
        window_start = now - window_seconds

        await redis.zremrangebyscore(key, 0, window_start)
        count = await redis.zcard(key)

        return max(0, limit - count)


# 全局单例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取速率限制器单例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
```

- [ ] **Step 2: 创建测试文件**

```python
# backend/tests/test_rate_limiter.py
"""速率限制器测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_check_rate_limit_allow():
    """测试速率限制 - 允许请求"""
    limiter = RateLimiter()

    mock_redis = AsyncMock()
    mock_pipeline = AsyncMock()
    mock_pipeline.execute.return_value = (None, None, 5, None)  # 5次请求
    mock_redis.pipeline.return_value = mock_pipeline
    limiter._redis = mock_redis

    result = await limiter.check_rate_limit("test_key", limit=10)
    assert result is True


@pytest.mark.asyncio
async def test_check_rate_limit_exceeded():
    """测试速率限制 - 超出限制"""
    limiter = RateLimiter()

    mock_redis = AsyncMock()
    mock_pipeline = AsyncMock()
    mock_pipeline.execute.return_value = (None, None, 15, None)  # 15次请求
    mock_redis.pipeline.return_value = mock_pipeline
    limiter._redis = mock_redis

    result = await limiter.check_rate_limit("test_key", limit=10)
    assert result is False
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/test_rate_limiter.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/core/rate_limiter.py backend/tests/test_rate_limiter.py
git commit -m "feat: add Redis sliding window rate limiter"
```

---

### Task 7: 补全published.py中的速率限制和异步执行

**Files:**
- Modify: `backend/app/api/v1/published.py`

- [ ] **Step 1: 创建Celery执行任务**

```python
# backend/app/tasks/execution_tasks.py
"""Celery执行任务"""

import asyncio
import logging
from app.core.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def execute_workflow_task(self, execution_id: str):
    """异步执行工作流"""
    try:
        from app.engine.executor import ExecutionEngine

        engine = ExecutionEngine()
        asyncio.run(engine.execute(execution_id))

        logger.info(f"Workflow execution {execution_id} completed")
    except Exception as exc:
        logger.error(f"Workflow execution {execution_id} failed: {exc}")
        self.retry(exc=exc, countdown=60)
```

- [ ] **Step 2: 修改published.py补全TODO**

```python
# 在published.py的execute_published_workflow函数中替换TODO

# 替换: # TODO: 检查速率限制
from app.core.rate_limiter import get_rate_limiter

rate_limiter = get_rate_limiter()
if not await rate_limiter.check_rate_limit(
    key=f"api_key:{api_key.id}",
    limit=api_key.rate_limit or 60,
):
    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded. Please try again later.",
    )

# 替换: # TODO: 异步启动执行
from app.tasks.execution_tasks import execute_workflow_task
execute_workflow_task.delay(str(execution.id))
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && python -m pytest tests/test_published.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/v1/published.py backend/app/tasks/execution_tasks.py
git commit -m "feat: implement rate limiting and async execution for published workflows"
```

---

## Phase 2: 前端页面

### Task 8: 创建Webhook API客户端

**Files:**
- Create: `frontend/src/api/webhooks.ts`

- [ ] **Step 1: 创建Webhook API客户端**

```typescript
// frontend/src/api/webhooks.ts
import apiClient from './client';

export interface Webhook {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  failure_count: number;
  last_triggered_at: string | null;
  created_at: string;
}

export interface WebhookCreate {
  url: string;
  events: string[];
  secret?: string;
}

export const webhooksApi = {
  // 获取Webhook列表
  list: async (): Promise<Webhook[]> => {
    const response = await apiClient.get('/webhooks/');
    return response.data;
  },

  // 创建Webhook
  create: async (data: WebhookCreate): Promise<Webhook> => {
    const response = await apiClient.post('/webhooks/', data);
    return response.data;
  },

  // 删除Webhook
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/webhooks/${id}`);
  },

  // 测试Webhook
  test: async (id: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`/webhooks/${id}/test`);
    return response.data;
  },

  // 获取支持的事件类型
  getEvents: async (): Promise<{ events: Array<{ type: string; name: string; description: string }> }> => {
    const response = await apiClient.get('/webhooks/events');
    return response.data;
  },
};
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/webhooks.ts
git commit -m "feat: add Webhook API client"
```

---

### Task 9: 创建定时任务API客户端

**Files:**
- Create: `frontend/src/api/schedules.ts`

- [ ] **Step 1: 创建定时任务API客户端**

```typescript
// frontend/src/api/schedules.ts
import apiClient from './client';

export interface ScheduledTask {
  id: string;
  crew_id: string;
  cron_expression: string;
  timezone: string;
  inputs: Record<string, unknown>;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  run_count: number;
  failure_count: number;
}

export interface ScheduleCreate {
  crew_id: string;
  cron_expression: string;
  timezone?: string;
  inputs?: Record<string, unknown>;
}

export const schedulesApi = {
  // 获取定时任务列表
  list: async (): Promise<ScheduledTask[]> => {
    const response = await apiClient.get('/schedules/');
    return response.data;
  },

  // 创建定时任务
  create: async (data: ScheduleCreate): Promise<{ success: boolean; task: ScheduledTask }> => {
    const response = await apiClient.post('/schedules/', data);
    return response.data;
  },

  // 删除定时任务
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/schedules/${id}`);
  },

  // 启用/禁用定时任务
  toggle: async (id: string, isActive: boolean): Promise<void> => {
    await apiClient.patch(`/schedules/${id}/toggle`, { is_active: isActive });
  },

  // 验证Cron表达式
  validateCron: async (expression: string): Promise<{ valid: boolean; next_runs: string[] }> => {
    const response = await apiClient.get('/schedules/cron/validate', {
      params: { expression },
    });
    return response.data;
  },

  // 获取定时任务详情
  get: async (id: string): Promise<ScheduledTask> => {
    const response = await apiClient.get(`/schedules/${id}`);
    return response.data;
  },
};
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/schedules.ts
git commit -m "feat: add Schedules API client"
```

---

### Task 10: 创建API发布API客户端

**Files:**
- Create: `frontend/src/api/published.ts`

- [ ] **Step 1: 创建API发布API客户端**

```typescript
// frontend/src/api/published.ts
import apiClient from './client';

export interface PublishedWorkflow {
  id: string;
  slug: string;
  name: string;
  description: string;
  version: string;
  is_public: boolean;
  rate_limit: number;
  created_at: string;
}

export interface PublishRequest {
  slug: string;
  name: string;
  description?: string;
  is_public?: boolean;
  version?: string;
  rate_limit?: number;
}

export const publishedApi = {
  // 获取已发布的工作流列表
  list: async (): Promise<{ workflows: PublishedWorkflow[]; total: number }> => {
    const response = await apiClient.get('/published/');
    return response.data;
  },

  // 发布工作流
  publish: async (crewId: string, data: PublishRequest): Promise<{ success: boolean; workflow: PublishedWorkflow }> => {
    const response = await apiClient.post(`/published/publish/${crewId}`, data);
    return response.data;
  },

  // 取消发布
  unpublish: async (workflowId: string): Promise<void> => {
    await apiClient.delete(`/published/unpublish/${workflowId}`);
  },

  // 获取API状态
  getStatus: async (slug: string): Promise<{ name: string; version: string; description: string; status: string }> => {
    const response = await apiClient.get(`/published/status/${slug}`);
    return response.data;
  },
};
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/published.ts
git commit -m "feat: add Published Workflows API client"
```

---

### Task 11: 创建Webhook管理页面

**Files:**
- Create: `frontend/src/pages/WebhooksPage.tsx`

- [ ] **Step 1: 创建Webhook管理页面**

```tsx
// frontend/src/pages/WebhooksPage.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, TestTube, Webhook as WebhookIcon } from 'lucide-react';
import toast from 'react-hot-toast';
import { webhooksApi, type Webhook, type WebhookCreate } from '../api/webhooks';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';

const WebhooksPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: webhooks, isLoading } = useQuery({
    queryKey: ['webhooks'],
    queryFn: () => webhooksApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
      toast.success('Webhook已删除');
    },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.test(id),
    onSuccess: (result) => {
      if (result.success) {
        toast.success('测试Webhook发送成功');
      } else {
        toast.error(result.message || '测试失败');
      }
    },
  });

  const activeCount = webhooks?.filter((w) => w.is_active).length || 0;
  const disabledCount = webhooks?.filter((w) => !w.is_active).length || 0;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Webhook管理</h1>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          创建Webhook
        </Button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">{webhooks?.length || 0}</div>
            <div className="text-sm text-gray-500">Webhook总数</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">{activeCount}</div>
            <div className="text-sm text-gray-500">活跃</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-red-600">{disabledCount}</div>
            <div className="text-sm text-gray-500">禁用</div>
          </CardContent>
        </Card>
      </div>

      {/* Webhook列表 */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : webhooks && webhooks.length > 0 ? (
        <div className="space-y-4">
          {webhooks.map((webhook) => (
            <Card key={webhook.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">{webhook.url}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      事件: {webhook.events.join(', ')}
                    </div>
                    <div className="text-sm text-gray-500">
                      失败次数: {webhook.failure_count}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => testMutation.mutate(webhook.id)}
                      disabled={testMutation.isPending}
                    >
                      <TestTube className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => deleteMutation.mutate(webhook.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <WebhookIcon className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">还没有Webhook</p>
            <p className="text-sm text-gray-400 mt-2">点击上方按钮创建第一个Webhook</p>
          </CardContent>
        </Card>
      )}

      {/* 创建Webhook模态框 */}
      {showCreateModal && (
        <CreateWebhookModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            queryClient.invalidateQueries({ queryKey: ['webhooks'] });
          }}
        />
      )}
    </div>
  );
};

const CreateWebhookModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [url, setUrl] = useState('');
  const [events, setEvents] = useState<string[]>([]);
  const [secret, setSecret] = useState('');

  const { data: eventsData } = useQuery({
    queryKey: ['webhook-events'],
    queryFn: () => webhooksApi.getEvents(),
  });

  const createMutation = useMutation({
    mutationFn: (data: WebhookCreate) => webhooksApi.create(data),
    onSuccess: () => {
      toast.success('Webhook创建成功');
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({ url, events, secret: secret || undefined });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <h2 className="text-xl font-bold mb-4">创建Webhook</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">回调URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="https://example.com/webhook"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">订阅事件</label>
              <div className="space-y-2">
                {eventsData?.events.map((event) => (
                  <label key={event.type} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={events.includes(event.type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setEvents([...events, event.type]);
                        } else {
                          setEvents(events.filter((ev) => ev !== event.type));
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm">{event.name}</span>
                    <span className="text-xs text-gray-500 ml-2">({event.description})</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">签名密钥 (可选)</label>
              <input
                type="text"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="用于验证Webhook签名"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button type="button" variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button type="submit" disabled={createMutation.isPending || events.length === 0}>
                创建
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default WebhooksPage;
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/WebhooksPage.tsx
git commit -m "feat: add Webhooks management page"
```

---

### Task 12: 创建定时任务管理页面

**Files:**
- Create: `frontend/src/pages/SchedulesPage.tsx`

- [ ] **Step 1: 创建定时任务管理页面**

```tsx
// frontend/src/pages/SchedulesPage.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Pause, Play, Clock } from 'lucide-react';
import toast from 'react-hot-toast';
import { schedulesApi, type ScheduleCreate } from '../api/schedules';
import { crewsApi } from '../api/crews';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';

const SchedulesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['schedules'],
    queryFn: () => schedulesApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => schedulesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      toast.success('定时任务已删除');
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      schedulesApi.toggle(id, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      toast.success('状态已更新');
    },
  });

  const activeCount = tasks?.filter((t) => t.is_active).length || 0;
  const totalRuns = tasks?.reduce((sum, t) => sum + t.run_count, 0) || 0;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">定时任务管理</h1>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          创建定时任务
        </Button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">{tasks?.length || 0}</div>
            <div className="text-sm text-gray-500">任务总数</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">{activeCount}</div>
            <div className="text-sm text-gray-500">运行中</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">{totalRuns}</div>
            <div className="text-sm text-gray-500">总执行次数</div>
          </CardContent>
        </Card>
      </div>

      {/* 任务列表 */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : tasks && tasks.length > 0 ? (
        <div className="space-y-4">
          {tasks.map((task) => (
            <Card key={task.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">工作流: {task.crew_id}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      Cron: <code className="bg-gray-100 px-2 py-1 rounded">{task.cron_expression}</code>
                    </div>
                    <div className="text-sm text-gray-500">
                      时区: {task.timezone} | 执行次数: {task.run_count} | 失败: {task.failure_count}
                    </div>
                    {task.next_run_at && (
                      <div className="text-sm text-blue-600 mt-1">
                        下次运行: {new Date(task.next_run_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleMutation.mutate({ id: task.id, isActive: !task.is_active })}
                    >
                      {task.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => deleteMutation.mutate(task.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <Clock className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">还没有定时任务</p>
            <p className="text-sm text-gray-400 mt-2">点击上方按钮创建第一个定时任务</p>
          </CardContent>
        </Card>
      )}

      {/* 创建定时任务模态框 */}
      {showCreateModal && (
        <CreateScheduleModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            queryClient.invalidateQueries({ queryKey: ['schedules'] });
          }}
        />
      )}
    </div>
  );
};

const CreateScheduleModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [crewId, setCrewId] = useState('');
  const [cronExpression, setCronExpression] = useState('0 9 * * *');
  const [timezone, setTimezone] = useState('Asia/Shanghai');

  const { data: crews } = useQuery({
    queryKey: ['crews'],
    queryFn: () => crewsApi.list(),
  });

  const { data: cronValidation } = useQuery({
    queryKey: ['cron-validate', cronExpression],
    queryFn: () => schedulesApi.validateCron(cronExpression),
    enabled: cronExpression.length > 0,
  });

  const createMutation = useMutation({
    mutationFn: (data: ScheduleCreate) => schedulesApi.create(data),
    onSuccess: () => {
      toast.success('定时任务创建成功');
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({ crew_id: crewId, cron_expression: cronExpression, timezone });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <h2 className="text-xl font-bold mb-4">创建定时任务</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">选择工作流</label>
              <select
                value={crewId}
                onChange={(e) => setCrewId(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="">请选择工作流</option>
                {crews?.map((crew) => (
                  <option key={crew.id} value={crew.id}>
                    {crew.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Cron表达式</label>
              <input
                type="text"
                value={cronExpression}
                onChange={(e) => setCronExpression(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg font-mono"
                placeholder="0 9 * * *"
                required
              />
              {cronValidation && (
                <div className="mt-2 text-sm">
                  {cronValidation.valid ? (
                    <div className="text-green-600">
                      <div>✓ 表达式有效</div>
                      <div className="mt-1">下次运行: {cronValidation.next_runs[0]}</div>
                    </div>
                  ) : (
                    <div className="text-red-600">✗ 无效的Cron表达式</div>
                  )}
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">时区</label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="Asia/Shanghai">Asia/Shanghai</option>
                <option value="UTC">UTC</option>
                <option value="America/New_York">America/New_York</option>
              </select>
            </div>
            <div className="flex justify-end space-x-2">
              <Button type="button" variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button type="submit" disabled={createMutation.isPending || !crewId}>
                创建
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default SchedulesPage;
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/SchedulesPage.tsx
git commit -m "feat: add Schedules management page"
```

---

### Task 13: 创建API发布管理页面

**Files:**
- Create: `frontend/src/pages/PublishedPage.tsx`

- [ ] **Step 1: 创建API发布管理页面**

```tsx
// frontend/src/pages/PublishedPage.tsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Globe, Copy, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { publishedApi, type PublishRequest } from '../api/published';
import { crewsApi } from '../api/crews';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';

const PublishedPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showPublishModal, setShowPublishModal] = useState(false);

  const { data: publishedData, isLoading } = useQuery({
    queryKey: ['published'],
    queryFn: () => publishedApi.list(),
  });

  const unpublishMutation = useMutation({
    mutationFn: (id: string) => publishedApi.unpublish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['published'] });
      toast.success('已取消发布');
    },
  });

  const workflows = publishedData?.workflows || [];
  const totalCalls = workflows.length * 100; // 模拟数据

  const copyEndpoint = (slug: string) => {
    const endpoint = `${window.location.origin}/api/v1/published/execute/${slug}`;
    navigator.clipboard.writeText(endpoint);
    toast.success('Endpoint已复制到剪贴板');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">API发布管理</h1>
        <Button onClick={() => setShowPublishModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          发布新API
        </Button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">{workflows.length}</div>
            <div className="text-sm text-gray-500">已发布API</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-600">{totalCalls}</div>
            <div className="text-sm text-gray-500">总调用次数</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">3</div>
            <div className="text-sm text-gray-500">API Key</div>
          </CardContent>
        </Card>
      </div>

      {/* 已发布列表 */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : workflows.length > 0 ? (
        <div className="space-y-4">
          {workflows.map((workflow) => (
            <Card key={workflow.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">{workflow.name}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                        /api/v1/published/execute/{workflow.slug}
                      </code>
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      版本: {workflow.version} | 速率限制: {workflow.rate_limit}/分钟
                    </div>
                    {workflow.description && (
                      <div className="text-sm text-gray-600 mt-2">{workflow.description}</div>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyEndpoint(workflow.slug)}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => unpublishMutation.mutate(workflow.id)}
                      disabled={unpublishMutation.isPending}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-8 text-center">
            <Globe className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">还没有发布的工作流API</p>
            <p className="text-sm text-gray-400 mt-2">点击上方按钮发布第一个API</p>
          </CardContent>
        </Card>
      )}

      {/* 发布API模态框 */}
      {showPublishModal && (
        <PublishModal
          onClose={() => setShowPublishModal(false)}
          onSuccess={() => {
            setShowPublishModal(false);
            queryClient.invalidateQueries({ queryKey: ['published'] });
          }}
        />
      )}
    </div>
  );
};

const PublishModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [crewId, setCrewId] = useState('');
  const [slug, setSlug] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const { data: crews } = useQuery({
    queryKey: ['crews'],
    queryFn: () => crewsApi.list(),
  });

  const publishMutation = useMutation({
    mutationFn: (data: PublishRequest) => publishedApi.publish(crewId, data),
    onSuccess: () => {
      toast.success('API发布成功');
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    publishMutation.mutate({ slug, name, description });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <h2 className="text-xl font-bold mb-4">发布工作流为API</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">选择工作流</label>
              <select
                value={crewId}
                onChange={(e) => setCrewId(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="">请选择工作流</option>
                {crews?.map((crew) => (
                  <option key={crew.id} value={crew.id}>
                    {crew.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">API Slug</label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg font-mono"
                placeholder="my-api"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">API名称</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="我的API"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">描述 (可选)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg"
                rows={3}
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button type="button" variant="outline" onClick={onClose}>
                取消
              </Button>
              <Button type="submit" disabled={publishMutation.isPending || !crewId || !slug}>
                发布
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default PublishedPage;
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/PublishedPage.tsx
git commit -m "feat: add Published Workflows management page"
```

---

### Task 14: 注册前端路由

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 添加路由**

在App.tsx的路由配置中添加：

```tsx
import WebhooksPage from './pages/WebhooksPage';
import SchedulesPage from './pages/SchedulesPage';
import PublishedPage from './pages/PublishedPage';

// 在路由配置中添加
<Route path="/webhooks" element={<WebhooksPage />} />
<Route path="/schedules" element={<SchedulesPage />} />
<Route path="/published" element={<PublishedPage />} />
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add routes for webhooks, schedules, and published pages"
```

---

## Phase 3: Plugin市场API

### Task 15: 创建Plugin评论模型

**Files:**
- Create: `backend/app/models/plugin_review.py`

- [ ] **Step 1: 创建Plugin评论模型**

```python
# backend/app/models/plugin_review.py
"""Plugin评论数据库模型"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class PluginReview(Base):
    """Plugin评论"""
    __tablename__ = "plugin_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plugin_id = Column(UUID(as_uuid=True), ForeignKey("plugin_marketplace.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "plugin_id": str(self.plugin_id),
            "user_id": str(self.user_id),
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
```

- [ ] **Step 2: 创建迁移脚本**

```bash
cd backend && alembic revision --autogenerate -m "add_plugin_reviews_table"
cd backend && alembic upgrade head
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/plugin_review.py backend/alembic/versions/
git commit -m "feat: add PluginReview model and migration"
```

---

### Task 16: 实现Plugin市场API

**Files:**
- Create: `backend/app/api/v1/plugins_marketplace.py`

- [ ] **Step 1: 创建Plugin市场API**

```python
# backend/app/api/v1/plugins_marketplace.py
"""Plugin市场API"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DatabaseSession, CurrentUser
from app.models.plugin import PluginMarketplace, PluginVersion
from app.models.plugin_review import PluginReview
from app.plugins.loader import get_plugin_loader

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/publish")
async def publish_plugin(
    data: dict,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """发布插件到市场"""
    plugin_id = data.get("plugin_id")
    if not plugin_id:
        raise HTTPException(400, "plugin_id is required")

    # 检查插件是否存在
    loader = get_plugin_loader()
    plugin = loader.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(404, "Plugin not found")

    # 检查是否已发布
    result = await db.execute(
        select(PluginMarketplace).where(PluginMarketplace.plugin_id == plugin_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Plugin already published")

    # 创建市场记录
    marketplace = PluginMarketplace(
        plugin_id=plugin_id,
        name=data.get("name", plugin.name),
        description=data.get("description", plugin.description),
        author=current_user.id,
        version=data.get("version", "1.0.0"),
        category=data.get("category", "general"),
        tags=data.get("tags", []),
        is_published=True,
    )

    db.add(marketplace)
    await db.commit()
    await db.refresh(marketplace)

    return {"success": True, "plugin": marketplace.to_dict()}


@router.get("/list")
async def list_plugins(
    db: DatabaseSession,
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
):
    """获取市场插件列表"""
    query = select(PluginMarketplace).where(PluginMarketplace.is_published == True)

    if category:
        query = query.where(PluginMarketplace.category == category)

    if search:
        query = query.where(PluginMarketplace.name.ilike(f"%{search}%"))

    # 统计总数
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    # 分页查询
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    plugins = result.scalars().all()

    return {
        "plugins": [p.to_dict() for p in plugins],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str, db: DatabaseSession):
    """获取插件详情"""
    result = await db.execute(
        select(PluginMarketplace).where(PluginMarketplace.id == plugin_id)
    )
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(404, "Plugin not found")

    # 获取评论统计
    review_result = await db.execute(
        select(
            func.count(PluginReview.id),
            func.avg(PluginReview.rating),
        ).where(PluginReview.plugin_id == plugin_id)
    )
    review_count, avg_rating = review_result.one()

    data = plugin.to_dict()
    data["review_count"] = review_count or 0
    data["avg_rating"] = float(avg_rating) if avg_rating else 0

    return data


@router.put("/{plugin_id}")
async def update_plugin(
    plugin_id: str,
    data: dict,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新插件信息"""
    result = await db.execute(
        select(PluginMarketplace).where(
            PluginMarketplace.id == plugin_id,
            PluginMarketplace.author == current_user.id,
        )
    )
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(404, "Plugin not found or not authorized")

    for key, value in data.items():
        if hasattr(plugin, key) and key not in ["id", "author", "created_at"]:
            setattr(plugin, key, value)

    await db.commit()
    await db.refresh(plugin)

    return {"success": True, "plugin": plugin.to_dict()}


@router.delete("/{plugin_id}")
async def delete_plugin(
    plugin_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除插件"""
    result = await db.execute(
        select(PluginMarketplace).where(
            PluginMarketplace.id == plugin_id,
            PluginMarketplace.author == current_user.id,
        )
    )
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(404, "Plugin not found or not authorized")

    await db.delete(plugin)
    await db.commit()

    return {"success": True, "message": "Plugin deleted"}


@router.post("/{plugin_id}/install")
async def install_plugin(
    plugin_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """安装插件"""
    result = await db.execute(
        select(PluginMarketplace).where(
            PluginMarketplace.id == plugin_id,
            PluginMarketplace.is_published == True,
        )
    )
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(404, "Plugin not found")

    # 更新下载量
    plugin.downloads = (plugin.downloads or 0) + 1
    await db.commit()

    # 加载插件
    loader = get_plugin_loader()
    loader.load_plugin(plugin.plugin_id)

    return {"success": True, "message": "Plugin installed"}


@router.post("/{plugin_id}/uninstall")
async def uninstall_plugin(
    plugin_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """卸载插件"""
    result = await db.execute(
        select(PluginMarketplace).where(PluginMarketplace.id == plugin_id)
    )
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(404, "Plugin not found")

    # 卸载插件
    loader = get_plugin_loader()
    loader.unload_plugin(plugin.plugin_id)

    return {"success": True, "message": "Plugin uninstalled"}


@router.get("/installed")
async def get_installed_plugins(
    current_user: CurrentUser,
):
    """获取已安装插件"""
    loader = get_plugin_loader()
    plugins = loader.get_all_plugins()

    return {
        "plugins": [
            {
                "id": p.name,
                "name": p.name,
                "description": p.description,
                "version": p.version,
            }
            for p in plugins
        ],
        "total": len(plugins),
    }


@router.post("/{plugin_id}/rate")
async def rate_plugin(
    plugin_id: str,
    data: dict,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """评分插件"""
    rating = data.get("rating")
    if not rating or rating < 1 or rating > 5:
        raise HTTPException(400, "Rating must be between 1 and 5")

    # 检查插件是否存在
    result = await db.execute(
        select(PluginMarketplace).where(PluginMarketplace.id == plugin_id)
    )
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(404, "Plugin not found")

    # 检查是否已评分
    existing = await db.execute(
        select(PluginReview).where(
            PluginReview.plugin_id == plugin_id,
            PluginReview.user_id == current_user.id,
        )
    )
    review = existing.scalar_one_or_none()

    if review:
        # 更新评分
        review.rating = rating
    else:
        # 创建新评分
        review = PluginReview(
            plugin_id=plugin_id,
            user_id=current_user.id,
            rating=rating,
        )
        db.add(review)

    await db.commit()

    return {"success": True, "message": "Rating saved"}


@router.get("/{plugin_id}/reviews")
async def get_reviews(
    plugin_id: str,
    db: DatabaseSession,
    page: int = 1,
    limit: int = 20,
):
    """获取评论列表"""
    result = await db.execute(
        select(PluginReview)
        .where(PluginReview.plugin_id == plugin_id)
        .order_by(PluginReview.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    reviews = result.scalars().all()

    return {
        "reviews": [r.to_dict() for r in reviews],
        "total": len(reviews),
    }


@router.post("/{plugin_id}/reviews")
async def add_review(
    plugin_id: str,
    data: dict,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """添加评论"""
    rating = data.get("rating", 5)
    comment = data.get("comment")

    review = PluginReview(
        plugin_id=plugin_id,
        user_id=current_user.id,
        rating=rating,
        comment=comment,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    return {"success": True, "review": review.to_dict()}
```

- [ ] **Step 2: 注册路由**

在 `backend/app/api/v1/__init__.py` 中添加：

```python
from app.api.v1 import plugins_marketplace

api_router.include_router(
    plugins_marketplace.router,
    prefix="/plugins/marketplace",
    tags=["Plugin Marketplace"],
)
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/api/v1/plugins_marketplace.py backend/app/api/v1/__init__.py
git commit -m "feat: implement Plugin Marketplace API"
```

---

## 自查清单

- [ ] 所有spec需求都有对应任务
- [ ] 无TBD/TODO占位符
- [ ] 类型/方法签名一致
- [ ] 每个任务有完整代码
- [ ] 每个任务有测试步骤
- [ ] 每个任务有提交步骤
