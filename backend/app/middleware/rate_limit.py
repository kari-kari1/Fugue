"""速率限制中间件 — FastAPI 中间件形式

自动为所有请求应用全局限流，认证端点使用更严格的限制。
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.rate_limiter import get_rate_limiter
from app.core.exceptions import ErrorCode

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """全局速率限制中间件"""

    def __init__(
        self,
        app,
        global_limit: int = 120,
        global_window: int = 60,
        auth_limit: int = 10,
        auth_window: int = 60,
    ):
        super().__init__(app)
        self.global_limit = global_limit
        self.global_window = global_window
        self.auth_limit = auth_limit
        self.auth_window = auth_window

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        limiter = get_rate_limiter()
        client_ip = request.client.host if request.client else "unknown"

        # 认证端点使用更严格的限制
        is_auth = request.url.path.startswith("/api/v1/auth")
        if is_auth:
            key = f"rate:auth:{client_ip}"
            limit = self.auth_limit
            window = self.auth_window
        else:
            key = f"rate:global:{client_ip}"
            limit = self.global_limit
            window = self.global_window

        allowed = await limiter.check_rate_limit(key, limit=limit, window_seconds=window)
        if not allowed:
            remaining = 0
            logger.warning("Rate limited: ip=%s path=%s", client_ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": ErrorCode.RATE_LIMITED.value,
                        "message": f"请求过于频繁，请 {window} 秒后重试",
                        "detail": {"retry_after": window},
                    }
                },
                headers={"Retry-After": str(window)},
            )

        response = await call_next(request)

        # 添加速率限制响应头
        remaining = await limiter.get_remaining(key, limit=limit, window_seconds=window)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window)

        return response
