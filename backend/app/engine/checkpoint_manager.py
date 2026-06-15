"""断点续传管理器"""

import logging
from typing import Dict, List, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkpoint import ExecutionCheckpoint
from app.models.execution import TaskExecution, TaskExecutionStatus

logger = logging.getLogger(__name__)


class CheckpointManager:
    """断点续传管理器

    职责：
    - 在任务完成后自动创建断点
    - 在暂停请求被接受时创建手动断点
    - 从最新断点恢复执行状态
    """

    def __init__(self, db: AsyncSession, execution_id: str):
        self.db = db
        self.execution_id = execution_id

    async def create_checkpoint(
        self,
        checkpoint_type: str,
        task_id: Optional[str] = None,
        task_name: Optional[str] = None,
        completed_task_ids: List[str] = None,
        task_outputs: Dict[str, str] = None,
        context: Dict[str, Any] = None,
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
    ) -> ExecutionCheckpoint:
        """创建断点"""
        checkpoint = ExecutionCheckpoint(
            execution_id=self.execution_id,
            checkpoint_type=checkpoint_type,
            task_id=task_id,
            task_name=task_name,
            completed_task_ids=completed_task_ids or [],
            task_outputs=task_outputs or {},
            context=context or {},
            total_tokens_so_far=total_tokens,
            total_cost_so_far=int(total_cost_usd * 10000),  # 存为万分之一美元
        )
        self.db.add(checkpoint)
        await self.db.flush()

        logger.info(
            f"[CHECKPOINT] Created checkpoint for execution {self.execution_id}: "
            f"type={checkpoint_type}, task={task_name or task_id}, "
            f"completed={len(completed_task_ids or [])}"
        )
        return checkpoint

    async def get_latest_checkpoint(self) -> Optional[ExecutionCheckpoint]:
        """获取最新的断点"""
        result = await self.db.execute(
            select(ExecutionCheckpoint)
            .where(ExecutionCheckpoint.execution_id == self.execution_id)
            .order_by(ExecutionCheckpoint.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def resume_from_checkpoint(self) -> Optional[Dict[str, Any]]:
        """从断点恢复执行状态

        Returns:
            恢复数据字典，如果无断点则返回 None。
            - completed_task_ids: 已完成的任务ID列表
            - task_outputs: 已完成任务的输出 {task_id: output}
            - context: 执行上下文
            - total_tokens: 截至断点的累计token数
            - total_cost_usd: 截至断点的累计费用（美元）
        """
        checkpoint = await self.get_latest_checkpoint()
        if not checkpoint:
            logger.info(
                f"[CHECKPOINT] No checkpoint found for execution {self.execution_id}"
            )
            return None

        logger.info(
            f"[CHECKPOINT] Resuming from checkpoint {checkpoint.id} "
            f"(type={checkpoint.checkpoint_type}, "
            f"completed={len(checkpoint.completed_task_ids or [])} tasks)"
        )

        return {
            "completed_task_ids": checkpoint.completed_task_ids or [],
            "task_outputs": checkpoint.task_outputs or {},
            "context": checkpoint.context or {},
            "total_tokens": checkpoint.total_tokens_so_far or 0,
            "total_cost_usd": (checkpoint.total_cost_so_far or 0) / 10000.0,
        }

    async def create_auto_checkpoint(
        self,
        task_id: str,
        task_name: str,
        completed_task_ids: List[str],
        task_outputs: Dict[str, str],
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
    ) -> ExecutionCheckpoint:
        """自动创建断点（每个任务完成后调用）"""
        return await self.create_checkpoint(
            checkpoint_type="task_end",
            task_id=task_id,
            task_name=task_name,
            completed_task_ids=list(completed_task_ids),
            task_outputs=dict(task_outputs),
            total_tokens=total_tokens,
            total_cost_usd=total_cost_usd,
        )

    async def create_manual_checkpoint(
        self,
        completed_task_ids: List[str],
        task_outputs: Dict[str, str],
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
        context: Dict[str, Any] = None,
    ) -> ExecutionCheckpoint:
        """手动创建断点（暂停时调用）"""
        return await self.create_checkpoint(
            checkpoint_type="pause",
            completed_task_ids=list(completed_task_ids),
            task_outputs=dict(task_outputs),
            total_tokens=total_tokens,
            total_cost_usd=total_cost_usd,
            context=context,
        )

    async def check_pause_requested(self) -> bool:
        """检查是否有暂停请求

        由执行引擎在每个任务循环中调用。
        如果有 pending 状态的暂停请求，将其标记为 accepted 并返回 True。
        """
        from app.models.checkpoint import ExecutionPauseRequest

        result = await self.db.execute(
            select(ExecutionPauseRequest).where(
                ExecutionPauseRequest.execution_id == self.execution_id,
                ExecutionPauseRequest.status == "pending",
            ).limit(1)
        )
        pause_req = result.scalar()

        if pause_req:
            pause_req.status = "accepted"
            await self.db.flush()
            logger.info(
                f"[CHECKPOINT] Pause request accepted for execution {self.execution_id}"
            )
            return True

        return False

    async def complete_pause_request(self):
        """将暂停请求标记为已完成"""
        from app.models.checkpoint import ExecutionPauseRequest

        result = await self.db.execute(
            select(ExecutionPauseRequest).where(
                ExecutionPauseRequest.execution_id == self.execution_id,
                ExecutionPauseRequest.status == "accepted",
            )
        )
        pause_req = result.scalar_one_or_none()

        if pause_req:
            pause_req.status = "completed"
            await self.db.flush()
