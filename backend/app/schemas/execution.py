"""Execution（执行）相关Schema"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ExecutionCreate(BaseModel):
    """创建执行"""
    crew_id: str
    inputs: dict[str, Any] = {}
    trigger_type: str = "manual"
    llm_api_keys: dict[str, str] = {}  # {"openai": "sk-xxx", "deepseek": "sk-xxx"}
    llm_base_urls: dict[str, str] = {}  # {"openai": "https://...", "deepseek": "https://..."}


class ExecutionResponse(BaseModel):
    """执行响应"""
    id: str
    crew_id: str
    user_id: str
    status: str
    trigger_type: str
    started_at: datetime | None
    completed_at: datetime | None
    total_tokens_used: int
    total_cost_usd: float
    results: dict[str, Any]
    error_log: str | None
    trace: list[dict[str, Any]] = []
    worktree_path: str | None = None
    sandbox_type: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HeadlessExecutionRequest(BaseModel):
    """无头模式执行请求 — 支持 CI/CD 和 API 集成"""
    crew_id: str
    inputs: dict[str, Any] = {}
    llm_api_keys: dict[str, str] = {}
    llm_base_urls: dict[str, str] = {}
    max_turns: int = 10  # 最大工具调用轮次
    output_format: str = "json"  # "json" 或 "stream-json"
    webhook_url: str | None = None  # 完成后的回调 URL


class HeadlessExecutionResponse(BaseModel):
    """无头模式执行响应"""
    execution_id: str
    status: str
    workflow_name: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    results: dict[str, Any] = {}
    error_log: str | None = None
    trace: list[dict[str, Any]] = []

    model_config = {"from_attributes": True}


class TaskExecutionResponse(BaseModel):
    """任务执行响应"""
    id: str
    execution_id: str
    task_id: str
    agent_id: str | None
    task_name: str | None = None
    agent_name: str | None = None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    input_context: dict[str, Any]
    output: str | None
    output_json: dict[str, Any] | None
    tokens_used: int
    cost_usd: float
    retry_count: int
    error_message: str | None
    thoughts: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
