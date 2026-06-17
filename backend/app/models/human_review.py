"""Human-in-the-loop 人工审核模型"""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class HumanReviewConfig(BaseModel):
    """人工审核配置（Crew级别）"""

    __tablename__ = "human_review_configs"

    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False, comment="审核节点名称")
    review_type = Column(String(20), nullable=False, comment="类型：approval/input/selection")
    prompt = Column(Text, nullable=False, comment="审核提示")
    options = Column(JSON, nullable=True, comment="选项（selection类型）")
    timeout_seconds = Column(Integer, nullable=True, comment="超时时间（秒）")
    timeout_action = Column(String(20), default="reject", comment="超时动作：approve/reject/skip")
    notification_channels = Column(JSON, default=list, comment="通知渠道")

    # 位置信息（前端画布坐标）
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)

    # 关联
    crew = relationship("Crew", back_populates="review_configs")

    def __repr__(self):
        return f"<HumanReviewConfig {self.name} ({self.review_type})>"


class HumanReviewRequest(BaseModel):
    """人工审核请求（运行时生成）"""

    __tablename__ = "human_review_requests"

    execution_id = Column(String(36), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(36), nullable=False, comment="关联的任务/节点ID")

    # 审核配置
    review_type = Column(String(20), nullable=False, comment="类型：approval/input/selection")
    prompt = Column(Text, nullable=False, comment="展示给用户的提示")
    options = Column(JSON, nullable=True, comment="选项（selection类型）")

    # 审核结果
    status = Column(String(20), default="pending", comment="状态：pending/approved/rejected/skipped")
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    review_result = Column(JSON, nullable=True, comment="审核结果")
    review_comment = Column(Text, nullable=True, comment="审核备注")

    # 时间
    reviewed_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=True)
    timeout_action = Column(String(20), default="reject", comment="超时动作：approve/reject/skip")

    # 关联
    execution = relationship("Execution", back_populates="review_requests")

    def __repr__(self):
        return f"<HumanReviewRequest {self.id} ({self.status})>"
