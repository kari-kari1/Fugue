"""Iteration（迭代）相关Schema"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class IterationCreate(BaseModel):
    """迭代创建请求"""
    feedback: str = Field(..., min_length=1, max_length=5000)
    mode: str = Field(..., pattern="^(reexecute|incremental)$")


class IterationResponse(BaseModel):
    """迭代响应"""
    id: str
    execution_id: str
    iteration_number: int
    feedback: str
    mode: str
    status: str
    refined_output: Optional[str] = None
    context_snapshot: Optional[dict] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
