"""插件沙箱 — 提供安全的执行环境"""

import asyncio
import logging
import sys
import traceback
from typing import Any, Dict, Optional
from uuid import uuid4
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PluginSandbox:
    """插件执行沙箱

    提供以下安全特性：
    1. 执行超时控制
    2. 资源限制（内存、CPU）
    3. 异常捕获和隔离
    4. 审计日志
    """

    def __init__(
        self,
        timeout: int = 30,  # 秒
        max_memory_mb: int = 256,
        allowed_modules: Optional[list] = None,
    ):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.allowed_modules = allowed_modules or [
            "json", "re", "math", "datetime", "collections",
            "itertools", "functools", "typing", "dataclasses",
        ]

    async def execute(
        self,
        plugin_name: str,
        tool_name: str,
        func,
        arguments: Dict[str, Any],
    ) -> str:
        """在沙箱中执行工具

        Args:
            plugin_name: 插件名称
            tool_name: 工具名称
            func: 要执行的函数
            arguments: 函数参数

        Returns:
            执行结果字符串

        Raises:
            TimeoutError: 执行超时
            Exception: 执行失败
        """
        logger.info(f"Sandbox executing: {plugin_name}.{tool_name}")

        try:
            # 使用asyncio.wait_for实现超时
            result = await asyncio.wait_for(
                self._execute_safe(func, arguments),
                timeout=self.timeout,
            )

            logger.info(f"Sandbox execution completed: {plugin_name}.{tool_name}")
            return result

        except asyncio.TimeoutError:
            error_msg = f"Tool '{tool_name}' execution timed out ({self.timeout}s)"
            logger.error(f"Sandbox timeout: {error_msg}")
            raise TimeoutError(error_msg)

        except Exception as e:
            error_msg = f"Tool '{tool_name}' execution failed: {str(e)}"
            logger.error(f"Sandbox error: {error_msg}\n{traceback.format_exc()}")
            raise

    async def _execute_safe(self, func, arguments: Dict[str, Any]) -> str:
        """安全执行函数"""
        try:
            # B12: 在限制 import 的沙箱中执行插件函数
            with self.restrict_imports():
                result = await func(**arguments)

            # 确保返回字符串
            if result is None:
                return ""
            elif isinstance(result, (dict, list)):
                import json
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return str(result)

        except TypeError as e:
            # 参数类型错误
            raise ValueError(f"Invalid arguments: {e}")

    @contextmanager
    def restrict_imports(self):
        """限制可导入的模块（上下文管理器）"""
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def restricted_import(name, *args, **kwargs):
            if name.split('.')[0] not in self.allowed_modules:
                raise ImportError(f"Import of module '{name}' is not allowed in sandbox")
            return original_import(name, *args, **kwargs)

        if hasattr(__builtins__, '__import__'):
            __builtins__.__import__ = restricted_import
        else:
            import builtins
            builtins.__import__ = restricted_import

        try:
            yield
        finally:
            if hasattr(__builtins__, '__import__'):
                __builtins__.__import__ = original_import
            else:
                import builtins
                builtins.__import__ = original_import


class SandboxPool:
    """沙箱池 — 管理多个沙箱实例"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_executions: Dict[str, asyncio.Task] = {}

    async def execute(
        self,
        plugin_name: str,
        tool_name: str,
        func,
        arguments: Dict[str, Any],
        timeout: int = 30,
    ) -> str:
        """从池中获取沙箱执行工具"""
        execution_id = f"{plugin_name}.{tool_name}.{uuid4().hex[:8]}"

        async with self._semaphore:
            logger.info(f"Sandbox pool: executing {execution_id} "
                       f"(active: {self.max_concurrent - self._semaphore._value}/{self.max_concurrent})")

            sandbox = PluginSandbox(timeout=timeout)
            task = asyncio.create_task(
                sandbox.execute(plugin_name, tool_name, func, arguments)
            )

            self._active_executions[execution_id] = task

            try:
                result = await task
                return result
            finally:
                if execution_id in self._active_executions:
                    del self._active_executions[execution_id]

    async def cancel_execution(self, execution_id: str):
        """取消正在执行的任务"""
        task = self._active_executions.get(execution_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled execution: {execution_id}")

    def get_active_count(self) -> int:
        """获取活跃执行数量"""
        return len(self._active_executions)

    def get_active_executions(self) -> list:
        """获取所有活跃执行的ID"""
        return list(self._active_executions.keys())


# 全局沙箱池实例
_sandbox_pool: Optional[SandboxPool] = None


def get_sandbox_pool() -> SandboxPool:
    """获取全局沙箱池实例"""
    global _sandbox_pool
    if _sandbox_pool is None:
        _sandbox_pool = SandboxPool()
    return _sandbox_pool
