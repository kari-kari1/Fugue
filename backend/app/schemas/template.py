from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str
    role: str
    goal: str
    backstory: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    tools: List[str] = []


class TaskConfig(BaseModel):
    """Task 配置"""
    name: str
    description: str
    expected_output: str
    output_type: str = "text"
    agent_index: int  # 索引 agents_config 中的 Agent
    depends_on: List[int] = []  # 依赖的 task 索引


class TemplateBase(BaseModel):
    """模板基础字段"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(research|code|analysis|document|literature)$")
    icon: str = "📋"
    difficulty: str = Field("intermediate", pattern="^(beginner|intermediate|advanced)$")
    agents_config: List[AgentConfig]
    tasks_config: List[TaskConfig]
    connections_config: Optional[List[Any]] = []
    process_type: str = Field("sequential", pattern="^(sequential|parallel)$")
    tags: List[str] = []


class TemplateCreate(TemplateBase):
    """创建自定义模板"""
    pass


class TemplateUpdate(BaseModel):
    """更新模板（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, pattern="^(research|code|analysis|document|literature)$")
    icon: Optional[str] = None
    difficulty: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    agents_config: Optional[List[AgentConfig]] = None
    tasks_config: Optional[List[TaskConfig]] = None
    connections_config: Optional[List[Any]] = None
    process_type: Optional[str] = Field(None, pattern="^(sequential|parallel)$")
    tags: Optional[List[str]] = None


class TemplateResponse(TemplateBase):
    """模板响应"""
    id: str
    use_count: int
    rating: float
    is_builtin: bool
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    items: List[TemplateResponse]
    total: int
    page: int
    limit: int
