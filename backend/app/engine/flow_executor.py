"""事件驱动 Flow 编排器 — @start / @listen / @router 装饰器模式

对标 CrewAI Flow 的事件驱动编排层，支持跨 Flow 事件传播。
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# 全局事件总线
_event_listeners: Dict[str, List[Callable]] = {}
_flow_registry: Dict[str, "Flow"] = {}


class FlowEvent:
    """Flow 事件"""
    def __init__(self, name: str, data: Any = None, source: str = None):
        self.name = name
        self.data = data
        self.source = source


async def emit(event_name: str, data: Any = None, source: str = None):
    """触发事件，通知所有监听器"""
    event = FlowEvent(name=event_name, data=data, source=source)
    listeners = _event_listeners.get(event_name, [])
    logger.info(f"[FLOW] Emitting event '{event_name}' to {len(listeners)} listener(s)")
    for listener in listeners:
        try:
            result = listener(event)
            if asyncio.iscoroutine(result):
                result = await result
            # router 监听器返回非空值时，触发目标事件
            if result and isinstance(result, str):
                await emit(result, data=data, source=f"{source or 'flow'}::{event_name}")
        except Exception as e:
            logger.error(f"[FLOW] Listener for '{event_name}' failed: {e}")


# ── 装饰器 ──────────────────────────────────────────


def start(event_name: str = None):
    """标记 Flow 入口方法。当 Flow 启动时自动调用标记为 @start 的方法。

    Args:
        event_name: 可选，完成后自动触发的后续事件名
    """
    def decorator(func: Callable):
        func._flow_start = True
        func._flow_start_event = event_name
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def listen(event_name: str):
    """注册事件监听器。当指定事件触发时调用装饰的方法。

    Args:
        event_name: 监听的事件名
    """
    def decorator(func: Callable):
        if event_name not in _event_listeners:
            _event_listeners[event_name] = []
        _event_listeners[event_name].append(func)
        func._flow_listen = event_name
        logger.info(f"[FLOW] Registered listener '{func.__name__}' for event '{event_name}'")
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def router(condition_func: Callable[[Dict], str]):
    """条件路由器。根据事件数据返回下一个事件名，实现条件分支。

    Args:
        condition_func: 接收事件 data，返回下一个事件名
    """
    def decorator(func: Callable):
        async def router_wrapper(event: FlowEvent):
            next_event = condition_func(event.data or {})
            if next_event:
                logger.info(f"[FLOW] Router '{func.__name__}' routing to '{next_event}'")
                result = await func(event)
                await emit(next_event, data=result, source="router")
                return result
            return None

        if func.__name__ not in [f.__name__ for f in _event_listeners.get("__router__", [])]:
            _event_listeners.setdefault("__router__", []).append(router_wrapper)
        return router_wrapper
    return decorator


# ── Flow 基类 ─────────────────────────────────────


class Flow:
    """事件驱动 Flow 基类

    用法:
        class MyFlow(Flow):
            @start()
            async def begin(self):
                return {"input": "data"}

            @listen("my_event")
            async def handle(self, event: FlowEvent):
                pass
    """

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self._running = False
        _flow_registry[self.name] = self

    async def run(self, input_data: Any = None) -> None:
        """启动 Flow：找到所有 @start 方法并执行"""
        self._running = True
        logger.info(f"[FLOW] Starting flow '{self.name}'")
        for attr_name in dir(self):
            attr = getattr(self, attr_name, None)
            if callable(attr) and getattr(attr, '_flow_start', False):
                try:
                    result = attr()
                    if asyncio.iscoroutine(result):
                        result = await result
                    start_event = getattr(attr, '_flow_start_event', None)
                    if start_event:
                        await emit(start_event, data=result, source=self.name)
                except Exception as e:
                    logger.error(f"[FLOW] Start method '{attr_name}' failed: {e}")
        self._running = False

    async def stop(self):
        self._running = False
        logger.info(f"[FLOW] Stopped flow '{self.name}'")


def clear_flows():
    """清理所有已注册的 Flow 和监听器（测试用）"""
    _event_listeners.clear()
    _flow_registry.clear()
