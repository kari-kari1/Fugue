"""工作流发布API — 将工作流发布为REST API"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DatabaseSession, CurrentUser
from app.models.execution import TriggerType
from app.models.api_key import APIKey
from app.models.published_workflow import PublishedWorkflow
from app.api.v1.api_keys import (
    WorkflowPublishRequest,
    WorkflowExecuteRequest,
    get_api_key_from_header,
)
from app.models.crew import Crew
from app.models.execution import Execution, ExecutionStatus
from app.engine.executor import ExecutionEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_published_workflows(
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取当前用户已发布的工作流"""
    result = await db.execute(
        select(PublishedWorkflow)
        .where(PublishedWorkflow.user_id == current_user.id)
        .order_by(PublishedWorkflow.created_at.desc())
    )
    workflows = result.scalars().all()

    return {
        "workflows": [
            {
                "id": str(w.id),
                "slug": w.slug,
                "name": w.name,
                "description": w.description,
                "version": w.version,
                "is_public": w.is_public,
                "rate_limit": w.rate_limit,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in workflows
        ],
        "total": len(workflows),
    }


@router.post("/publish/{crew_id}")
async def publish_workflow(
    crew_id: str,
    data: WorkflowPublishRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """发布工作流为API"""
    # 检查工作流是否存在
    result = await db.execute(
        select(Crew).where(
            Crew.id == crew_id,
            Crew.user_id == current_user.id,
        )
    )
    crew = result.scalar_one_or_none()

    if not crew:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # 检查slug是否已存在
    existing = await db.execute(
        select(PublishedWorkflow).where(PublishedWorkflow.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")

    # 创建发布记录
    published = PublishedWorkflow(
        user_id=current_user.id,
        crew_id=crew_id,
        slug=data.slug,
        name=data.name,
        description=data.description,
        is_public=data.is_public,
        version=data.version,
        rate_limit=data.rate_limit,
    )

    db.add(published)
    await db.commit()
    await db.refresh(published)

    return {
        "success": True,
        "workflow": {
            "id": str(published.id),
            "slug": published.slug,
            "endpoint": f"/api/v1/published/{published.slug}",
            "name": published.name,
        },
    }


@router.delete("/unpublish/{workflow_id}")
async def unpublish_workflow(
    workflow_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """取消发布工作流"""
    result = await db.execute(
        select(PublishedWorkflow).where(
            PublishedWorkflow.id == workflow_id,
            PublishedWorkflow.user_id == current_user.id,
        )
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(status_code=404, detail="Published workflow not found")

    await db.delete(workflow)
    await db.commit()

    return {"success": True, "message": "Workflow unpublished"}


# ─── 公开执行端点 ───


@router.post("/execute/{slug}")
async def execute_published_workflow(
    slug: str,
    request: Request,
    data: WorkflowExecuteRequest,
    db: DatabaseSession,
    authorization: Optional[str] = Header(None),
):
    """执行已发布的工作流

    需要在Authorization header中提供API Key：
    ```
    POST /api/v1/published/execute/{slug}
    Authorization: Bearer af_xxxxxxxxxxxxxxxx
    Content-Type: application/json

    {
        "inputs": {"topic": "AI行业分析"},
        "callback_url": "https://your-app.com/callback"
    }
    ```
    """
    # 验证API Key
    api_key = await get_api_key_from_header(db, authorization)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    # 获取发布的工作流
    result = await db.execute(
        select(PublishedWorkflow).where(
            PublishedWorkflow.slug == slug,
        )
    )
    published = result.scalar_one_or_none()

    if not published:
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # 检查权限
    if not published.is_public and published.user_id != api_key.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 检查API Key权限
    if "execute" not in (api_key.permissions or []):
        raise HTTPException(status_code=403, detail="API Key does not have execute permission")

    # 速率限制检查
    from app.core.rate_limiter import get_rate_limiter
    rate_limiter = get_rate_limiter()
    if not await rate_limiter.check_rate_limit(
        key=f"api_key:{api_key.id}",
        limit=api_key.rate_limit or 60,
    ):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # 创建执行
    execution = Execution(
        crew_id=published.crew_id,
        user_id=api_key.user_id,
        status=ExecutionStatus.PENDING,
        trigger_type=TriggerType.API,
    )

    db.add(execution)

    # 更新API Key使用时间
    from datetime import datetime, timezone
    api_key.last_used_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(execution)

    # C1: 异步启动执行（Celery 守卫）
    if settings.USE_CELERY:
        from app.tasks.execution_tasks import execute_workflow
        execute_workflow.delay(str(execution.id))
    else:
        import asyncio
        from app.engine.executor import ExecutionEngine
        async def _run():
            try:
                engine = ExecutionEngine(execution_id=str(execution.id))
                await engine.run()
            except Exception as e:
                logger.error(f"Direct execution failed: {e}")
        asyncio.create_task(_run())

    return {
        "execution_id": str(execution.id),
        "status": "pending",
        "message": "Workflow execution started",
        "poll_url": f"/api/v1/executions/{execution.id}",
    }


@router.get("/status/{slug}")
async def get_api_status(
    slug: str,
    db: DatabaseSession,
):
    """获取API状态（公开端点）"""
    result = await db.execute(
        select(PublishedWorkflow).where(PublishedWorkflow.slug == slug)
    )
    published = result.scalar_one_or_none()

    if not published:
        raise HTTPException(status_code=404, detail="API not found")

    return {
        "name": published.name,
        "version": published.version,
        "description": published.description,
        "status": "active",
    }
