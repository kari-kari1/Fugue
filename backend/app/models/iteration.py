"""Iteration（迭代）模型"""

import enum
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, JSON, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship, validates

from app.models.base import BaseModel


class IterationMode(str, enum.Enum):
    """迭代模式"""
    REEXECUTE = "reexecute"
    INCREMENTAL = "incremental"


class IterationStatus(str, enum.Enum):
    """迭代状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Iteration(BaseModel):
    """迭代记录模型

    用于记录任务执行的迭代历史，支持反馈驱动的重新执行。
    """

    __tablename__ = "iterations"

    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    iteration_number = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=False)
    mode = Column(SQLEnum(IterationMode), nullable=False)
    status = Column(SQLEnum(IterationStatus), default=IterationStatus.PENDING)

    # 迭代内容
    original_task_snapshot = Column(JSON)
    previous_output = Column(Text)
    refined_output = Column(Text)
    context_snapshot = Column(JSON, nullable=True, comment="迭代时的完整执行上下文快照")

    # 资源消耗
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    # 错误信息
    error_message = Column(Text, nullable=True)

    # 时间戳
    completed_at = Column(DateTime, nullable=True)

    # 关系
    execution = relationship("Execution", back_populates="iterations")

    def __init__(self, **kwargs):
        """初始化迭代记录"""
        if 'status' not in kwargs:
            kwargs['status'] = IterationStatus.PENDING
        if 'iteration_number' in kwargs and kwargs['iteration_number'] < 1:
            raise ValueError("iteration_number must be >= 1")
        super().__init__(**kwargs)

    @validates('tokens_used', 'cost_usd')
    def validate_non_negative(self, key: str, value: float) -> float:
        """验证tokens_used和cost_usd为非负数"""
        if value is not None and value < 0:
            raise ValueError(f"{key} must be >= 0")
        return value

    def __repr__(self) -> str:
        return f"<Iteration #{self.iteration_number} ({self.status.value if self.status else 'UNKNOWN'})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "execution_id": self.execution_id,
            "iteration_number": self.iteration_number,
            "feedback": self.feedback,
            "mode": self.mode.value if self.mode else None,
            "status": self.status.value if self.status else None,
            "original_task_snapshot": self.original_task_snapshot,
            "previous_output": self.previous_output,
            "refined_output": self.refined_output,
            "context_snapshot": self.context_snapshot,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "error_message": self.error_message,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
