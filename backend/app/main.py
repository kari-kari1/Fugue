"""Fugue - FastAPI主应用"""

import logging
import logging.handlers
import os
import signal
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

# G3: 配置日志持久化（RotatingFileHandler）
class _SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Windows 安全日志旋转：捕获 PermissionError 防止多进程冲突"""

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        try:
            super().doRollover()
        except PermissionError:
            # 另一个进程持有文件，跳过旋转，重新打开当前文件
            self.stream = self._open()


def _setup_logging():
    """配置日志 — 同时输出到 stderr 和文件"""
    log_dir = Path(os.environ.get("APPDATA", Path.home())) / "Fugue" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "fugue.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 文件 handler — 5MB × 3 个备份，delay=True 延迟打开避免无写时占用
    file_handler = _SafeRotatingFileHandler(
        str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8", delay=True
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root_logger.addHandler(file_handler)

    # stderr handler
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root_logger.addHandler(stderr_handler)

    return logging.getLogger(__name__)

logger = _setup_logging()
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import init_db, close_db, AsyncSessionLocal
from app.models.execution import Execution, ExecutionStatus
from app.api.v1 import api_router
from app.plugins.manager import initialize_plugins, shutdown_plugins
from app.plugins.loader import initialize_plugin_system

logger = logging.getLogger(__name__)

# E7: 全局 shutdown 事件
_shutdown_event = asyncio.Event()


async def shutdown_all():
    """E7: 统一关闭所有资源"""
    logger.info("Executing unified shutdown...")
    _shutdown_event.set()
    await shutdown_plugins()
    await close_db()
    try:
        from app.core.rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        if hasattr(limiter, '_redis') and limiter._redis:
            await limiter._redis.close()
    except Exception as e:
        logger.debug(f"Rate limiter cleanup skipped: {e}")
    logger.info("Unified shutdown complete")


def _signal_handler(signum, frame):
    """E5: 信号处理 — 触发优雅关闭"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    _shutdown_event.set()


async def cleanup_stale_executions():
    """清理僵尸执行记录 - 将长时间RUNNING状态的执行标记为FAILED"""
    try:
        async with AsyncSessionLocal() as db:
            # 查找超过30分钟仍在RUNNING状态的执行
            # 使用naive datetime以匹配数据库中的TIMESTAMP WITHOUT TIME ZONE
            threshold = datetime.utcnow() - timedelta(minutes=30)

            result = await db.execute(
                select(Execution).where(
                    Execution.status == ExecutionStatus.RUNNING,
                    Execution.started_at < threshold,
                )
            )
            stale_executions = result.scalars().all()

            if stale_executions:
                logger.warning(f"Found {len(stale_executions)} stale executions, marking as FAILED")
                for execution in stale_executions:
                    execution.status = ExecutionStatus.FAILED
                    execution.completed_at = datetime.utcnow()
                    execution.error_log = "执行超时（超过30分钟），系统自动标记为失败"
                    logger.info(f"Marked stale execution {execution.id} as FAILED")

                await db.commit()
                logger.info(f"Cleaned up {len(stale_executions)} stale executions")
            else:
                logger.info("No stale executions found")

    except Exception as e:
        logger.error(f"Failed to cleanup stale executions: {e}", exc_info=True)


async def cleanup_stale_iterations():
    """清理僵尸迭代记录 - 将RUNNING状态但进程已重启的迭代标记为FAILED"""
    try:
        from app.models.iteration import Iteration, IterationStatus
        async with AsyncSessionLocal() as db:
            # 所有仍在 RUNNING 的迭代都是僵尸（进程重启后不可能还在运行）
            result = await db.execute(
                select(Iteration).where(
                    Iteration.status == IterationStatus.RUNNING,
                )
            )
            stale = result.scalars().all()

            if stale:
                logger.warning(f"Found {len(stale)} stale iterations, marking as FAILED")
                for it in stale:
                    it.status = IterationStatus.FAILED
                    it.error_message = "进程重启，迭代被中断。请重新提交反馈。"
                    logger.info(f"Marked stale iteration {it.id} as FAILED")
                await db.commit()
                logger.info(f"Cleaned up {len(stale)} stale iterations")
            else:
                logger.info("No stale iterations found")

    except Exception as e:
        logger.error(f"Failed to cleanup stale iterations: {e}", exc_info=True)


async def ensure_memory_configs():
    """为缺少记忆配置的 Crew 补建默认 MemoryConfig"""
    try:
        from app.models.crew import Crew
        from app.models.memory import MemoryConfig
        async with AsyncSessionLocal() as db:
            # 查找没有 MemoryConfig 的 Crew
            crews_result = await db.execute(select(Crew))
            all_crews = crews_result.scalars().all()

            configs_result = await db.execute(select(MemoryConfig.crew_id))
            existing_crew_ids = {row[0] for row in configs_result.all()}

            created = 0
            for crew in all_crews:
                if crew.id not in existing_crew_ids:
                    db.add(MemoryConfig(
                        crew_id=crew.id,
                        short_term_enabled=True,
                        short_term_window=5,
                        long_term_enabled=True,
                        vector_store_type="chromadb",
                        retrieval_strategy="similarity",
                        top_k=3,
                        auto_index_on_complete=True,
                    ))
                    created += 1

            if created:
                await db.commit()
                logger.info(f"Created {created} missing MemoryConfig records")
            else:
                logger.info("All crews have MemoryConfig")

    except Exception as e:
        logger.error(f"Failed to ensure memory configs: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # E5: 注册信号处理器
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # 启动时
    await init_db()
    await cleanup_stale_executions()
    await cleanup_stale_iterations()
    await ensure_memory_configs()

    # 自动 seed 内置模板（幂等，已有则跳过）
    try:
        from app.services.template_seeder import seed_templates
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as seed_db:
            result = await seed_templates(seed_db)
            await seed_db.commit()
            if result.get("created"):
                logger.info(f"Seeded {len(result['created'])} built-in templates")
    except Exception as e:
        logger.error(f"Failed to seed templates: {e}")

    try:
        await initialize_plugin_system()
        logger.info("Plugin system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize plugin system: {e}")

    yield

    # E7+C9: 统一关闭
    await shutdown_all()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="多智能体协作工作流平台API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS中间件 — 含桌面应用兼容（Tauri 自定义协议发送 Origin: null）
import re as _re
_desktop_origin_regex = r"(https?|tauri)://(localhost|127\.0\.0\.1|tauri\.localhost)(:\d+)?$"
_cors_origins = settings.CORS_ORIGINS + ["null"]  # "null" 匹配 Tauri WebView 自定义协议
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_desktop_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全头中间件
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 可观测性中间件 — 请求耗时指标
from app.core.observability import MetricsMiddleware
app.add_middleware(MetricsMiddleware)

# 全局异常处理器
from app.core.exceptions import register_exception_handlers
register_exception_handlers(app)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """处理数据库完整性错误（如重复注册）"""
    import logging
    logging.getLogger(__name__).error(f"IntegrityError: {exc.orig}")
    return JSONResponse(
        status_code=400,
        content={"detail": f"数据完整性错误: {str(exc.orig)[:200]}"},
    )


@app.get("/")
async def root():
    """健康检查"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus 指标端点 — 报告第一章 可观测性 (5/10)"""
    from app.core.observability import metrics
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=metrics.to_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
