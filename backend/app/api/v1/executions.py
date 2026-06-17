"""执行相关API"""

import asyncio
import logging
from datetime import UTC

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.core.config import settings
from app.core.database import db_session_manager
from app.models.crew import Crew
from app.models.execution import Execution, ExecutionStatus, TaskExecution, TriggerType
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionResponse,
    HeadlessExecutionRequest,
    HeadlessExecutionResponse,
    TaskExecutionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# E8: 后台任务引用注册表 — 防止 GC 回收未完成的 Task
_background_tasks: set[asyncio.Task] = set()


def _track_task(task: asyncio.Task):
    """E8: 注册后台任务引用"""
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _submit_to_celery(
    execution_id: str,
    llm_api_keys: dict = None,
    llm_base_urls: dict = None,
) -> str:
    """提交任务到Celery队列，传递LLM配置"""
    from app.tasks.execution_tasks import execute_workflow
    task = execute_workflow.delay(
        execution_id=execution_id,
        llm_api_keys=llm_api_keys or {},
        llm_base_urls=llm_base_urls or {},
    )
    return task.id


def _execution_to_response(exec: Execution) -> ExecutionResponse:
    """手动构造ExecutionResponse"""
    return ExecutionResponse(
        id=exec.id,
        crew_id=exec.crew_id,
        user_id=exec.user_id,
        status=exec.status.value if hasattr(exec.status, 'value') else exec.status,
        trigger_type=exec.trigger_type.value if hasattr(exec.trigger_type, 'value') else exec.trigger_type,
        started_at=exec.started_at,
        completed_at=exec.completed_at,
        total_tokens_used=exec.total_tokens_used or 0,
        total_cost_usd=exec.total_cost_usd or 0.0,
        results=exec.results if isinstance(exec.results, dict) else {},
        error_log=exec.error_log,
        trace=exec.trace if isinstance(exec.trace, list) else [],
        worktree_path=getattr(exec, 'worktree_path', None),
        sandbox_type=getattr(exec, 'sandbox_type', None),
        created_at=exec.created_at,
        updated_at=exec.updated_at,
    )


