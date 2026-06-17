"""DAG校验API — 执行前验证工作流结构"""

from collections import defaultdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DatabaseSession
from app.models.crew import Crew

router = APIRouter()


class CrewIdIn(BaseModel):
    crew_id: str


async def _load_crew(crew_id: str, db: DatabaseSession, current_user: CurrentUser) -> Crew:
    """加载 Crew 并做权限校验"""
    result = await db.execute(
        select(Crew)
        .where(Crew.id == crew_id, Crew.user_id == current_user.id)
        .options(selectinload(Crew.agents), selectinload(Crew.tasks))
    )
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return crew


def _validate_crew_structure(crew: Crew) -> dict:
    """校验 Crew 的 DAG 结构，返回 {errors, warnings, stats}"""
    agents = crew.agents or []
    tasks = crew.tasks or []
    errors: list[str] = []
    warnings: list[str] = []

    if not tasks:
        errors.append("工作流中没有任务")
    if not agents:
        errors.append("工作流中没有Agent")

    tasks_without_agent = [t.name for t in tasks if not t.agent_id]
    if tasks_without_agent:
        warnings.append(f"以下任务未分配Agent: {', '.join(tasks_without_agent)}")

    agent_ids = {a.id for a in agents}
    for t in tasks:
        if t.agent_id and t.agent_id not in agent_ids:
            errors.append(f"任务'{t.name}'的Agent引用无效")

    task_ids = {t.id for t in tasks}
    for t in tasks:
        for dep_id in (t.context_task_ids or []):
            if dep_id not in task_ids:
                errors.append(f"任务'{t.name}'的依赖引用无效: {dep_id[:8]}")
            if dep_id == t.id:
                errors.append(f"任务'{t.name}'依赖自己")

    # 环检测（Kahn 拓扑排序）
    if tasks:
        task_map = {t.id: t for t in tasks}
        in_degree: dict[str, int] = defaultdict(int)
        dependents: dict[str, list[str]] = defaultdict(list)
        for t in tasks:
            deps = [d for d in (t.context_task_ids or []) if d in task_map]
            in_degree[t.id] = len(deps)
            for dep_id in deps:
                dependents[dep_id].append(t.id)

        visited = 0
        queue = [t.id for t in tasks if in_degree[t.id] == 0]
        while queue:
            node = queue.pop(0)
            visited += 1
            for dep in dependents[node]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if visited < len(tasks):
            cycle_tasks = [t.name for t in tasks if in_degree[t.id] > 0]
            errors.append(f"检测到循环依赖: {' → '.join(cycle_tasks)}")

    return {
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "agents": len(agents),
            "tasks": len(tasks),
            "tasks_with_agent": len(tasks) - len(tasks_without_agent),
        },
    }


@router.get("/crew/{crew_id}/validate")
async def validate_workflow(crew_id: str, db: DatabaseSession, current_user: CurrentUser):
    """校验工作流的DAG结构，返回错误和警告"""
    crew = await _load_crew(crew_id, db, current_user)
    result = _validate_crew_structure(crew)
    return {
        "valid": len(result["errors"]) == 0,
        **result,
    }


@router.post("/validate-dag")
async def validate_dag(body: CrewIdIn, db: DatabaseSession, current_user: CurrentUser):
    """POST 方式校验 DAG 结构"""
    crew = await _load_crew(body.crew_id, db, current_user)
    result = _validate_crew_structure(crew)
    return {
        "is_valid": len(result["errors"]) == 0,
        **result,
    }


@router.post("/validate-crew")
async def validate_crew(body: CrewIdIn, db: DatabaseSession, current_user: CurrentUser):
    """校验工作流是否就绪（可执行）"""
    crew = await _load_crew(body.crew_id, db, current_user)
    result = _validate_crew_structure(crew)
    return {
        "is_ready": len(result["errors"]) == 0,
        **result,
    }


@router.post("/validate-execution")
async def validate_execution(body: CrewIdIn, db: DatabaseSession, current_user: CurrentUser):
    """校验工作流是否可执行"""
    crew = await _load_crew(body.crew_id, db, current_user)
    result = _validate_crew_structure(crew)
    return {
        "can_execute": len(result["errors"]) == 0,
        **result,
    }
