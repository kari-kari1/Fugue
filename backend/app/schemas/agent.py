"""Agent（智能体）相关Schema"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    """Agent基础Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    goal: str = Field(..., min_length=1)
    backstory: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    allow_delegation: bool = False
    max_iterations: int = Field(default=10, ge=1, le=100)
    system_prompt_template: Optional[str] = None
    tools_config: List[str] = []
    agent_experience: Optional[str] = None
    position_x: float = 0
    position_y: float = 0


class AgentCreate(AgentBase):
    """创建Agent"""
    crew_id: str


class AgentUpdate(BaseModel):
    """更新Agent"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, min_length=1, max_length=255)
    goal: Optional[str] = None
    backstory: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    allow_delegation: Optional[bool] = None
    max_iterations: Optional[int] = Field(None, ge=1, le=100)
    system_prompt_template: Optional[str] = None
    tools_config: Optional[List[str]] = None
    agent_experience: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class AgentResponse(AgentBase):
    """Agent响应"""
    id: str
    crew_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
