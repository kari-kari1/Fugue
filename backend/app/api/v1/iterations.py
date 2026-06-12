"""迭代相关API"""

import asyncio
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from app.api.deps import DatabaseSession, CurrentUser
from app.models.execution import Execution, ExecutionStatus, TaskExecution
from app.models.iteration import Iteration, IterationMode, IterationStatus
from app.schemas.iteration import IterationCreate, IterationResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# 后台任务引用注册表 — 防止 GC 回收
_bg_tasks: set[asyncio.Task] = set()


def _track(task: asyncio.Task):
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)


def _iteration_to_response(iteration: Iteration) -> IterationResponse:
    """手动构造IterationResponse"""
    return IterationResponse(
        id=iteration.id,
        execution_id=iteration.execution_id,
        iteration_number=iteration.iteration_number,
        feedback=iteration.feedback,
        mode=iteration.mode.value if hasattr(iteration.mode, 'value') else iteration.mode,
        status=iteration.status.value if hasattr(iteration.status, 'value') else iteration.status,
        refined_output=iteration.refined_output,
        context_snapshot=iteration.context_snapshot,
        tokens_used=iteration.tokens_used or 0,
        cost_usd=iteration.cost_usd or 0.0,
        error_message=iteration.error_message,
        created_at=iteration.created_at,
        updated_at=iteration.updated_at,
        completed_at=iteration.completed_at,
    )


async def _get_execution_for_user(
    execution_id: str, user_id: str, db: DatabaseSession
) -> Execution:
    """获取并验证execution属于当前用户"""
    result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.user_id == user_id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return execution


async def _build_context_snapshot(execution: Execution, db: DatabaseSession) -> dict:
    """构建完整的执行上下文快照

    查询该 execution 下所有 TaskExecution 记录，聚合其任务输出、
    资源消耗等信息，形成一个完整的上下文快照，供后续迭代使用。
    """
    from app.models.task import Task

    te_result = await db.execute(
        select(TaskExecution)
        .where(TaskExecution.execution_id == execution.id)
        .order_by(TaskExecution.created_at)
    )
    task_executions = te_result.scalars().all()

    # 查询任务基本信息用于名称映射
    task_ids = list({te.task_id for te in task_executions})
    task_map: dict[str, str] = {}
    if task_ids:
        task_result = await db.execute(
            select(Task.id, Task.name).where(Task.id.in_(task_ids))
        )
        task_map = {row[0]: row[1] for row in task_result.all()}

    task_outputs = []
    for te in task_executions:
        task_outputs.append({
            "task_id": te.task_id,
            "task_name": task_map.get(te.task_id, "unknown"),
            "output": (te.output or "")[:5000],
            "tokens_used": te.tokens_used or 0,
            "cost_usd": te.cost_usd or 0.0,
            "status": te.status.value if hasattr(te.status, "value") else str(te.status),
        })

    return {
        "execution_status": execution.status.value if hasattr(execution.status, "value") else str(execution.status),
        "total_tokens": execution.total_tokens_used or 0,
        "total_cost": execution.total_cost_usd or 0.0,
        "results": execution.results or {},
        "task_outputs": task_outputs,
        "snapshot_time": datetime.utcnow().isoformat(),
    }


