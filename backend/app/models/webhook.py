"""Webhook数据库模型"""

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String

from app.models.base import BaseModel


class Webhook(BaseModel):
    """Webhook配置"""

    __tablename__ = "webhooks"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False, comment="Webhook目标URL")
    events = Column(JSON, nullable=False, default=list, comment="订阅事件列表")
    secret_hash = Column(String(64), nullable=True, comment="签名密钥哈希（SHA256）")
    is_active = Column(Boolean, default=True, comment="是否启用")
    failure_count = Column(Integer, default=0, comment="连续失败次数")
    last_triggered_at = Column(DateTime, nullable=True, comment="最后触发时间")

    def __repr__(self):
        return f"<Webhook {self.url} (active={self.is_active})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "url": self.url,
            "events": self.events,
            "is_active": self.is_active,
            "failure_count": self.failure_count,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
