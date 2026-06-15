"""任务完成处理 — 从 executor.py 拆分

负责: 保存任务结果、记忆存储、知识库索引、完成事件发布。
报告 P0-4 要求拆分 executor.py 为独立模块。
"""

import logging
import uuid as _uuid
from datetime import datetime
from typing import Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.agent import Agent
from app.models.execution import Execution, TaskExecution, TaskExecutionStatus
from app.models.task import Task
from app.services.event_publisher import event_publisher

logger = logging.getLogger(__name__)


async def finalize_task(
    engine,
    db: AsyncSession,
    execution: Execution,
    task: Task,
    agent: Agent,
    te: TaskExecution,
    final_content: str,
    all_tool_calls: list,
    total_tokens: int,
    total_cost: float,
    task_outputs: Dict[str, str],
):
    """保存任务结果、记忆、知识库索引，发布完成事件"""
    te.status = TaskExecutionStatus.COMPLETED
    te.completed_at = datetime.utcnow()
    te.output = final_content
    te.tokens_used = total_tokens
    te.cost_usd = total_cost

    thought_entries = []
    for tc_entry in all_tool_calls:
        thought_entries.append({
            "timestamp": tc_entry.get("timestamp", ""),
            "type": "tool_use",
            "content": f"[{tc_entry.get('tool_name','')}] {str(tc_entry.get('output',''))[:200]}",
        })
    thought_entries.append({
        "timestamp": datetime.utcnow().isoformat(),
        "type": "reasoning",
        "content": (final_content or "")[:500],
    })
    te.thoughts = thought_entries
    te.tool_calls = all_tool_calls
    flag_modified(te, 'thoughts')
    flag_modified(te, 'tool_calls')
    task_outputs[task.id] = final_content or ""
    engine._add_trace(execution, "task.completed", agent_name=agent.name, task_name=task.name, data={
        "tokens": total_tokens, "cost": f"${total_cost:.4f}", "tool_calls": len(all_tool_calls),
    })
    await db.commit()

    # 保存结论到 Agent 长期记忆
    if final_content and agent:
        try:
            from app.services.memory_service import MemoryService
            mem_svc = MemoryService(db)
            await mem_svc.save_memory(
                agent_id=str(agent.id),
                content=final_content[:2000],
                memory_type="conclusion",
                execution_id=str(execution.id),
            )
        except Exception as mem_err:
            logger.warning("[EXECUTOR] Memory save failed: %s", mem_err)

    # 自动索引输出到知识库
    if getattr(engine, '_memory_config', None) and getattr(engine._memory_config, 'auto_index_on_complete', True):
        try:
            from app.services.vector_store import get_vector_store
            vs = get_vector_store()
            if vs and final_content:
                from app.models.memory import AgentKnowledgeMapping
                _mappings = await db.execute(
                    select(AgentKnowledgeMapping).where(AgentKnowledgeMapping.agent_id == agent.id)
                )
                _mapping = _mappings.scalars().first()
                if _mapping:
                    await vs.add_documents(
                        knowledge_base_id=str(_mapping.knowledge_base_id),
                        documents=[{
                            "id": str(_uuid.uuid4()),
                            "content": final_content[:5000],
                            "metadata": {
                                "task_name": task.name,
                                "agent_id": str(agent.id),
                                "execution_id": str(execution.id),
                                "type": "task_output",
                            },
                        }],
                    )
                    logger.info("[EXECUTOR] Auto-indexed task output to KB: %s", task.name)
        except Exception as idx_err:
            logger.warning("[EXECUTOR] Auto-index failed: %s", idx_err)

    await event_publisher.publish_task_completed(
        execution_id=engine.execution_id,
        task_name=task.name, agent_name=agent.name,
        tokens_used=total_tokens, cost_usd=total_cost,
    )
