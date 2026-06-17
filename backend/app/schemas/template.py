from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str
    role: str
    goal: str
    backstory: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    tools: list[str] = []


class TaskConfig(BaseModel):
    """Task 配置"""
    name: str
    description: str
    expected_output: str
    output_type: str = "text"
    agent_index: int  # 索引 agents_config 中的 Agent
    depends_on: list[int] = []  # 依赖的 task 索引


class TemplateBase(BaseModel):
    """模板基础字段"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    category: str = Field(..., pattern="^(research|code|analysis|document|literature)$")
    icon: str = "📋"
    difficulty: str = Field("intermediate", pattern="^(beginner|intermediate|advanced)$")
    agents_config: list[AgentConfig]
    tasks_config: list[TaskConfig]
    connections_config: list[Any] | None = []
    process_type: str = Field("sequential", pattern="^(sequential|parallel)$")
    tags: list[str] = []


class TemplateCreate(TemplateBase):
    """创建自定义模板"""
    pass


class TemplateUpdate(BaseModel):
    """更新模板（所有字段可选）"""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    category: str | None = Field(None, pattern="^(research|code|analysis|document|literature)$")
    icon: str | None = None
    difficulty: str | None = Field(None, pattern="^(beginner|intermediate|advanced)$")
    agents_config: list[AgentConfig] | None = None
    tasks_config: list[TaskConfig] | None = None
    connections_config: list[Any] | None = None
    process_type: str | None = Field(None, pattern="^(sequential|parallel)$")
    tags: list[str] | None = None


class TemplateResponse(TemplateBase):
    """模板响应"""
    id: str
    use_count: int
    rating: float
    is_builtin: bool
    user_id: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    items: list[TemplateResponse]
    total: int
    page: int
    limit: int
