"""API Key模型"""

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class APIKey(BaseModel):
    """API Key模型"""

    __tablename__ = "api_keys"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, comment="Key名称")
    key_hash = Column(String(64), nullable=False, unique=True, index=True, comment="Key哈希（SHA256）")
    key_prefix = Column(String(10), nullable=False, comment="Key前缀（用于显示）")
    is_active = Column(Boolean, default=True, comment="是否启用")
    permissions = Column(JSON, default=list, comment="权限列表")
    rate_limit = Column(Integer, default=1000, comment="每小时请求限制")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")

    # 关系
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey {self.name} ({self.key_prefix}...)>"
