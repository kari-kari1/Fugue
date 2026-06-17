"""循环配置模型"""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class LoopConfig(BaseModel):
    """循环配置"""

    __tablename__ = "loop_configs"

    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True)

    # 循环配置
    name = Column(String(100), nullable=False, comment="循环节点名称")
    max_iterations = Column(Integer, default=10, comment="最大迭代次数")
    condition = Column(String(500), comment="继续循环的条件（Python表达式）")
    exit_on_failure = Column(Boolean, default=True, comment="失败时退出循环")

    # 循环体
    loop_body_task_ids = Column(JSON, default=list, comment="循环体内的任务ID列表")

    # 位置信息（画布）
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)

    # 关联
    crew = relationship("Crew", back_populates="loop_configs")

    def __repr__(self):
        return f"<LoopConfig {self.name} max={self.max_iterations}>"
