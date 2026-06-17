"""Agent（智能体）相关Schema"""

from datetime import datetime

from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    """Agent基础Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    goal: str = Field(..., min_length=1)
    backstory: str | None = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    allow_delegation: bool = False
    max_iterations: int = Field(default=10, ge=1, le=100)
    system_prompt_template: str | None = None
    tools_config: list[str] = []
    agent_experience: str | None = None
    position_x: float = 0
    position_y: float = 0


class AgentCreate(AgentBase):
    """创建Agent"""
    crew_id: str


class AgentUpdate(BaseModel):
    """更新Agent"""
    name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = Field(None, min_length=1, max_length=255)
    goal: str | None = None
    backstory: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    temperature: float | None = Field(None, ge=0, le=2)
    max_tokens: int | None = Field(None, ge=1, le=128000)
    allow_delegation: bool | None = None
    max_iterations: int | None = Field(None, ge=1, le=100)
    system_prompt_template: str | None = None
    tools_config: list[str] | None = None
    agent_experience: str | None = None
    position_x: float | None = None
    position_y: float | None = None


class AgentResponse(AgentBase):
    """Agent响应"""
    id: str
    crew_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
