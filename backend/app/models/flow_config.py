"""事件流配置模型 — 持久化 @start / @listen / @router 节点"""

from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class FlowConfig(BaseModel):
    """事件流节点配置"""

    __tablename__ = "flow_configs"

    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True)

    # 节点类型：start / listen / router_event
    flow_type = Column(String(20), nullable=False, comment="事件流节点类型")
    name = Column(String(100), nullable=False, comment="节点名称")
    event_name = Column(String(200), comment="事件名（@start/@listen 的方法名或事件标识）")
    condition = Column(String(500), comment="路由条件表达式（@router 使用）")
    description = Column(String(500), comment="描述")

    # 关联任务（事件触发后执行的任务 ID 列表）
    linked_task_ids = Column(JSON, default=list, comment="关联的任务ID列表")

    # 位置信息（画布）
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)

    # 额外配置
    config = Column(JSON, default=dict, comment="额外配置参数")

    # 关系
    crew = relationship("Crew", back_populates="flow_configs")

    def __repr__(self):
        return f"<FlowConfig {self.flow_type}:{self.name}>"
