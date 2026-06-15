"""任务（Task）相关API"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DatabaseSession, CurrentUser
from app.models.task import Task
from app.models.crew import Crew
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/crew/{crew_id}", response_model=List[TaskResponse])
async def list_tasks(
    crew_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取工作流下的所有任务"""
    # 验证工作流归属
    result = await db.execute(
        select(Crew).where(Crew.id == crew_id, Crew.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="工作流不存在")

    result = await db.execute(
        select(Task).where(Task.crew_id == crew_id).order_by(Task.created_at)
    )
    tasks = result.scalars().all()

    return tasks


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建任务"""
    # 验证工作流归属
    result = await db.execute(
        select(Crew).where(Crew.id == task_data.crew_id, Crew.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="工作流不存在")

    task_dict = task_data.model_dump()
    logger.error(f"CREATE_TASK: name={task_dict.get('name')} agent_id={repr(task_dict.get('agent_id'))} deps={task_dict.get('context_task_ids')}")
    task = Task(**task_dict)
    db.add(task)
    try:
        await db.flush()
    except Exception as e:
        logger.error(f"CREATE_TASK flush error: {e}")
        raise
    await db.refresh(task)

    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取任务详情"""
    result = await db.execute(
        select(Task)
        .join(Crew, Task.crew_id == Crew.id)
        .where(Task.id == task_id, Crew.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新任务"""
    result = await db.execute(
        select(Task)
        .join(Crew, Task.crew_id == Crew.id)
        .where(Task.id == task_id, Crew.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = task_data.model_dump(exclude_unset=True)
    logger.error(f"UPDATE_TASK: id={task_id[:8]} update_data={update_data}")
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()
    await db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除任务"""
    result = await db.execute(
        select(Task)
        .join(Crew, Task.crew_id == Crew.id)
        .where(Task.id == task_id, Crew.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await db.delete(task)
