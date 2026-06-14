"""工作流（Crew）相关API"""


from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DatabaseSession
from app.models.agent import Agent
from app.models.crew import Crew
from app.schemas.agent import AgentResponse
from app.schemas.crew import CrewCreate, CrewDetailResponse, CrewResponse, CrewUpdate
from app.schemas.task import TaskResponse

router = APIRouter()


def _crew_to_response(crew: Crew) -> CrewResponse:
    """将Crew模型转为CrewResponse（避免Pydantic from_attributes读到Base.metadata）"""
    return CrewResponse(
        id=crew.id,
        name=crew.name,
        description=crew.description,
        user_id=crew.user_id,
        process=crew.process.value if hasattr(crew.process, 'value') else crew.process,
        approval_mode=getattr(crew, 'approval_mode', 'semi_auto') or 'semi_auto',
        max_execution_time=crew.max_execution_time,
        cost_budget=crew.cost_budget,
        workspace_dir=crew.workspace_dir,
        metadata_=crew.metadata_ if crew.metadata_ is not None else {},
        project_memory=getattr(crew, 'project_memory', None),
        is_template=crew.is_template,
        template_category=crew.template_category,
        created_at=crew.created_at,
        updated_at=crew.updated_at,
    )


@router.get("/", response_model=list[CrewResponse])
async def list_crews(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_template: str | None = None,
):
    """获取工作流列表"""
    query = select(Crew).where(Crew.user_id == current_user.id)

    if is_template:
        query = query.where(Crew.is_template == is_template)

    query = query.offset(skip).limit(limit).order_by(Crew.created_at.desc())
    result = await db.execute(query)
    crews = result.scalars().all()

    return [_crew_to_response(c) for c in crews]


@router.post("/", response_model=CrewResponse, status_code=status.HTTP_201_CREATED)
async def create_crew(
    crew_data: CrewCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建工作流"""
    crew = Crew(
        **crew_data.model_dump(),
        user_id=current_user.id,
    )
    db.add(crew)
    await db.flush()

    # 自动创建默认记忆配置
    from app.models.memory import MemoryConfig
    mem_config = MemoryConfig(
        crew_id=crew.id,
        short_term_enabled=True,
        short_term_window=5,
        long_term_enabled=True,
        vector_store_type="chromadb",
        retrieval_strategy="similarity",
        top_k=3,
        auto_index_on_complete=True,
    )
    db.add(mem_config)
    await db.commit()
    await db.refresh(crew)

    return _crew_to_response(crew)


@router.get("/{crew_id}", response_model=CrewDetailResponse)
async def get_crew(
    crew_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取工作流详情"""
    result = await db.execute(
        select(Crew)
        .where(Crew.id == crew_id, Crew.user_id == current_user.id)
        .options(selectinload(Crew.agents), selectinload(Crew.tasks))
    )
    crew = result.scalar_one_or_none()

    if not crew:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在",
        )

    # 手动构造详细响应
    return CrewDetailResponse(
        **_crew_to_response(crew).model_dump(),
        agents=[AgentResponse.model_validate(a, from_attributes=True) for a in (crew.agents or [])],
        tasks=[TaskResponse.model_validate(t, from_attributes=True) for t in (crew.tasks or [])],
    )


@router.put("/{crew_id}", response_model=CrewResponse)
async def update_crew(
    crew_id: str,
    crew_data: CrewUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新工作流"""
    result = await db.execute(
        select(Crew).where(Crew.id == crew_id, Crew.user_id == current_user.id)
    )
    crew = result.scalar_one_or_none()

    if not crew:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在",
        )

    update_data = crew_data.model_dump(exclude_unset=True)
    # 处理metadata字段名映射（schema字段名metadata_，但API接受metadata）
    field_map = {"metadata": "metadata_"}
    for field, value in update_data.items():
        orm_field = field_map.get(field, field)
        setattr(crew, orm_field, value)

    await db.flush()
    await db.refresh(crew)

    return _crew_to_response(crew)


@router.delete("/{crew_id}", status_code=status.HTTP_200_OK)
async def delete_crew(
    crew_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除工作流（级联删除关联的agents、tasks、executions）"""
    result = await db.execute(
        select(Crew).where(Crew.id == crew_id, Crew.user_id == current_user.id)
    )
    crew = result.scalar_one_or_none()

    if not crew:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工作流不存在",
        )

    await db.delete(crew)
    await db.flush()
    await db.commit()
    return {"message": "工作流已删除"}


# ── 分层项目记忆 API ──────────────────────────────────────


from pydantic import BaseModel


class ProjectMemoryUpdate(BaseModel):
    """项目记忆更新请求"""
    project_memory: str = ""  # AGENTS.md 内容


class AgentExperienceUpdate(BaseModel):
    """Agent经验更新请求"""
    agent_experience: str = ""


@router.get("/{crew_id}/memory")
async def get_project_memory(
    crew_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取项目的 AGENTS.md 记忆内容"""
    result = await db.execute(
        select(Crew).where(Crew.id == crew_id, Crew.user_id == current_user.id)
    )
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(status_code=404, detail="工作流不存在")

    return {
        "crew_id": crew_id,
        "project_memory": crew.project_memory or "",
    }


@router.put("/{crew_id}/memory")
async def update_project_memory(
    crew_id: str,
    data: ProjectMemoryUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新项目的 AGENTS.md 记忆内容"""
    result = await db.execute(
        select(Crew).where(Crew.id == crew_id, Crew.user_id == current_user.id)
    )
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(status_code=404, detail="工作流不存在")

    crew.project_memory = data.project_memory
    await db.commit()

    return {
        "crew_id": crew_id,
        "project_memory": crew.project_memory or "",
        "message": "项目记忆已更新",
    }


@router.get("/{crew_id}/agents/{agent_id}/experience")
async def get_agent_experience(
    crew_id: str,
    agent_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取Agent经验记忆"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.crew_id == crew_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    return {
        "agent_id": agent_id,
        "agent_experience": agent.agent_experience or "",
    }


@router.put("/{crew_id}/agents/{agent_id}/experience")
async def update_agent_experience(
    crew_id: str,
    agent_id: str,
    data: AgentExperienceUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新Agent经验记忆"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.crew_id == crew_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent不存在")

    agent.agent_experience = data.agent_experience
    await db.commit()

    return {
        "agent_id": agent_id,
        "agent_experience": agent.agent_experience or "",
        "message": "Agent经验已更新",
    }
