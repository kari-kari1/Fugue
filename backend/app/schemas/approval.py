"""审批相关 Schema"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ApprovalRequestResponse(BaseModel):
    """审批请求响应"""
    request_id: str
    execution_id: str
    tool_name: str
    tool_args: Dict[str, Any]
    risk_level: str
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalAction(BaseModel):
    """审批操作请求"""
    reason: Optional[str] = Field(None, max_length=2000, description="审批/拒绝原因")
    approved_by: Optional[str] = Field(None, max_length=256, description="审批人标识")


class ApprovalModeConfig(BaseModel):
    """审批模式配置"""
    mode: str = Field(
        ...,
        pattern="^(safe|semi_auto|full_auto)$",
        description="审批模式: safe / semi_auto / full_auto",
    )
