"""Execution（执行）相关Schema"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ExecutionCreate(BaseModel):
    """创建执行"""
    crew_id: str
    inputs: Dict[str, Any] = {}
    trigger_type: str = "manual"
    llm_api_keys: Dict[str, str] = {}  # {"openai": "sk-xxx", "deepseek": "sk-xxx"}
    llm_base_urls: Dict[str, str] = {}  # {"openai": "https://...", "deepseek": "https://..."}


class ExecutionResponse(BaseModel):
    """执行响应"""
    id: str
    crew_id: str
    user_id: str
    status: str
    trigger_type: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_tokens_used: int
    total_cost_usd: float
    results: Dict[str, Any]
    error_log: Optional[str]
    trace: List[Dict[str, Any]] = []
    worktree_path: Optional[str] = None
    sandbox_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HeadlessExecutionRequest(BaseModel):
    """无头模式执行请求 — 支持 CI/CD 和 API 集成"""
    crew_id: str
    inputs: Dict[str, Any] = {}
    llm_api_keys: Dict[str, str] = {}
    llm_base_urls: Dict[str, str] = {}
    max_turns: int = 10  # 最大工具调用轮次
    output_format: str = "json"  # "json" 或 "stream-json"
    webhook_url: Optional[str] = None  # 完成后的回调 URL


class HeadlessExecutionResponse(BaseModel):
    """无头模式执行响应"""
    execution_id: str
    status: str
    workflow_name: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    results: Dict[str, Any] = {}
    error_log: Optional[str] = None
    trace: List[Dict[str, Any]] = []

    model_config = {"from_attributes": True}


class TaskExecutionResponse(BaseModel):
    """任务执行响应"""
    id: str
    execution_id: str
    task_id: str
    agent_id: Optional[str]
    task_name: Optional[str] = None
    agent_name: Optional[str] = None
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    input_context: Dict[str, Any]
    output: Optional[str]
    output_json: Optional[Dict[str, Any]]
    tokens_used: int
    cost_usd: float
    retry_count: int
    error_message: Optional[str]
    thoughts: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
