# backend/app/services/export_service.py

from typing import Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.crew import Crew
from app.models.agent import Agent
from app.models.task import Task
from app.models.execution import Execution, TaskExecution


class ExportService:
    """导出服务"""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    @staticmethod
    def _needs_code_block(text: str) -> bool:
        """判断文本是否需要用代码块包裹"""
        if not text:
            return False

        # 检测 Markdown 特殊字符
        special_chars = ['#', '*', '_', '|', '`', '>', '~', '[', ']', '!']
        if any(char in text for char in special_chars):
            return True

        # 检测行首列表标记
        lines = text.split('\n')
        for line in lines[:5]:  # 只检查前5行
            stripped = line.lstrip()
            if stripped.startswith(('- ', '* ', '+ ')):
                return True
            # 检测有序列表（数字. 空格）
            if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in '.)' and stripped[2] == ' ':
                return True

        return False

    @staticmethod
    def _wrap_in_code_block(text: str) -> str:
        """将文本包裹在代码块中"""
        if not text:
            return "（无输出）"

        # 如果文本包含三反引号，使用四反引号包裹
        if '```' in text:
            return f"````\n{text}\n````"
        else:
            return f"```\n{text}\n```"

    async def export_crew_json(self, crew_id: str) -> Dict[str, Any]:
        """导出工作流为JSON"""
        result = await self.db.execute(
            select(Crew)
            .where(
                Crew.id == crew_id,
                Crew.user_id == self.user_id,
            )
            .options(
                selectinload(Crew.agents),
                selectinload(Crew.tasks),
            )
        )
        crew = result.scalar_one_or_none()

        if not crew:
            raise ValueError("工作流不存在")

        return {
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "crew": {
                "name": crew.name,
                "description": crew.description,
                "process": crew.process.value if crew.process else None,
                "agents": [
                    {
                        "name": agent.name,
                        "role": agent.role,
                        "goal": agent.goal,
                        "backstory": agent.backstory,
                        "llm_provider": agent.llm_provider,
                        "llm_model": agent.llm_model,
                        "tools_config": agent.tools_config,
                    }
                    for agent in crew.agents
                ],
                "tasks": [
                    {
                        "name": task.name,
                        "description": task.description,
                        "expected_output": task.expected_output,
                        "output_type": task.output_type.value if task.output_type else None,
                        "agent_name": next(
                            (a.name for a in crew.agents if a.id == task.agent_id),
                            None,
                        ),
                        "context_task_ids": task.context_task_ids,
                    }
                    for task in crew.tasks
                ],
            },
        }

    async def export_execution_markdown(self, execution_id: str) -> str:
        """导出执行结果为Markdown"""
        result = await self.db.execute(
            select(Execution)
            .where(
                Execution.id == execution_id,
                Execution.user_id == self.user_id,
            )
            .options(
                selectinload(Execution.crew).selectinload(Crew.agents),
                selectinload(Execution.crew).selectinload(Crew.tasks),
                selectinload(Execution.task_executions),
            )
        )
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError("执行不存在")

        crew = execution.crew
        task_executions = {
            te.task_id: te for te in execution.task_executions
        }

        md = f"""# {crew.name} - 执行结果

**执行时间**: {execution.started_at.strftime('%Y-%m-%d %H:%M:%S') if execution.started_at else 'N/A'}
**完成时间**: {execution.completed_at.strftime('%Y-%m-%d %H:%M:%S') if execution.completed_at else 'N/A'}
**状态**: {execution.status.value}
**总Token数**: {execution.total_tokens_used}
**总费用**: ${execution.total_cost_usd:.4f}

---

"""

        for task in crew.tasks:
            agent = next((a for a in crew.agents if a.id == task.agent_id), None)
            te = task_executions.get(task.id)

            md += f"""## {task.name}

**执行Agent**: {agent.name if agent else '未分配'}
**任务描述**: {task.description}

### 输出结果

"""
            if te and te.status.value == "completed":
                output = te.output or "（无输出）"
                if self._needs_code_block(output):
                    md += self._wrap_in_code_block(output)
                else:
                    md += output
            elif te and te.status.value == "failed":
                md += f"**执行失败**: {te.error_message}"
            else:
                md += "（未执行）"

            md += "\n\n---\n\n"

        return md

    async def export_execution_json(self, execution_id: str) -> Dict[str, Any]:
        """导出执行结果为JSON"""
        result = await self.db.execute(
            select(Execution)
            .where(
                Execution.id == execution_id,
                Execution.user_id == self.user_id,
            )
            .options(
                selectinload(Execution.crew),
                selectinload(Execution.task_executions),
            )
        )
        execution = result.scalar_one_or_none()

        if not execution:
            raise ValueError("执行不存在")

        return {
            "execution_id": str(execution.id),
            "crew_id": str(execution.crew_id),
            "crew_name": execution.crew.name,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "total_tokens_used": execution.total_tokens_used,
            "total_cost_usd": execution.total_cost_usd,
            "task_results": [
                {
                    "task_id": str(te.task_id),
                    "status": te.status.value,
                    "output": te.output,
                    "error_message": te.error_message,
                    "tokens_used": te.tokens_used,
                    "cost_usd": te.cost_usd,
                }
                for te in execution.task_executions
            ],
        }
