"""MCP Resource definitions — workflow templates.

暴露工作流模板为 MCP Resources，支持静态资源和参数化模板。
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP


def register_resources(server: FastMCP) -> None:
    """将工作流资源注册到 FastMCP 服务器。"""

    @server.resource("fugue://workflows")
    async def list_workflow_templates() -> str:
        """List all available workflow templates.

        Returns a JSON array of workflow summaries.
        """
        from sqlalchemy import select
        from app.core.database import db_session_manager
        from app.models.crew import Crew

        async with db_session_manager.get_session() as session:
            result = await session.execute(select(Crew).limit(100))
            crews = result.scalars().all()

            return json.dumps([
                {
                    "uri": f"fugue://workflows/{c.id}",
                    "name": c.name,
                    "description": c.description,
                }
                for c in crews
            ])

    @server.resource("fugue://workflows/{workflow_id}")
    async def get_workflow_detail(workflow_id: str) -> str:
        """Get detailed configuration for a specific workflow.

        Args:
            workflow_id: The workflow ID to retrieve.

        Returns:
            JSON object with full workflow configuration.
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.core.database import db_session_manager
        from app.models.crew import Crew

        async with db_session_manager.get_session() as session:
            result = await session.execute(
                select(Crew)
                .where(Crew.id == workflow_id)
                .options(selectinload(Crew.agents), selectinload(Crew.tasks))
            )
            crew = result.scalar_one_or_none()

            if crew is None:
                return json.dumps({"error": f"Workflow '{workflow_id}' not found"})

            agents = [
                {"id": str(a.id), "name": a.name, "role": a.role}
                for a in crew.agents
            ]
            tasks = [
                {"id": str(t.id), "name": t.name, "description": t.description}
                for t in crew.tasks
            ]

            return json.dumps({
                "id": str(crew.id),
                "name": crew.name,
                "description": crew.description,
                "agents": agents,
                "tasks": tasks,
            })
