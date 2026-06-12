"""基础模型类"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String

from app.core.database import Base


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


def utcnow():
    """获取当前UTC时间（不带时区信息，兼容TIMESTAMP WITHOUT TIME ZONE）"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    """时间戳混入类"""

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class BaseModel(Base, TimestampMixin):
    """基础模型类"""

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid)
