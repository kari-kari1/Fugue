"""结构化日志配置

提供 JSON 格式化器和请求追踪 ID 支持。
在多智能体并行执行环境下，通过 execution_id 和 trace_id 关联日志。
"""

import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

# ─── 上下文变量 — 跨 async 调用传播 ──────────────────────────────────────────

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
execution_id_var: ContextVar[str] = ContextVar("execution_id", default="")
agent_name_var: ContextVar[str] = ContextVar("agent_name", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


def set_trace_context(
    trace_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """设置当前请求/执行的日志上下文"""
    if trace_id is not None:
        trace_id_var.set(trace_id)
    if execution_id is not None:
        execution_id_var.set(execution_id)
    if agent_name is not None:
        agent_name_var.set(agent_name)
    if user_id is not None:
        user_id_var.set(user_id)


def clear_trace_context():
    """清除日志上下文"""
    trace_id_var.set("")
    execution_id_var.set("")
    agent_name_var.set("")
    user_id_var.set("")


def generate_trace_id() -> str:
    """生成短追踪 ID"""
    return uuid.uuid4().hex[:12]


# ─── JSON 格式化器 ───────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """将日志记录格式化为 JSON 行"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 追踪上下文
        trace_id = trace_id_var.get("")
        execution_id = execution_id_var.get("")
        agent_name = agent_name_var.get("")
        user_id = user_id_var.get("")

        if trace_id:
            log_entry["trace_id"] = trace_id
        if execution_id:
            log_entry["execution_id"] = execution_id
        if agent_name:
            log_entry["agent_name"] = agent_name
        if user_id:
            log_entry["user_id"] = user_id

        # 附加异常信息
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }
            if record.exc_text:
                log_entry["exception"]["traceback"] = record.exc_text

        # 附加额外字段
        for key in ("path", "method", "status_code", "duration_ms"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, ensure_ascii=False)


class ReadableFormatter(logging.Formatter):
    """开发模式下使用的可读格式化器（含追踪 ID）"""

    def format(self, record: logging.LogRecord) -> str:
        trace_id = trace_id_var.get("")
        execution_id = execution_id_var.get("")
        agent_name = agent_name_var.get("")

        prefix_parts = []
        if execution_id:
            prefix_parts.append(f"exec={execution_id[:8]}")
        if agent_name:
            prefix_parts.append(f"agent={agent_name}")
        if trace_id:
            prefix_parts.append(f"trace={trace_id[:8]}")

        prefix = " ".join(prefix_parts)
        if prefix:
            prefix = f"[{prefix}] "

        record.prefix = prefix
        base = super().format(record)
        return base


# ─── 日志配置 ────────────────────────────────────────────────────────────────

def setup_logging(json_mode: bool = False, level: str = "INFO"):
    """配置全局日志

    Args:
        json_mode: True 使用 JSON 格式（生产），False 使用可读格式（开发）
        level: 日志级别
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 移除已有的 handler（避免重复）
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    if json_mode:
        handler.setFormatter(JSONFormatter())
    else:
        formatter = ReadableFormatter(
            fmt="%(asctime)s %(prefix)s%(levelname)-8s %(name)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)

    root.addHandler(handler)

    # 降低第三方库噪音
    for noisy in ("httpx", "httpcore", "aiosqlite", "chromadb"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
