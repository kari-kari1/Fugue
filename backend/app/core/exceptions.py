"""统一异常处理体系

提供自定义异常类层次、错误码枚举和 FastAPI 全局异常处理器。
替代路由中分散的 HTTPException，统一 API 错误响应格式。
"""

import logging
from enum import Enum
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ─── 错误码枚举 ────────────────────────────────────────────────────────────

class ErrorCode(str, Enum):
    """业务错误码 — 前端可用于 i18n 和条件逻辑"""
    # 通用
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # 工作流
    CREW_NOT_FOUND = "CREW_NOT_FOUND"
    CREW_IN_USE = "CREW_IN_USE"

    # 知识库
    KB_NOT_FOUND = "KB_NOT_FOUND"
    KB_CHUNK_FAILED = "KB_CHUNK_FAILED"
    KB_SEARCH_FAILED = "KB_SEARCH_FAILED"
    KB_MAPPING_EXISTS = "KB_MAPPING_EXISTS"
    KB_MAPPING_NOT_FOUND = "KB_MAPPING_NOT_FOUND"

    # 迭代
    ITERATION_INVALID_STATE = "ITERATION_INVALID_STATE"

    # 审批
    APPROVAL_NOT_FOUND = "APPROVAL_NOT_FOUND"
    APPROVAL_STATE_CONFLICT = "APPROVAL_STATE_CONFLICT"


# ─── HTTP 状态码映射 ────────────────────────────────────────────────────────

_ERROR_STATUS_MAP: dict[ErrorCode, int] = {
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.CONFLICT: status.HTTP_409_CONFLICT,
    ErrorCode.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.CREW_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.CREW_IN_USE: status.HTTP_409_CONFLICT,
    ErrorCode.KB_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.KB_CHUNK_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.KB_SEARCH_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.KB_MAPPING_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCode.KB_MAPPING_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.ITERATION_INVALID_STATE: status.HTTP_400_BAD_REQUEST,
    ErrorCode.APPROVAL_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.APPROVAL_STATE_CONFLICT: status.HTTP_409_CONFLICT,
}


# ─── 自定义异常类 ────────────────────────────────────────────────────────────

class AppError(Exception):
    """应用业务异常基类"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        detail: Any | None = None,
    ):
        self.code = code
        self.message = message
        self.detail = detail
        self.status_code = _ERROR_STATUS_MAP.get(code, 500)
        super().__init__(message)


class NotFoundError(AppError):
    """资源不存在"""

    def __init__(self, code: ErrorCode, resource: str, resource_id: str = ""):
        msg = f"{resource}不存在" + (f": {resource_id}" if resource_id else "")
        super().__init__(code=code, message=msg)


class ConflictError(AppError):
    """资源冲突（重复创建、状态不符等）"""

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(code=code, message=message)


class ValidationError(AppError):
    """输入校验失败"""

    def __init__(self, message: str, detail: Any | None = None):
        super().__init__(code=ErrorCode.VALIDATION_ERROR, message=message, detail=detail)


class RateLimitError(AppError):
    """请求限流"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            code=ErrorCode.RATE_LIMITED,
            message=f"请求过于频繁，请 {retry_after} 秒后重试",
            detail={"retry_after": retry_after},
        )


# ─── 全局异常处理器注册 ──────────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器到 FastAPI 应用"""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """处理自定义业务异常 — 统一响应格式"""
        logger.warning(
            "AppError: code=%s message=%s path=%s",
            exc.code.value, exc.message, request.url.path,
        )
        body: dict[str, Any] = {
            "error": {
                "code": exc.code.value,
                "message": exc.message,
            }
        }
        if exc.detail is not None:
            body["error"]["detail"] = exc.detail
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """处理 Pydantic 请求验证错误 — 返回统一错误格式"""
        logger.warning(
            "ValidationError: path=%s errors=%s",
            request.url.path, exc.errors(),
        )
        messages = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            messages.append(f"{loc}: {err['msg']}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR.value,
                    "message": "请求参数验证失败",
                    "detail": messages,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """兜底处理未捕获异常 — 返回统一 500，不泄露内部信息"""
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "服务器内部错误，请稍后重试",
                }
            },
        )
