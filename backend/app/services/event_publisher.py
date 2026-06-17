"""事件发布服务 - 发布执行事件到WebSocket"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.core.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    # Agent执行事件
    AGENT_THINKING = "agent.thinking"
    AGENT_TOOL_CALL = "agent.tool_call"
    AGENT_OUTPUT = "agent.output"
    AGENT_ERROR = "agent.error"

    # Task执行事件
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_RETRYING = "task.retrying"
    TASK_SKIPPED = "task.skipped"

    # Crew执行事件
    CREW_STARTED = "crew.started"
    CREW_COMPLETED = "crew.completed"
    CREW_FAILED = "crew.failed"
    CREW_PAUSED = "crew.paused"
    CREW_RESUMED = "crew.resumed"
    CREW_CANCELLED = "crew.cancelled"

    # 迭代事件
    ITERATION_STARTED = "iteration.started"
    ITERATION_PROGRESS = "iteration.progress"
    ITERATION_COMPLETED = "iteration.completed"
    ITERATION_FAILED = "iteration.failed"

    # 系统事件
    COST_UPDATE = "system.cost_update"
    PROGRESS_UPDATE = "system.progress"
    HEARTBEAT = "system.heartbeat"
    WARNING = "system.warning"
    HUMAN_REVIEW_NEEDED = "system.review"


class EventPublisher:
    """事件发布服务 - 发布执行事件到WebSocket"""

    async def publish(
        self,
        execution_id: str,
        event_type: EventType,
        data: dict[str, Any] | None = None,
        agent_name: str = "",
        task_name: str = "",
    ):
        """发布事件到WebSocket"""
        message = {
            "type": event_type.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "execution_id": execution_id,
            "agent_name": agent_name,
            "task_name": task_name,
            "data": data or {},
        }

        await ws_manager.broadcast(execution_id, message)
        logger.debug(f"Published event {event_type.value} for execution {execution_id}")

    async def publish_agent_thinking(
        self,
        execution_id: str,
        agent_name: str,
        thought: str,
        step: str = "",
    ):
        """发布Agent思考事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.AGENT_THINKING,
            agent_name=agent_name,
            data={
                "content": thought,
                "step": step,
            },
        )

    async def publish_agent_tool_call(
        self,
        execution_id: str,
        agent_name: str,
        tool_name: str,
        tool_input: dict[str, Any],
    ):
        """发布Agent工具调用事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.AGENT_TOOL_CALL,
            agent_name=agent_name,
            data={
                "tool_name": tool_name,
                "input": tool_input,
            },
        )

    async def publish_task_started(
        self,
        execution_id: str,
        task_name: str,
        agent_name: str,
    ):
        """发布任务开始事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.TASK_STARTED,
            task_name=task_name,
            agent_name=agent_name,
        )

    async def publish_task_completed(
        self,
        execution_id: str,
        task_name: str,
        agent_name: str,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        duration_ms: int = 0,
    ):
        """发布任务完成事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.TASK_COMPLETED,
            task_name=task_name,
            agent_name=agent_name,
            data={
                "tokens": tokens_used,
                "cost": f"${cost_usd:.4f}",
                "duration": f"{duration_ms}ms",
            },
        )

    async def publish_task_failed(
        self,
        execution_id: str,
        task_name: str,
        agent_name: str,
        error: str,
    ):
        """发布任务失败事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.TASK_FAILED,
            task_name=task_name,
            agent_name=agent_name,
            data={
                "error": error,
            },
        )

    async def publish_progress(
        self,
        execution_id: str,
        completed: int,
        total: int,
    ):
        """发布进度更新事件"""
        progress = (completed / total * 100) if total > 0 else 0
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.PROGRESS_UPDATE,
            data={
                "completed": completed,
                "total": total,
                "progress": round(progress, 2),
            },
        )

    async def publish_cost_update(
        self,
        execution_id: str,
        total_tokens: int,
        total_cost: float,
    ):
        """发布成本更新事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.COST_UPDATE,
            data={
                "total_tokens": total_tokens,
                "total_cost": f"${total_cost:.4f}",
            },
        )

    async def publish_crew_started(
        self,
        execution_id: str,
        crew_name: str,
        process_type: str,
    ):
        """发布工作流开始事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.CREW_STARTED,
            data={
                "crew_name": crew_name,
                "process": process_type,
            },
        )

    async def publish_crew_completed(
        self,
        execution_id: str,
        total_tokens: int,
        total_cost: float,
        tasks_completed: int,
    ):
        """发布工作流完成事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.CREW_COMPLETED,
            data={
                "total_tokens": total_tokens,
                "total_cost": f"${total_cost:.4f}",
                "tasks_completed": tasks_completed,
            },
        )

    async def publish_crew_failed(
        self,
        execution_id: str,
        error: str,
    ):
        """发布工作流失败事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.CREW_FAILED,
            data={
                "error": error,
            },
        )

    async def publish_warning(
        self,
        execution_id: str,
        message: str,
        level: str = "warning",
        extra: dict = None,
    ):
        """发布预警事件（如成本超限、审批请求）"""
        data = {
            "message": message,
            "level": level,
        }
        if extra:
            data.update(extra)
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.WARNING,
            data=data,
        )

    async def publish_iteration_started(
        self,
        execution_id: str,
        iteration_id: str,
        iteration_number: int,
    ):
        """发布迭代开始事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.ITERATION_STARTED,
            data={
                "iteration_id": iteration_id,
                "iteration_number": iteration_number,
            },
        )

    async def publish_iteration_completed(
        self,
        execution_id: str,
        iteration_id: str,
    ):
        """发布迭代完成事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.ITERATION_COMPLETED,
            data={
                "iteration_id": iteration_id,
            },
        )

    async def publish_iteration_failed(
        self,
        execution_id: str,
        iteration_id: str,
        error_message: str,
    ):
        """发布迭代失败事件"""
        await self.publish(
            execution_id=execution_id,
            event_type=EventType.ITERATION_FAILED,
            data={
                "iteration_id": iteration_id,
                "error": error_message,
            },
        )


# 全局事件发布器实例
event_publisher = EventPublisher()
