"""Webhook管理API"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.services.webhook_service import WebhookEventType, get_webhook_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── 请求/响应模型 ───


class WebhookCreate(BaseModel):
    """创建Webhook请求"""
    url: str = Field(..., description="回调URL")
    events: list[str] = Field(..., min_length=1, description="订阅的事件列表")
    secret: str | None = Field(None, description="签名密钥（可选）")


class WebhookResponse(BaseModel):
    """Webhook响应"""
    id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: str
    last_triggered_at: str | None
    failure_count: int


# ─── API端点 ───


@router.get("/", response_model=list[WebhookResponse])
async def list_webhooks(
    current_user: CurrentUser,
):
    """获取当前用户的所有Webhook"""
    service = get_webhook_service()
    webhooks = await service.get_user_webhooks(current_user.id)

    return [
        WebhookResponse(
            id=wh["id"],
            url=wh["url"],
            events=wh["events"],
            is_active=wh["is_active"],
            created_at=wh["created_at"],
            last_triggered_at=wh.get("last_triggered_at"),
            failure_count=wh.get("failure_count", 0),
        )
        for wh in webhooks
    ]


@router.post("/")
async def create_webhook(
    data: WebhookCreate,
    current_user: CurrentUser,
):
    """创建新的Webhook"""
    service = get_webhook_service()

    # 验证事件类型
    valid_events = {e.value for e in WebhookEventType}
    invalid_events = set(data.events) - valid_events
    if invalid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event types: {', '.join(invalid_events)}",
        )

    webhook = await service.register_webhook(
        user_id=current_user.id,
        url=data.url,
        events=data.events,
        secret=data.secret,
    )

    return webhook


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: CurrentUser,
):
    """删除Webhook"""
    service = get_webhook_service()
    success = await service.unregister_webhook(current_user.id, webhook_id)

    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {"success": True, "message": "Webhook deleted"}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: CurrentUser,
):
    """测试Webhook"""
    service = get_webhook_service()
    result = await service.test_webhook(webhook_id, current_user.id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/events")
async def list_webhook_events():
    """列出所有支持的Webhook事件类型"""
    events = [
        {
            "type": "execution.completed",
            "name": "执行完成",
            "description": "工作流执行成功完成时触发",
        },
        {
            "type": "execution.failed",
            "name": "执行失败",
            "description": "工作流执行失败时触发",
        },
        {
            "type": "execution.started",
            "name": "执行开始",
            "description": "工作流开始执行时触发",
        },
        {
            "type": "task.completed",
            "name": "任务完成",
            "description": "单个任务执行完成时触发",
        },
        {
            "type": "task.failed",
            "name": "任务失败",
            "description": "单个任务执行失败时触发",
        },
        {
            "type": "review.required",
            "name": "需要审核",
            "description": "工作流需要人工审核时触发",
        },
    ]

    return {
        "events": events,
        "total": len(events),
    }
