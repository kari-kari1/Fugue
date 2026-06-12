"""已发布工作流模型"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PublishedWorkflow(BaseModel):
    """已发布的工作流"""

    __tablename__ = "published_workflows"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True, comment="URL友好标识")
    name = Column(String(200), nullable=False, comment="API名称")
    description = Column(String(500), nullable=True, comment="API描述")
    is_public = Column(Boolean, default=False, comment="是否公开")
    version = Column(String(20), default="1.0.0", comment="API版本")
    rate_limit = Column(Integer, default=100, comment="每小时请求限制")
    call_count = Column(Integer, default=0, comment="调用次数")

    # 关系
    user = relationship("User", back_populates="published_workflows")
    crew = relationship("Crew", back_populates="published_workflows")

    def __repr__(self):
        return f"<PublishedWorkflow {self.slug}>"
