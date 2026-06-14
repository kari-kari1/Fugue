"""Crew（工作流团队）模型"""

import enum

from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ProcessType(str, enum.Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    # Anthropic 五种工作流模式
    PROMPT_CHAIN = "prompt_chain"
    ROUTER = "router"
    ORCHESTRATOR = "orchestrator"
    EVALUATOR_OPTIMIZER = "evaluator_optimizer"
    # 事件驱动流程
    EVENT_FLOW = "event_flow"
    # 动态规划流程 — Agent 自主分解目标并逐步执行
    PLAN_EXECUTE = "plan_execute"


class Crew(BaseModel):
    """工作流团队模型"""

    __tablename__ = "crews"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # 执行配置
    process = Column(SQLEnum(ProcessType), default=ProcessType.SEQUENTIAL)
    max_execution_time = Column(Integer, default=3600)  # 最大执行时间（秒）
    cost_budget = Column(Float, nullable=True)  # 成本预算（美元）

    # 工作空间目录 — 限制 agent 文件操作范围
    workspace_dir = Column(String(500), nullable=True)

    # 审批模式: safe, semi_auto, full_auto
    approval_mode = Column(String(20), default="semi_auto")

    # 分层项目记忆
    project_memory = Column(Text, nullable=True, comment="项目级AGENTS.md内容，存储项目约定、技术栈、编码规范等")

    # 元数据
    metadata_ = Column("metadata", JSON, default=dict)
    is_template = Column(String(10), default="false")
    template_category = Column(String(100), nullable=True)

    # 关系 - 明确指定外键以避免歧义
    agents = relationship("Agent", back_populates="crew", cascade="all, delete-orphan")
    # 直接任务关系
    tasks = relationship("Task", back_populates="crew", cascade="all, delete-orphan",
                        foreign_keys="[Task.crew_id]", primaryjoin="Crew.id==Task.crew_id")
    executions = relationship("Execution", back_populates="crew", cascade="all, delete-orphan")
    condition_branches = relationship("ConditionBranch", back_populates="crew", cascade="all, delete-orphan")
    loop_configs = relationship("LoopConfig", back_populates="crew", cascade="all, delete-orphan")
    review_configs = relationship("HumanReviewConfig", back_populates="crew", cascade="all, delete-orphan")
    memory_configs = relationship("MemoryConfig", back_populates="crew", cascade="all, delete-orphan")
    plugins = relationship("PluginConfig", back_populates="crew", cascade="all, delete-orphan")
    flow_configs = relationship("FlowConfig", back_populates="crew", cascade="all, delete-orphan")
    user = relationship("User")

    def __repr__(self):
        return f"<Crew {self.name}>"

    published_workflows = relationship("PublishedWorkflow", back_populates="crew", cascade="all, delete-orphan")
