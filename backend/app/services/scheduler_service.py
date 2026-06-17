"""定时任务调度服务 — 数据库持久化版本"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from croniter import croniter
from sqlalchemy import select

from app.core.config import settings
from app.core.database import db_session_manager
from app.models.crew import Crew
from app.models.execution import Execution, ExecutionStatus
from app.models.scheduled_task import ScheduledTask as ScheduledTaskModel

logger = logging.getLogger(__name__)


def _calculate_next_run(cron_expression: str) -> datetime | None:
    """根据Cron表达式计算下次运行时间（UTC）"""
    try:
        cron = croniter(cron_expression, datetime.now(UTC).replace(tzinfo=None))
        return cron.get_next(datetime)
    except Exception as e:
        logger.error(f"Invalid cron expression '{cron_expression}': {e}")
        return None


class SchedulerService:
    """定时任务调度服务（数据库持久化）"""

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
        id: str,
        crew_id: str,
        user_id: str,
        cron_expression: str,
        timezone: str = "UTC",
        inputs: dict[str, Any] | None = None,
    ) -> ScheduledTaskModel:
        """添加定时任务并写入数据库

        Args:
            id: 任务ID
            crew_id: 工作流ID
            user_id: 用户ID
            cron_expression: Cron表达式（5位：分 时 日 月 周）
            timezone: 时区
            inputs: 执行输入

        Returns:
            ScheduledTaskModel数据库实例
        """
        if not croniter.is_valid(cron_expression):
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        next_run = _calculate_next_run(cron_expression)

        task = ScheduledTaskModel(
            id=id,
            crew_id=crew_id,
            user_id=user_id,
            cron_expression=cron_expression,
            timezone=timezone,
            inputs=inputs or {},
            is_active=True,
            next_run_at=next_run,
            run_count=0,
            failure_count=0,
        )

        async with db_session_manager.get_session() as db:
            db.add(task)
            await db.flush()
            await db.refresh(task)

        logger.info(f"Added scheduled task {id}: {cron_expression}")
        return task

    async def remove_task(self, task_id: str) -> bool:
        """从数据库删除定时任务"""
        async with db_session_manager.get_session() as db:
            result = await db.execute(
                select(ScheduledTaskModel).where(ScheduledTaskModel.id == task_id)
            )
            task = result.scalar_one_or_none()
            if task is None:
                return False

            await db.delete(task)

        logger.info(f"Removed scheduled task {task_id}")
        return True

    async def toggle_task(self, task_id: str, is_active: bool) -> bool:
        """启用/禁用定时任务（更新数据库）"""
        async with db_session_manager.get_session() as db:
            result = await db.execute(
                select(ScheduledTaskModel).where(ScheduledTaskModel.id == task_id)
            )
            task = result.scalar_one_or_none()
            if task is None:
                return False

            task.is_active = is_active
            if is_active:
                task.next_run_at = _calculate_next_run(task.cron_expression)
            else:
                task.next_run_at = None

        logger.info(f"Toggled scheduled task {task_id}: is_active={is_active}")
        return True

    async def get_task(self, task_id: str) -> ScheduledTaskModel | None:
        """从数据库查询单个定时任务"""
        async with db_session_manager.get_session() as db:
            result = await db.execute(
                select(ScheduledTaskModel).where(ScheduledTaskModel.id == task_id)
            )
            return result.scalar_one_or_none()

    async def get_user_tasks(self, user_id: str) -> list[ScheduledTaskModel]:
        """从数据库查询用户的所有定时任务"""
        async with db_session_manager.get_session() as db:
            result = await db.execute(
                select(ScheduledTaskModel).where(ScheduledTaskModel.user_id == user_id)
            )
            return list(result.scalars().all())

    async def _check_and_execute_tasks(self):
        """从数据库查询到期任务并执行"""
        now = datetime.now(UTC).replace(tzinfo=None)

        async with db_session_manager.get_session() as db:
            result = await db.execute(
                select(ScheduledTaskModel).where(
                    ScheduledTaskModel.is_active == True,  # noqa: E712
                    ScheduledTaskModel.next_run_at != None,  # noqa: E711
                    ScheduledTaskModel.next_run_at <= now,
                )
            )
            tasks_to_run = list(result.scalars().all())

        if not tasks_to_run:
            return

        logger.info(f"Found {len(tasks_to_run)} tasks to execute")

        for task in tasks_to_run:
            try:
                await self._execute_task(task)
                await self._mark_task_executed(task.id, success=True)
            except Exception as e:
                logger.error(f"Failed to execute scheduled task {task.id}: {e}")
                await self._mark_task_executed(task.id, success=False)

    async def _execute_task(self, task: ScheduledTaskModel):
        """执行定时任务：创建Execution记录并通过Celery触发执行"""
        logger.info(f"Executing scheduled task {task.id} for crew {task.crew_id}")

        async with db_session_manager.get_session() as db:
            # 检查工作流是否存在
            result = await db.execute(
                select(Crew).where(Crew.id == task.crew_id)
            )
            crew = result.scalar_one_or_none()
            if not crew:
                raise ValueError(f"Crew {task.crew_id} not found")

            # 创建执行记录
            execution = Execution(
                crew_id=task.crew_id,
                user_id=task.user_id,
                status=ExecutionStatus.PENDING,
                trigger_type="scheduled",
                inputs=task.inputs or {},
            )
            db.add(execution)
            await db.flush()
            await db.refresh(execution)
            execution_id = str(execution.id)

        # C1+C3: Celery 守卫 — 有 Celery 用 delay，否则直接调用
        if settings.USE_CELERY:
            from app.tasks.execution_tasks import execute_workflow
            execute_workflow.delay(execution_id)
            logger.info(f"Dispatched Celery task for execution {execution_id}")
        else:
            # 直接执行（无 Celery 模式）
            asyncio.create_task(self._run_directly(execution_id))
            logger.info(f"Dispatched direct execution {execution_id} (no Celery)")

    async def _run_directly(self, execution_id: str):
        """无 Celery 模式下直接执行工作流"""
        try:
            from app.engine.executor import ExecutionEngine
            engine = ExecutionEngine(execution_id=execution_id)
            await engine.run()
        except Exception as e:
            logger.error(f"Direct execution {execution_id} failed: {e}")

    async def _mark_task_executed(self, task_id: str, success: bool):
        """更新任务的执行记录：run_count / failure_count / next_run_at"""
        async with db_session_manager.get_session() as db:
            result = await db.execute(
                select(ScheduledTaskModel).where(ScheduledTaskModel.id == task_id)
            )
            task = result.scalar_one_or_none()
            if task is None or not task.is_active:
                return

            now = datetime.now(UTC).replace(tzinfo=None)
            task.last_run_at = now
            task.run_count = (task.run_count or 0) + 1

            if not success:
                task.failure_count = (task.failure_count or 0) + 1
            else:
                task.failure_count = 0

            task.next_run_at = _calculate_next_run(task.cron_expression)

    async def get_all_tasks(self) -> list[dict[str, Any]]:
        """获取所有定时任务（用于调试）"""
        async with db_session_manager.get_session() as db:
            result = await db.execute(select(ScheduledTaskModel))
            tasks = result.scalars().all()
            return [t.to_dict() for t in tasks]


# 全局调度器实例
_scheduler: SchedulerService | None = None


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
