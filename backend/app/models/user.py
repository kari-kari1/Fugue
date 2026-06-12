"""用户模型"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """用户模型"""

    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    avatar_url = Column(String(500), nullable=True)

    # 关系
    plugins = relationship("PluginConfig", back_populates="user", cascade="all, delete-orphan")
    published_plugins = relationship("PluginMarketplace", back_populates="publisher")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    published_workflows = relationship("PublishedWorkflow", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"
