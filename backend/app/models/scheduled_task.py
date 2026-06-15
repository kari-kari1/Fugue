"""定时任务数据库模型"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, ForeignKey

from app.models.base import BaseModel


class ScheduledTask(BaseModel):
    """定时任务配置"""

    __tablename__ = "scheduled_tasks"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crew_id = Column(String(36), ForeignKey("crews.id", ondelete="CASCADE"), nullable=False, index=True)
    cron_expression = Column(String, nullable=False, comment="Cron表达式")
    timezone = Column(String, default="UTC", comment="时区")
    inputs = Column(JSON, default=dict, comment="任务输入参数")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_run_at = Column(DateTime, nullable=True, comment="最后执行时间")
    next_run_at = Column(DateTime, nullable=True, comment="下次执行时间")
    run_count = Column(Integer, default=0, comment="执行次数")
    failure_count = Column(Integer, default=0, comment="连续失败次数")

    def __repr__(self):
        return f"<ScheduledTask {self.cron_expression} (active={self.is_active})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "crew_id": self.crew_id,
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "inputs": self.inputs,
            "is_active": self.is_active,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