@router.get(
    "/{execution_id}/iterations",
    response_model=List[IterationResponse],
)
async def list_iterations(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取执行的迭代列表"""
    await _get_execution_for_user(execution_id, current_user.id, db)

    result = await db.execute(
        select(Iteration)
        .where(Iteration.execution_id == execution_id)
        .order_by(Iteration.iteration_number)
    )
    iterations = result.scalars().all()
    return [_iteration_to_response(it) for it in iterations]


@router.post(
    "/{execution_id}/refine",
    response_model=IterationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def refine_execution(
    execution_id: str,
    data: IterationCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建迭代优化"""
    execution = await _get_execution_for_user(execution_id, current_user.id, db)

    # 验证执行状态：只有completed或failed才能迭代
    if execution.status not in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
        raise HTTPException(
            status_code=400,
            detail="只有已完成或失败的执行才能进行迭代优化",
        )

    # 计算下一个迭代编号
    count_result = await db.execute(
        select(func.count(Iteration.id)).where(
            Iteration.execution_id == execution_id
        )
    )
    current_count = count_result.scalar() or 0
    next_iteration_number = current_count + 1

    # 截取上一次输出作为previous_output
    previous_output = None
    if current_count > 0:
        last_result = await db.execute(
            select(Iteration)
            .where(Iteration.execution_id == execution_id)
            .order_by(Iteration.iteration_number.desc())
            .limit(1)
        )
        last_iteration = last_result.scalar_one_or_none()
        if last_iteration:
            previous_output = last_iteration.refined_output

    # 构建完整的执行上下文快照
    context_snapshot = await _build_context_snapshot(execution, db)

    # 创建Iteration记录
    iteration = Iteration(
        execution_id=execution_id,
        iteration_number=next_iteration_number,
        feedback=data.feedback,
        mode=IterationMode(data.mode),
        status=IterationStatus.PENDING,
        previous_output=previous_output,
        context_snapshot=context_snapshot,
    )
    db.add(iteration)
    await db.flush()
    await db.refresh(iteration)

    iter_id = iteration.id

    # 先返回响应，然后在后台执行迭代
    await db.commit()
    resp = _iteration_to_response(iteration)

    # 后台执行迭代优化
    async def _run_iteration_bg():
        from app.engine.executor import ExecutionEngine
        from app.core.database import db_session_manager

        try:
            # 从 execution 获取 LLM 配置
            llm_keys = {}
            llm_urls = {}
            try:
                async with db_session_manager.get_session() as bg_db:
                    bg_exec = await bg_db.get(Execution, execution_id)
                    if not bg_exec:
                        logger.error(f"Iteration {iter_id}: execution {execution_id} not found")
                        return
                    llm_keys = bg_exec.llm_api_keys or {}
                    llm_urls = bg_exec.llm_base_urls or {}
            except Exception as db_err:
                logger.error(f"Iteration {iter_id}: failed to load execution config: {db_err}")
                # 继续用空配置尝试

            engine = ExecutionEngine(
                execution_id=execution_id,
                llm_api_keys=llm_keys,
                llm_base_urls=llm_urls,
            )
            # 总超时保护：10 分钟
            await asyncio.wait_for(
                engine.run_iteration(execution_id, iter_id),
                timeout=600,
            )
            logger.info(f"Iteration {iter_id} completed successfully")

        except asyncio.TimeoutError:
            logger.error(f"Iteration {iter_id} timed out after 600s")
            try:
                async with db_session_manager.get_session() as bg_db:
                    it = await bg_db.get(Iteration, iter_id)
                    if it and it.status in (IterationStatus.PENDING, IterationStatus.RUNNING):
                        it.status = IterationStatus.FAILED
                        it.error_message = "迭代优化超时（10分钟），请简化任务或稍后重试"
                        await bg_db.commit()
            except Exception as mark_err:
                logger.error(f"Failed to mark iteration {iter_id} as FAILED: {mark_err}")
        except Exception as e:
            logger.error(f"Iteration {iter_id} failed: {e}", exc_info=True)
            # 标记迭代为失败
            try:
                async with db_session_manager.get_session() as bg_db:
                    it = await bg_db.get(Iteration, iter_id)
                    if it and it.status in (IterationStatus.PENDING, IterationStatus.RUNNING):
                        it.status = IterationStatus.FAILED
                        it.error_message = str(e)[:500]
                        await bg_db.commit()
            except Exception as mark_err:
                logger.error(f"Failed to mark iteration {iter_id} as FAILED: {mark_err}")

    _track(asyncio.create_task(_run_iteration_bg()))
    logger.info(
        f"Created iteration #{next_iteration_number} for execution {execution_id}, background execution started"
    )

    return resp
