"""Task（任务）模型"""

import enum

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class OutputType(str, enum.Enum):
    """输出类型"""
    TEXT = "text"
    JSON = "json"
    FILE = "file"
    CODE = "code"


class Task(BaseModel):
    """任务模型"""

    __tablename__ = "tasks"

    crew_id = Column(String(36), ForeignKey("crews.id"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)

    # 输出配置
    output_type = Column(SQLEnum(OutputType), default=OutputType.TEXT)
    output_file = Column(String(500), nullable=True)

    # 依赖关系（DAG）
    context_task_ids = Column(JSON, default=list)  # 依赖的任务ID列表

    # 执行配置
    max_retries = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=300)
    human_review_required = Column(Boolean, default=False)

    # 子工作流（嵌套执行）
    sub_crew_id = Column(String(36), ForeignKey("crews.id", ondelete="SET NULL"), nullable=True, index=True)

    # 验证规则
    validation_rules = Column(JSON, default=list)

    # 位置信息（用于画布渲染）
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)

    # 扩展配置（附件、自定义参数等）
    config = Column(JSON, default=dict, nullable=True)

    # 关系 - 明确指定外键以避免歧义
    crew = relationship("Crew", back_populates="tasks", foreign_keys="[Task.crew_id]",
                       primaryjoin="Crew.id==Task.crew_id")
    agent = relationship("Agent", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.name}>"
