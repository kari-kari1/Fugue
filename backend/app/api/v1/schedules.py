"""定时任务管理API"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.services.scheduler_service import get_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── 请求/响应模型 ───


class ScheduleCreate(BaseModel):
    """创建定时任务请求"""
    crew_id: str = Field(..., description="工作流ID")
    cron_expression: str = Field(..., description="Cron表达式（5位：分 时 日 月 周）")
    timezone: str = Field(default="UTC", description="时区")
    inputs: dict[str, Any] = Field(default_factory=dict, description="执行输入")


class ScheduleResponse(BaseModel):
    """定时任务响应"""
    id: str
    crew_id: str
    cron_expression: str
    timezone: str
    inputs: dict[str, Any]
    is_active: bool
    last_run_at: str | None
    next_run_at: str | None
    run_count: int
    failure_count: int


# ─── API端点 ───


@router.get("/", response_model=list[ScheduleResponse])
async def list_schedules(
    current_user: CurrentUser,
):
    """获取当前用户的所有定时任务"""
    scheduler = get_scheduler()
    tasks = await scheduler.get_user_tasks(current_user.id)

    return [
        ScheduleResponse(
            id=task.id,
            crew_id=task.crew_id,
            cron_expression=task.cron_expression,
            timezone=task.timezone,
            inputs=task.inputs,
            is_active=task.is_active,
            last_run_at=task.last_run_at.isoformat() if task.last_run_at else None,
            next_run_at=task.next_run_at.isoformat() if task.next_run_at else None,
            run_count=task.run_count,
            failure_count=task.failure_count,
        )
        for task in tasks
    ]


@router.post("/")
async def create_schedule(
    data: ScheduleCreate,
    current_user: CurrentUser,
):
    """创建新的定时任务"""
    scheduler = get_scheduler()

    # 生成任务ID
    import uuid
    task_id = f"schedule_{uuid.uuid4().hex[:12]}"

    try:
        task = await scheduler.add_task(
            id=task_id,
            crew_id=data.crew_id,
            user_id=current_user.id,
            cron_expression=data.cron_expression,
            timezone=data.timezone,
            inputs=data.inputs,
        )

        return {
            "success": True,
            "task": task.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cron/validate")
async def validate_cron_expression(
    expression: str,
):
    """验证Cron表达式"""
    from croniter import croniter

    if not croniter.is_valid(expression):
        raise HTTPException(status_code=400, detail="Invalid cron expression")

    # 计算接下来5次运行时间
    cron = croniter(expression)
    next_runs = []
    for _ in range(5):
        next_runs.append(cron.get_next(datetime).isoformat())

    return {
        "valid": True,
        "expression": expression,
        "next_runs": next_runs,
    }


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: CurrentUser,
):
    """删除定时任务"""
    scheduler = get_scheduler()
    task = await scheduler.get_task(schedule_id)

    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await scheduler.remove_task(schedule_id)

    return {"success": True, "message": "Schedule deleted"}


@router.patch("/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: str,
    current_user: CurrentUser,
):
    """启用/禁用定时任务"""
    scheduler = get_scheduler()
    task = await scheduler.get_task(schedule_id)

    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")

    new_status = not task.is_active
    await scheduler.toggle_task(schedule_id, new_status)

    return {
        "success": True,
        "is_active": new_status,
    }


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    current_user: CurrentUser,
):
    """获取定时任务详情"""
    scheduler = get_scheduler()
    task = await scheduler.get_task(schedule_id)

    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return ScheduleResponse(
        id=task.id,
        crew_id=task.crew_id,
        cron_expression=task.cron_expression,
        timezone=task.timezone,
        inputs=task.inputs,
        is_active=task.is_active,
        last_run_at=task.last_run_at.isoformat() if task.last_run_at else None,
        next_run_at=task.next_run_at.isoformat() if task.next_run_at else None,
        run_count=task.run_count,
        failure_count=task.failure_count,
    )
