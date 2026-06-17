# backend/app/tasks/celery_app.py

from celery import Celery

from app.core.config import settings

# 创建Celery应用
celery_app = Celery(
    "fugue",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.execution_tasks"],
)

# Celery配置
celery_app.conf.update(
    # 序列化配置
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区配置
    timezone="UTC",
    enable_utc=True,

    # 任务配置
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # 超时配置（30分钟软超时，1小时硬超时）
    task_soft_time_limit=1800,
    task_time_limit=3600,

    # 结果过期时间（24小时）
    result_expires=86400,

    # 任务路由
    task_routes={
        "app.tasks.execution_tasks.*": {"queue": "execution"},
    },

    # 默认队列
    task_default_queue="default",

    # Redis 传输选项
    broker_transport_options={
        'visibility_timeout': 43200,  # 12小时，略大于 task_time_limit (3600s)
    },
)

# 队列配置
celery_app.conf.task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
    "execution": {
        "exchange": "execution",
        "routing_key": "execution",
    },
}
