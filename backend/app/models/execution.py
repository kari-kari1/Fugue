"""Execution（执行实例）模型"""

import enum

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ExecutionStatus(str, enum.Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_REVIEW = "waiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerType(str, enum.Enum):
    """触发类型"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    API = "api"
    WEBHOOK = "webhook"


class Execution(BaseModel):
    """执行实例模型"""

    __tablename__ = "executions"

    crew_id = Column(String(36), ForeignKey("crews.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING)
    trigger_type = Column(SQLEnum(TriggerType), default=TriggerType.MANUAL)

    # 执行时间
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 资源消耗
    total_tokens_used = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    # 执行结果
    results = Column(JSON, default=dict)
    error_log = Column(Text, nullable=True)

    # Celery任务ID（用于取消任务）
    celery_task_id = Column(String(100), nullable=True, comment="Celery任务ID")

    # 存储 LLM 配置（用于迭代优化时复用）
    llm_api_keys = Column(JSON, nullable=True, default=dict)
    llm_base_urls = Column(JSON, nullable=True, default=dict)

    def set_api_keys(self, keys: dict):
        """加密存储 API 密钥"""
        if not keys:
            self.llm_api_keys = {}
            return
        from app.core.encryption import encrypt
        encrypted = {}
        for provider, key in keys.items():
            if key and isinstance(key, str):
                encrypted[provider] = encrypt(key)
            else:
                encrypted[provider] = key
        self.llm_api_keys = encrypted

    def get_api_keys(self) -> dict:
        """解密读取 API 密钥"""
        if not self.llm_api_keys:
            return {}
        from app.core.encryption import decrypt, is_encrypted
        decrypted = {}
        for provider, key in self.llm_api_keys.items():
            if key and isinstance(key, str) and is_encrypted(key):
                try:
                    decrypted[provider] = decrypt(key)
                except Exception:
                    decrypted[provider] = key
            else:
                decrypted[provider] = key
        return decrypted

    # 执行轨迹
    trace = Column(JSON, default=list)

    # Git Worktree 路径（用于隔离执行）
    worktree_path = Column(String(500), nullable=True)
    # 沙箱类型（执行时自动检测）
    sandbox_type = Column(String(20), nullable=True, comment="沙箱类型: none/bwrap/docker/seatbelt")

    # 关系
    crew = relationship("Crew", back_populates="executions")
    user = relationship("User")
    task_executions = relationship("TaskExecution", back_populates="execution", cascade="all, delete-orphan")
    review_requests = relationship("HumanReviewRequest", back_populates="execution", cascade="all, delete-orphan")
    iterations = relationship("Iteration", back_populates="execution", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Execution {self.id} ({self.status})>"


class TaskExecutionStatus(str, enum.Enum):
    """任务执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class TaskExecution(BaseModel):
    """任务执行记录"""

    __tablename__ = "task_executions"

    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True)

    status = Column(SQLEnum(TaskExecutionStatus), default=TaskExecutionStatus.PENDING)

    # 执行时间
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 输入输出
    input_context = Column(JSON, default=dict)
    output = Column(Text, nullable=True)
    output_json = Column(JSON, nullable=True)

    # 资源消耗
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    retry_count = Column(Integer, default=0)

    # 错误信息
    error_message = Column(Text, nullable=True)

    # Agent思维过程
    thoughts = Column(JSON, default=list)
    tool_calls = Column(JSON, default=list)

    # 关系
    execution = relationship("Execution", back_populates="task_executions")
    task = relationship("Task")
    agent = relationship("Agent")

    def __repr__(self):
        return f"<TaskExecution {self.id} ({self.status})>"
