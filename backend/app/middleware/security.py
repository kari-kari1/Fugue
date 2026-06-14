"""安全 HTTP 头中间件

为所有响应添加安全相关 HTTP 头，防止常见 Web 攻击。
"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """添加安全 HTTP 头"""

    def __init__(
        self,
        app,
        csp: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:;",
    ):
        super().__init__(app)
        self.csp = csp

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = self.csp
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # 仅对 HTTPS 请求添加 HSTS（Tauri 桌面端使用 tauri:// 协议，不适用）
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