@router.get("/", response_model=list[ExecutionResponse])
async def list_executions(
    db: DatabaseSession,
    current_user: CurrentUser,
    crew_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """获取执行记录列表"""
    query = select(Execution).where(Execution.user_id == current_user.id)
    if crew_id:
        query = query.where(Execution.crew_id == crew_id)
    query = query.offset(skip).limit(limit).order_by(Execution.created_at.desc())
    result = await db.execute(query)
    executions = result.scalars().all()
    return [_execution_to_response(e) for e in executions]


@router.post("/", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def create_execution(
    execution_data: ExecutionCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建执行（启动工作流）"""
    # 验证工作流归属
    result = await db.execute(
        select(Crew).where(Crew.id == execution_data.crew_id, Crew.user_id == current_user.id)
    )
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 检查是否有正在运行的执行（超过10分钟的视为超时，自动标记为FAILED）
    from datetime import datetime, timedelta
    running = await db.execute(
        select(Execution).where(
            Execution.crew_id == execution_data.crew_id,
            Execution.status == ExecutionStatus.RUNNING,
        )
    )
    running_exec = running.scalar_one_or_none()
    if running_exec:
        # 如果运行超过10分钟，视为超时，标记为FAILED后放行
        started = running_exec.started_at or running_exec.created_at
        if started:
            age = datetime.now(UTC) - (started if started.tzinfo else started.replace(tzinfo=UTC))
            if age > timedelta(minutes=10):
                logger.warning(f"Execution {running_exec.id} stuck in RUNNING for {age}, marking as FAILED")
                running_exec.status = ExecutionStatus.FAILED
                running_exec.error_log = "执行超时（超过10分钟），自动标记为失败"
                await db.flush()
                running_exec = None
        if running_exec:
            raise HTTPException(status_code=400, detail="该工作流已有正在运行的执行")

    execution = Execution(
        crew_id=execution_data.crew_id,
        user_id=current_user.id,
        trigger_type=TriggerType(execution_data.trigger_type),
        results=execution_data.inputs,
        llm_base_urls=execution_data.llm_base_urls or {},
    )
    execution.set_api_keys(execution_data.llm_api_keys or {})
    db.add(execution)
    await db.flush()
    await db.refresh(execution)

    exec_id = execution.id

    # 提交到Celery任务队列
    if settings.USE_CELERY:
        try:
            celery_task_id = _submit_to_celery(
                exec_id,
                llm_api_keys=execution_data.llm_api_keys or {},
                llm_base_urls=execution_data.llm_base_urls or {},
            )
            execution.celery_task_id = celery_task_id
            logger.info(f"Submitted execution {exec_id} to Celery (task_id: {celery_task_id})")
        except Exception as e:
            logger.error(f"Failed to submit execution {exec_id} to Celery: {e}")
            raise HTTPException(status_code=500, detail="任务队列提交失败")
    else:
        # 开发环境：使用asyncio直接执行（向后兼容）
        import asyncio
        async def _run_execution_background():
            from app.core.database import db_session_manager
            from app.engine.executor import start_execution
            try:
                await start_execution(exec_id, execution_data.llm_api_keys or {}, execution_data.llm_base_urls or {})
            except Exception as e:
                logger.error(f"Background execution failed: {e}", exc_info=True)
                # 标记 execution 为 FAILED，防止前端永远卡在"正在初始化"
                try:
                    async with db_session_manager.get_session() as bg_db:
                        from sqlalchemy import update as sa_update
                        await bg_db.execute(
                            sa_update(Execution)
                            .where(Execution.id == exec_id)
                            .values(status=ExecutionStatus.FAILED, error_log=f"Background execution error: {str(e)[:500]}")
                        )
                        await bg_db.commit()
                except Exception as mark_err:
                    logger.error(f"Failed to mark execution {exec_id} as FAILED: {mark_err}")

        # 先 commit execution row，再启动后台任务，避免 DB session 冲突
        await db.commit()
        resp = _execution_to_response(execution)

        # E8: 使用 task 注册表防止 GC 回收
        _track_task(asyncio.create_task(_run_execution_background()))
        logger.info(f"Started direct async execution for {exec_id} (Celery disabled)")
        return resp

    await db.commit()
    resp = _execution_to_response(execution)

    return resp


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取执行详情"""
    result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.user_id == current_user.id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    # 安全网：PENDING 超过 2 分钟自动标记 FAILED
    if execution.status == ExecutionStatus.PENDING:
        from datetime import datetime, timedelta
        if execution.created_at and datetime.now(UTC) - execution.created_at.replace(tzinfo=UTC) > timedelta(minutes=2):
            execution.status = ExecutionStatus.FAILED
            execution.error_log = "执行超时：后台任务未能在2分钟内启动"
            execution.completed_at = datetime.now(UTC)
            await db.commit()
            logger.warning(f"Auto-failed execution {execution_id}: stuck in PENDING for >2 minutes")

    return _execution_to_response(execution)


@router.get("/{execution_id}/task-executions", response_model=list[TaskExecutionResponse])
async def list_task_executions(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取执行中各任务的执行记录"""
    # 先验证执行记录归属
    exec_result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.user_id == current_user.id,
        )
    )
    if not exec_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="执行记录不存在")

    from sqlalchemy.orm import selectinload


    result = await db.execute(
        select(TaskExecution)
        .where(TaskExecution.execution_id == execution_id)
        .options(
            selectinload(TaskExecution.task),
            selectinload(TaskExecution.agent),
        )
        .order_by(TaskExecution.created_at)
    )
    task_execs = result.scalars().all()

    # 手动注入 task_name / agent_name 到返回对象
    responses = []
    for te in task_execs:
        resp = TaskExecutionResponse(
            id=te.id,
            execution_id=te.execution_id,
            task_id=te.task_id,
            agent_id=te.agent_id,
            task_name=te.task.name if te.task else None,
            agent_name=te.agent.name if te.agent else None,
            status=te.status.value if hasattr(te.status, 'value') else te.status,
            started_at=te.started_at,
            completed_at=te.completed_at,
            input_context=te.input_context if isinstance(te.input_context, dict) else {},
            output=te.output,
            output_json=te.output_json,
            tokens_used=te.tokens_used or 0,
            cost_usd=te.cost_usd or 0.0,
            retry_count=te.retry_count or 0,
            error_message=te.error_message,
            thoughts=te.thoughts if isinstance(te.thoughts, list) else [],
            tool_calls=te.tool_calls if isinstance(te.tool_calls, list) else [],
            created_at=te.created_at,
            updated_at=te.updated_at,
        )
        responses.append(resp)
    return responses


@router.post("/{execution_id}/cancel")
async def cancel_execution_endpoint(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """取消执行"""
    result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.user_id == current_user.id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="执行无法取消")

    # 取消 Celery 任务（如果有）
    cancelled_by_celery = False
    if execution.celery_task_id and settings.USE_CELERY:
        try:
            from app.tasks.celery_app import celery_app
            celery_app.control.revoke(execution.celery_task_id, terminate=True)
            cancelled_by_celery = True
            logger.info(f"[API] Revoked Celery task {execution.celery_task_id}")
        except Exception as e:
            logger.error(f"[API] Failed to revoke Celery task: {e}")

    # 取消引擎执行
    cancelled_by_engine = False
    try:
        from app.engine.executor import cancel_execution_engine
        result = cancel_execution_engine(execution_id)
        cancelled_by_engine = bool(result)
        if cancelled_by_engine:
            logger.info(f"[API] Cancelled engine execution {execution_id}")
        else:
            logger.warning(f"[API] Engine execution {execution_id} not found in running engines")
    except Exception as e:
        logger.error(f"[API] Failed to cancel engine execution: {e}")

    # 无论引擎是否找到，都将状态标记为 CANCELLED
    # 引擎会在下次检查 _cancelled 标志时停止
    execution.status = ExecutionStatus.CANCELLED
    execution.error_log = None
    if not cancelled_by_celery and not cancelled_by_engine:
        execution.error_log = "取消信号已发送，引擎将在当前任务完成后停止。"
        logger.warning(f"[API] Engine not found in memory for {execution_id}, status set to CANCELLED anyway")

    # 直接更新 RUNNING/PENDING 的 TaskExecution 记录，避免前端显示过期状态
    from datetime import datetime

    from sqlalchemy import update as sa_update

    from app.models.execution import TaskExecution, TaskExecutionStatus
    await db.execute(
        sa_update(TaskExecution)
        .where(
            TaskExecution.execution_id == execution_id,
            TaskExecution.status.in_([TaskExecutionStatus.RUNNING, TaskExecutionStatus.PENDING]),
        )
        .values(
            status=TaskExecutionStatus.FAILED,
            error_message="任务已被用户取消",
            completed_at=datetime.utcnow(),
        )
    )

    await db.commit()

    return {
        "message": "取消请求已处理",
        "celery_revoked": cancelled_by_celery,
        "engine_cancelled": cancelled_by_engine,
    }


@router.post("/{execution_id}/pause")
async def pause_execution(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """暂停执行"""
    from app.models.checkpoint import ExecutionPauseRequest

    result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.user_id == current_user.id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    if execution.status != ExecutionStatus.RUNNING:
        raise HTTPException(status_code=400, detail="只能暂停正在运行的执行")

    # 检查是否已有 pending 状态的暂停请求
    existing = await db.execute(
        select(ExecutionPauseRequest).where(
            ExecutionPauseRequest.execution_id == execution_id,
            ExecutionPauseRequest.status == "pending",
        )
    )
    if existing.scalar_one_or_none():
        return {"message": "暂停请求已存在", "signal_sent": False}

    # 创建暂停请求（Worker 会在下一次循环检查时处理）
    pause_request = ExecutionPauseRequest(
        execution_id=execution_id,
        requested_by=current_user.id,
    )
    db.add(pause_request)

    # 尝试通过内存信号快速暂停（如果引擎在本进程内）
    paused_by_engine = False
    try:
        from app.engine.executor import pause_execution_engine
        paused_by_engine = pause_execution_engine(execution_id)
    except Exception as e:
        logger.warning(f"[API] Failed to signal pause to engine: {e}")

    await db.commit()

    return {
        "message": "暂停请求已发送",
        "signal_sent": paused_by_engine,
    }


@router.post("/{execution_id}/resume")
async def resume_execution(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """从断点恢复执行"""
    # A5: 移除 with_for_update()（SQLite桌面模式不需要行锁）
    result = await db.execute(
        select(Execution)
        .where(
            Execution.id == execution_id,
            Execution.user_id == current_user.id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    if execution.status != ExecutionStatus.PAUSED:
        raise HTTPException(status_code=400, detail="执行未处于暂停状态，无法恢复")

    # 先更新状态为 RUNNING，再提交任务
    execution.status = ExecutionStatus.RUNNING
    await db.commit()

    # 提交恢复任务到 Celery 或直接异步执行
    try:
        if settings.USE_CELERY:
            from app.tasks.execution_tasks import execute_workflow
            task = execute_workflow.delay(
                execution_id=execution_id,
                resume=True,
            )
            execution.celery_task_id = task.id
            await db.commit()
            logger.info(f"[API] Submitted resume execution {execution_id} to Celery (task_id: {task.id})")
        else:
            import asyncio
            async def _run_resume_background():
                from app.engine.executor import start_execution
                try:
                    await start_execution(execution_id, resume=True)
                except Exception as e:
                    logger.error(f"[API] Background resume failed: {e}", exc_info=True)

            _track_task(asyncio.create_task(_run_resume_background()))
            logger.info(f"[API] Started direct async resume for {execution_id}")
    except Exception as e:
        # 任务提交失败，回滚状态
        execution.status = ExecutionStatus.PAUSED
        execution.error_log = f"恢复失败: {str(e)}"
        await db.commit()
        logger.error(f"[API] Failed to submit resume for {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="恢复失败")

    return {"message": "执行已恢复"}


@router.get("/{execution_id}/checkpoints")
async def list_checkpoints(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取执行的断点列表"""
    from app.models.checkpoint import ExecutionCheckpoint

    # 验证执行归属
    exec_result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.user_id == current_user.id,
        )
    )
    if not exec_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="执行记录不存在")

    result = await db.execute(
        select(ExecutionCheckpoint)
        .where(ExecutionCheckpoint.execution_id == execution_id)
        .order_by(ExecutionCheckpoint.created_at.desc())
    )
    checkpoints = result.scalars().all()

    return [
        {
            "id": cp.id,
            "checkpoint_type": cp.checkpoint_type,
            "task_id": cp.task_id,
            "task_name": cp.task_name,
            "completed_task_count": len(cp.completed_task_ids or []),
            "total_tokens_so_far": cp.total_tokens_so_far,
            "created_at": cp.created_at.isoformat() if cp.created_at else None,
        }
        for cp in checkpoints
    ]


@router.get("/stats/summary")
async def get_execution_stats(
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取执行统计摘要"""
    from sqlalchemy import func

    # 总执行次数
    total_result = await db.execute(
        select(func.count(Execution.id))
        .where(Execution.user_id == current_user.id)
    )
    total_executions = total_result.scalar() or 0

    # 成功执行次数
    completed_result = await db.execute(
        select(func.count(Execution.id))
        .where(
            Execution.user_id == current_user.id,
            Execution.status == ExecutionStatus.COMPLETED,
        )
    )
    completed_executions = completed_result.scalar() or 0

    # 总Token消耗
    tokens_result = await db.execute(
        select(func.sum(Execution.total_tokens_used))
        .where(Execution.user_id == current_user.id)
    )
    total_tokens = tokens_result.scalar() or 0

    # 总成本
    cost_result = await db.execute(
        select(func.sum(Execution.total_cost_usd))
        .where(Execution.user_id == current_user.id)
    )
    total_cost = cost_result.scalar() or 0.0

    # 计算成功率
    success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else 0

    return {
        "total_executions": total_executions,
        "completed_executions": completed_executions,
        "success_rate": round(success_rate, 1),
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 4),
    }


# ── 无头模式 API ────────────────────────────────────────────


@router.post("/run", response_model=HeadlessExecutionResponse, status_code=status.HTTP_201_CREATED)
async def run_headless(
    execution_data: HeadlessExecutionRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """无头模式执行工作流 — 同步等待完成并返回结果

    适用于 CI/CD 集成、API 调用等非交互式场景。
    支持 JSON 和 stream-json 两种输出格式。
    """
    from app.engine.executor import start_execution

    # 验证工作流归属
    result = await db.execute(
        select(Crew).where(Crew.id == execution_data.crew_id, Crew.user_id == current_user.id)
    )
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(status_code=404, detail="工作流不存在")

    # 创建执行记录
    execution = Execution(
        crew_id=execution_data.crew_id,
        user_id=current_user.id,
        trigger_type=TriggerType("api"),
        results=execution_data.inputs,
        llm_base_urls=execution_data.llm_base_urls or {},
    )
    execution.set_api_keys(execution_data.llm_api_keys or {})
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    exec_id = execution.id

    # 同步执行
    try:
        await start_execution(
            exec_id,
            execution_data.llm_api_keys or {},
            execution_data.llm_base_urls or {},
            max_turns=execution_data.max_turns,
        )
    except Exception as e:
        logger.error(f"Headless execution {exec_id} failed: {e}", exc_info=True)

    # 刷新执行结果
    await db.refresh(execution)

    response = HeadlessExecutionResponse(
        execution_id=exec_id,
        status=execution.status.value if hasattr(execution.status, 'value') else str(execution.status),
        workflow_name=crew.name,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        total_tokens_used=execution.total_tokens_used or 0,
        total_cost_usd=execution.total_cost_usd or 0.0,
        results=execution.results if isinstance(execution.results, dict) else {},
        error_log=execution.error_log,
        trace=execution.trace if isinstance(execution.trace, list) else [],
    )

    # webhook 回调（异步后台，不阻塞响应）
    if execution_data.webhook_url:
        async def _fire_webhook():
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        execution_data.webhook_url,
                        json=response.model_dump(),
                        timeout=aiohttp.ClientTimeout(total=10),
                    )
            except Exception as wh_err:
                logger.warning(f"Webhook to {execution_data.webhook_url} failed: {wh_err}")
        asyncio.create_task(_fire_webhook())

    # output_format 支持
    if execution_data.output_format == "stream-json":
        import json as _json

        from fastapi.responses import StreamingResponse
        async def ndjson_stream():
            for event in (execution.trace or []):
                yield _json.dumps(event, ensure_ascii=False) + "\n"
            yield _json.dumps(response.model_dump(), ensure_ascii=False) + "\n"
        return StreamingResponse(ndjson_stream(), media_type="application/x-ndjson")

    return response


@router.get("/{execution_id}/stream")
async def stream_execution(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """SSE 流式输出执行进度 — 实时推送执行状态和工具调用"""
    import asyncio as aio

    from fastapi.responses import StreamingResponse

    # 验证执行记录归属
    result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.user_id == current_user.id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    async def event_stream():
        last_trace_len = 0
        timeout_seconds = 1800  # 30分钟总超时
        start_time = aio.get_event_loop().time()

        while True:
            elapsed = aio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                yield f"data: {json.dumps({'type': 'timeout', 'message': '执行流超时（30分钟）'})}\n\n"
                break

            async with db_session_manager.get_session() as stream_db:
                exec_ref = await stream_db.get(Execution, execution_id)
                if not exec_ref:
                    break

                # 推送新的事件
                current_trace = exec_ref.trace or []
                if len(current_trace) > last_trace_len:
                    for event in current_trace[last_trace_len:]:
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    last_trace_len = len(current_trace)

                # 推送当前状态
                status_val = exec_ref.status.value if hasattr(exec_ref.status, 'value') else str(exec_ref.status)
                yield f"event: status\ndata: {json.dumps({'status': status_val, 'tokens': exec_ref.total_tokens_used or 0, 'cost': exec_ref.total_cost_usd or 0.0})}\n\n"

                # 终止条件
                if status_val in ("completed", "failed", "cancelled"):
                    yield f"event: done\ndata: {json.dumps({'status': status_val, 'results': exec_ref.results or {}, 'error': exec_ref.error_log})}\n\n"
                    break

            await aio.sleep(1)  # 1秒轮询间隔

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
