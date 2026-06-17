"""审批相关 Schema"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApprovalRequestResponse(BaseModel):
    """审批请求响应"""
    request_id: str
    execution_id: str
    tool_name: str
    tool_args: dict[str, Any]
    risk_level: str
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    reject_reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalAction(BaseModel):
    """审批操作请求"""
    reason: str | None = Field(None, max_length=2000, description="审批/拒绝原因")
    approved_by: str | None = Field(None, max_length=256, description="审批人标识")


class ApprovalModeConfig(BaseModel):
    """审批模式配置"""
    mode: str = Field(
        ...,
        pattern="^(safe|semi_auto|full_auto)$",
        description="审批模式: safe / semi_auto / full_auto",
    )
