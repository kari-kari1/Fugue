"""可观测性模块 — 报告第一章 可观测性 (5/10) 要求

提供:
- Prometheus 指标端点 (/metrics)
- Sentry 错误追踪集成
- 请求耗时中间件
- 执行指标收集
"""

import logging
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# ─── Prometheus 指标 ────────────────────────────────────────────────────────

class MetricsCollector:
    """内存级 Prometheus 指标收集器（不依赖 prometheus_client 库）"""

    def __init__(self):
        self.http_requests_total: dict[str, int] = {}      # method+path+status -> count
        http_request_duration_seconds: dict[str, list] = {} # method+path -> [durations]
        self._http_durations = http_request_duration_seconds
        self.execution_total: int = 0
        self.execution_success: int = 0
        self.execution_failed: int = 0
        self.task_total: int = 0
        self.task_success: int = 0
        self.task_failed: int = 0
        self.llm_calls_total: int = 0
        self.llm_tokens_total: int = 0
        self.llm_cost_total: float = 0.0
        self.active_executions: int = 0

    def record_http_request(self, method: str, path: str, status: int, duration: float):
        key = f'{method}|{path}|{status}'
        self.http_requests_total[key] = self.http_requests_total.get(key, 0) + 1
        dur_key = f'{method}|{path}'
        self._http_durations.setdefault(dur_key, []).append(duration)

    def record_execution(self, success: bool):
        self.execution_total += 1
        if success:
            self.execution_success += 1
        else:
            self.execution_failed += 1

    def record_task(self, success: bool):
        self.task_total += 1
        if success:
            self.task_success += 1
        else:
            self.task_failed += 1

    def record_llm_call(self, tokens: int, cost: float):
        self.llm_calls_total += 1
        self.llm_tokens_total += tokens
        self.llm_cost_total += cost

    def to_prometheus(self) -> str:
        """导出 Prometheus 文本格式"""
        lines = [
            "# HELP http_requests_total Total HTTP requests",
            "# TYPE http_requests_total counter",
        ]
        for key, count in self.http_requests_total.items():
            method, path, status = key.split("|")
            lines.append(f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')

        lines.extend([
            "# HELP execution_total Total workflow executions",
            "# TYPE execution_total counter",
            f"execution_total {self.execution_total}",
            f"execution_success_total {self.execution_success}",
            f"execution_failed_total {self.execution_failed}",

            "# HELP task_total Total task executions",
            "# TYPE task_total counter",
            f"task_total {self.task_total}",
            f"task_success_total {self.task_success}",
            f"task_failed_total {self.task_failed}",

            "# HELP llm_metrics LLM usage metrics",
            "# TYPE llm_calls_total counter",
            f"llm_calls_total {self.llm_calls_total}",
            f"llm_tokens_total {self.llm_tokens_total}",
            f"llm_cost_usd_total {self.llm_cost_total:.6f}",

            "# HELP active_executions Currently active executions",
            "# TYPE active_executions gauge",
            f"active_executions {self.active_executions}",
        ])

        return "\n".join(lines) + "\n"


# 全局单例
metrics = MetricsCollector()


# ─── 请求耗时中间件 ─────────────────────────────────────────────────────────

class MetricsMiddleware(BaseHTTPMiddleware):
    """记录每个 HTTP 请求的耗时和状态码"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        # 过滤 /metrics 自身和健康检查，避免噪音
        path = request.url.path
        if path not in ("/metrics", "/health"):
            # 归一化路径（去掉 ID 参数）
            normalized = self._normalize_path(path)
            metrics.record_http_request(request.method, normalized, response.status_code, duration)

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """将路径中的 UUID/ID 参数归一化为 {id}"""
        import re
        # UUID pattern
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}', path,
        )
        # 纯数字 ID
        path = re.sub(r'/\d+', '/{id}', path)
        return path


# ─── Sentry 集成 ────────────────────────────────────────────────────────────

def init_sentry(dsn: Optional[str] = None, environment: str = "development"):
    """初始化 Sentry 错误追踪（可选，需安装 sentry-sdk）"""
    if not dsn:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[sentry_logging],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
        logger.info("Sentry initialized for environment: %s", environment)
    except ImportError:
        logger.warning("sentry-sdk not installed, Sentry disabled. Install with: pip install sentry-sdk")
    except Exception as e:
        logger.warning("Failed to initialize Sentry: %s", e)
