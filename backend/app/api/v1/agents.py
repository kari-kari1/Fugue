"""智能体（Agent）相关API"""


from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.models.agent import Agent
from app.models.crew import Crew
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate

router = APIRouter()


@router.get("/crew/{crew_id}", response_model=list[AgentResponse])
async def list_agents(
    crew_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取工作流下的所有智能体"""
    # 验证工作流归属
    result = await db.execute(
        select(Crew).where(Crew.id == crew_id, Crew.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="工作流不存在")

    result = await db.execute(
        select(Agent).where(Agent.crew_id == crew_id).order_by(Agent.created_at)
    )
    agents = result.scalars().all()

    return agents


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建智能体"""
    # 验证工作流归属
    result = await db.execute(
        select(Crew).where(Crew.id == str(agent_data.crew_id), Crew.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="工作流不存在")

    agent = Agent(**agent_data.model_dump())
    db.add(agent)
    await db.flush()
    await db.refresh(agent)

    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取智能体详情"""
    result = await db.execute(
        select(Agent)
        .join(Crew)
        .where(Agent.id == agent_id, Crew.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")

    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新智能体"""
    result = await db.execute(
        select(Agent)
        .join(Crew)
        .where(Agent.id == agent_id, Crew.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")

    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.flush()
    await db.refresh(agent)

    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除智能体"""
    result = await db.execute(
        select(Agent)
        .join(Crew)
        .where(Agent.id == agent_id, Crew.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")

    await db.delete(agent)
