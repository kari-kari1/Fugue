import asyncio
from celery import Task
from app.tasks.celery_app import celery_app
from app.core.database import db_session_manager, get_session_factory_for_celery
from app.engine.executor import ExecutionEngine
from app.models.execution import Execution, ExecutionStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


def run_async(coro):
    """在同步环境中运行异步代码

    在 Celery worker 中创建新的事件循环并运行异步代码。
    """
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        # 清理
        loop.close()
        asyncio.set_event_loop(None)


async def _mark_execution_failed(execution_id: str, error: str):
    """标记执行为失败状态"""
    # 使用 db_session_manager 获取适用于当前事件循环的会话
    async with db_session_manager.get_session() as db:
        result = await db.execute(
            select(Execution).where(Execution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if execution and execution.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            execution.status = ExecutionStatus.FAILED
            execution.error_log = error
            await db.commit()
            logger.info(f"[CELERY] Marked execution {execution_id} as FAILED: {error}")


@celery_app.task(
    bind=True,
    name="execute_workflow",
    queue="execution",
    max_retries=3,
    default_retry_delay=60,
)
def execute_workflow(
    self,
    execution_id: str,
    llm_api_keys: dict = None,
    llm_base_urls: dict = None,
    resume: bool = False,
):
    """Celery任务：执行工作流（支持断点续传）

    Args:
        execution_id: 执行ID
        llm_api_keys: LLM API密钥
        llm_base_urls: LLM基础URL
        resume: 是否从断点恢复
    """
    logger.info(f"[CELERY] Starting execution {execution_id}, resume={resume}")

    try:
        # 在任务函数内创建引擎实例（每次都是新实例）
        engine = ExecutionEngine(
            execution_id=execution_id,
            llm_api_keys=llm_api_keys or {},
            llm_base_urls=llm_base_urls or {},
        )
        run_async(engine.run(resume=resume))
        logger.info(f"[CELERY] Execution {execution_id} completed successfully")
        return {"execution_id": execution_id, "status": "completed"}

    except Exception as exc:
        logger.error(f"[CELERY] Execution {execution_id} failed: {exc}", exc_info=True)
        try:
            # 使用 Celery 内建重试机制
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            # 重试耗尽，标记为失败
            logger.error(f"[CELERY] Max retries exceeded for execution {execution_id}")
            run_async(_mark_execution_failed(execution_id, str(exc)))
            raise


@celery_app.task(name="cancel_execution", queue="execution")
def cancel_execution(execution_id: str):
    """取消执行"""
    logger.info(f"[CELERY] Cancelling execution {execution_id}")

    try:
        engine = ExecutionEngine(
            execution_id=execution_id,
            llm_api_keys={},
            llm_base_urls={},
        )
        run_async(engine.cancel())
        return {"execution_id": execution_id, "status": "cancelled"}
    except Exception as exc:
        logger.error(f"[CELERY] Failed to cancel execution {execution_id}: {exc}", exc_info=True)
        raise
