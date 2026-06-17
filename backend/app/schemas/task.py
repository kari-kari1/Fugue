"""Task（任务）相关Schema"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Task基础Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    expected_output: str | None = None
    output_type: str = "text"  # text, json, file, code
    output_file: str | None = None
    context_task_ids: list[str | None] = []  # 依赖的任务ID列表
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    human_review_required: bool = False
    validation_rules: list[dict[str, Any]] = []
    position_x: float = 0
    position_y: float = 0
    config: dict[str, Any] | None = None


class TaskCreate(TaskBase):
    """创建Task"""
    crew_id: str
    agent_id: str | None = None


class TaskUpdate(BaseModel):
    """更新Task"""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    expected_output: str | None = None
    output_type: str | None = None
    output_file: str | None = None
    context_task_ids: list[str] | None = None
    agent_id: str | None = None
    max_retries: int | None = Field(None, ge=0, le=10)
    timeout_seconds: int | None = Field(None, ge=10, le=3600)
    human_review_required: bool | None = None
    validation_rules: list[dict[str, Any]] | None = None
    position_x: float | None = None
    position_y: float | None = None
    config: dict[str, Any] | None = None


class TaskResponse(TaskBase):
    """Task响应"""
    id: str
    crew_id: str
    agent_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
