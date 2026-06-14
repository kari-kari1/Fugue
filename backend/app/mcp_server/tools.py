"""MCP Tool definitions — execute_workflow, get_execution_status, list_workflows.

所有数据库依赖在函数体内延迟导入，避免模块加载时因模型缺失而失败。
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP


def register_tools(server: FastMCP) -> None:
    """将 Agent 工具注册到 FastMCP 服务器。"""

    @server.tool()
    async def execute_workflow(
        workflow_id: str,
        inputs: dict[str, Any] | None = None,
        llm_api_keys: dict[str, str] | None = None,
        llm_base_urls: dict[str, str] | None = None,
    ) -> str:
        """Start execution of a workflow by its ID.

        Args:
            workflow_id: The ID of the workflow (crew) to execute.
            inputs: Optional input variables for the workflow.
            llm_api_keys: Optional mapping of provider name to API key.
            llm_base_urls: Optional mapping of provider name to base URL.

        Returns:
            JSON string with execution_id and initial status.
        """
        from app.core.database import db_session_manager
        from app.models.crew import Crew
        from app.models.execution import Execution, ExecutionStatus

        async with db_session_manager.get_session() as session:
            crew = await session.get(Crew, workflow_id)
            if crew is None:
                return json.dumps({"error": f"Workflow '{workflow_id}' not found"})

            execution = Execution(
                crew_id=workflow_id,
                status=ExecutionStatus.PENDING,
                inputs=inputs or {},
            )
            # Pass LLM credentials through to the execution record
            execution.llm_api_keys = llm_api_keys or {}
            execution.llm_base_urls = llm_base_urls or {}
            session.add(execution)
            await session.commit()
            await session.refresh(execution)

            return json.dumps({
                "execution_id": str(execution.id),
                "status": execution.status.value,
                "workflow_id": workflow_id,
            })

    @server.tool()
    async def get_execution_status(execution_id: str) -> str:
        """Get the current status and details of a workflow execution.

        Args:
            execution_id: The ID of the execution to query.

        Returns:
            JSON string with execution details and current status.
        """
        from app.core.database import db_session_manager
        from app.models.execution import Execution

        async with db_session_manager.get_session() as session:
            execution = await session.get(Execution, execution_id)
            if execution is None:
                return json.dumps({"error": f"Execution '{execution_id}' not found"})

            return json.dumps({
                "execution_id": str(execution.id),
                "status": execution.status.value,
                "workflow_id": execution.crew_id,
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
                "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
                "error_message": execution.error_message,
            })

    @server.tool()
    async def list_workflows(
        limit: int = 20,
        offset: int = 0,
        user_id: str | None = None,
    ) -> str:
        """List available workflows with pagination.

        Args:
            limit: Maximum number of workflows to return (default 20).
            offset: Number of workflows to skip (default 0).
            user_id: Optional filter by owner user ID.

        Returns:
            JSON string with list of workflows and pagination info.
        """
        from sqlalchemy import select

        from app.core.database import db_session_manager
        from app.models.crew import Crew

        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        async with db_session_manager.get_session() as session:
            query = select(Crew).offset(offset).limit(limit)
            if user_id is not None:
                query = query.where(Crew.user_id == user_id)

            result = await session.execute(query)
            crews = result.scalars().all()

            workflows = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "description": c.description,
                }
                for c in crews
            ]

            return json.dumps({
                "workflows": workflows,
                "limit": limit,
                "offset": offset,
                "count": len(workflows),
            })

    @server.tool()
    async def get_task_status(execution_id: str) -> str:
        """获取工作流执行中每个任务的详细状态。

        Args:
            execution_id: 执行实例 ID
        """
        import json
        async with db_session_manager.get_session() as db:
            from app.models.execution import TaskExecution
            result = await db.execute(
                select(TaskExecution).where(TaskExecution.execution_id == execution_id)
            )
            tasks = result.scalars().all()
            if not tasks:
                return json.dumps({"error": "No tasks found"})
            return json.dumps([{
                "task_id": str(t.task_id),
                "agent_id": str(t.agent_id) if t.agent_id else None,
                "status": t.status.value if hasattr(t.status, 'value') else t.status,
                "output": (t.output or "")[:200],
                "tokens_used": t.tokens_used,
                "cost_usd": t.cost_usd,
                "retry_count": t.retry_count,
                "error": t.error_message,
            } for t in tasks], ensure_ascii=False)

    @server.tool()
    async def list_deferred_tasks(limit: int = 20) -> str:
        """列出所有待处理/重试中的延迟任务。

        Args:
            limit: 返回数量上限（默认 20）
        """
        import json

        from app.models.execution import TaskExecution, TaskExecutionStatus
        async with db_session_manager.get_session() as db:
            result = await db.execute(
                select(TaskExecution)
                .where(TaskExecution.status.in_([
                    TaskExecutionStatus.PENDING,
                    TaskExecutionStatus.RETRYING,
                ]))
                .order_by(TaskExecution.created_at.desc())
                .limit(limit)
            )
            tasks = result.scalars().all()
            return json.dumps([{
                "task_id": str(t.task_id),
                "execution_id": str(t.execution_id),
                "status": t.status.value if hasattr(t.status, 'value') else t.status,
                "retry_count": t.retry_count,
                "error": t.error_message,
            } for t in tasks], ensure_ascii=False)
