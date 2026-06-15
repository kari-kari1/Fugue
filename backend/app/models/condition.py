"""条件分支模型"""

from sqlalchemy import Column, String, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ConditionBranch(BaseModel):
    """条件分支配置"""

    __tablename__ = "condition_branches"

    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True)

    # 条件配置
    name = Column(String(100), nullable=False, comment="条件节点名称")
    expression = Column(String(500), nullable=False, comment="条件表达式（Python语法）")
    description = Column(String(500), comment="条件描述")

    # 分支配置
    true_branch_task_ids = Column(JSON, default=list, comment="条件为真时执行的任务ID列表")
    false_branch_task_ids = Column(JSON, default=list, comment="条件为假时执行的任务ID列表")

    # 位置信息（画布）
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)

    # 关系
    crew = relationship("Crew", back_populates="condition_branches")

    def __repr__(self):
        return f"<ConditionBranch {self.name}>"
