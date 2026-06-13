"""Crew（工作流）相关Schema"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CrewBase(BaseModel):
    """Crew基础Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    process: str = "sequential"  # sequential, parallel, hierarchical
    approval_mode: str = "semi_auto"  # safe, semi_auto, full_auto
    max_execution_time: int = Field(default=3600, ge=60, le=86400)
    cost_budget: Optional[float] = Field(None, ge=0)
    workspace_dir: Optional[str] = None
    metadata_: Dict[str, Any] = Field(default={}, alias="metadata", serialization_alias="metadata")


class CrewCreate(CrewBase):
    """创建Crew"""
    pass


class CrewUpdate(BaseModel):
    """更新Crew"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    process: Optional[str] = None
    approval_mode: Optional[str] = None  # safe, semi_auto, full_auto
    max_execution_time: Optional[int] = Field(None, ge=60, le=86400)
    cost_budget: Optional[float] = Field(None, ge=0)
    workspace_dir: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CrewResponse(CrewBase):
    """Crew响应"""
    id: str
    user_id: str
    approval_mode: str = "semi_auto"
    project_memory: Optional[str] = None
    is_template: str
    template_category: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


# 延迟导入避免循环依赖
def _get_agent_task_schemas():
    from app.schemas.agent import AgentResponse
    from app.schemas.task import TaskResponse
    return AgentResponse, TaskResponse


class CrewDetailResponse(CrewResponse):
    """Crew详细响应（包含关联数据）"""
    agents: List[Any] = []
    tasks: List[Any] = []

    model_config = {"from_attributes": True, "populate_by_name": True}


# 在模块加载后解析前向引用
AgentResponse, TaskResponse = _get_agent_task_schemas()
CrewDetailResponse.model_rebuild()
