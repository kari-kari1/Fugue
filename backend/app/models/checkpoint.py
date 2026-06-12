"""执行断点检查点模型"""

from sqlalchemy import Column, String, JSON, ForeignKey, Integer

from app.models.base import BaseModel


class ExecutionCheckpoint(BaseModel):
    """执行断点检查点"""

    __tablename__ = "execution_checkpoints"

    execution_id = Column(
        String(36),
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 断点位置
    checkpoint_type = Column(
        String(20), nullable=False, comment="类型：task_start/task_end/manual/pause"
    )
    task_id = Column(String(36), nullable=True, comment="关联的任务ID")
    task_name = Column(String(200), nullable=True, comment="任务名称（便于阅读）")

    # 状态快照
    completed_task_ids = Column(
        JSON, default=list, comment="已完成的任务ID列表"
    )
    task_outputs = Column(JSON, default=dict, comment="已完成任务的输出")
    context = Column(JSON, default=dict, comment="执行上下文快照")

    # 统计信息（便于恢复时快速恢复累计值）
    total_tokens_so_far = Column(Integer, default=0, comment="截至断点的累计token数")
    total_cost_so_far = Column(Integer, default=0, comment="截至断点的累计费用（万分之一美元）")

    def __repr__(self):
        return (
            f"<ExecutionCheckpoint {self.id} type={self.checkpoint_type} "
            f"execution={self.execution_id}>"
        )


class ExecutionPauseRequest(BaseModel):
    """执行暂停请求（用户请求 -> Worker 异步检查）"""

    __tablename__ = "execution_pause_requests"

    execution_id = Column(
        String(36),
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by = Column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    status = Column(
        String(20),
        default="pending",
        comment="状态：pending/accepted/completed",
    )
