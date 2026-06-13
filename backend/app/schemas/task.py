"""Task（任务）相关Schema"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Task基础Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    expected_output: Optional[str] = None
    output_type: str = "text"  # text, json, file, code
    output_file: Optional[str] = None
    context_task_ids: List[Optional[str]] = []  # 依赖的任务ID列表
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    human_review_required: bool = False
    validation_rules: List[Dict[str, Any]] = []
    position_x: float = 0
    position_y: float = 0
    config: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    """创建Task"""
    crew_id: str
    agent_id: Optional[str] = None


class TaskUpdate(BaseModel):
    """更新Task"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    expected_output: Optional[str] = None
    output_type: Optional[str] = None
    output_file: Optional[str] = None
    context_task_ids: Optional[List[str]] = None
    agent_id: Optional[str] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=10, le=3600)
    human_review_required: Optional[bool] = None
    validation_rules: Optional[List[Dict[str, Any]]] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    config: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    """Task响应"""
    id: str
    crew_id: str
    agent_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
