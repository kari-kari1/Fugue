"""Plugin评论数据库模型"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from app.models.base import BaseModel


class PluginReview(BaseModel):
    """Plugin评论"""
    __tablename__ = "plugin_reviews"

    plugin_id = Column(String(36), ForeignKey("plugin_marketplace.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "plugin_id": self.plugin_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
