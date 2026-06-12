"""模板相关API"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.deps import DatabaseSession, CurrentUser
from app.models.template import Template
from app.models.crew import Crew, ProcessType
from app.models.agent import Agent
from app.models.task import Task, OutputType
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
)
from app.services.template_marketplace import TemplateMarketplaceService

router = APIRouter()


class RatingRequest(BaseModel):
    """评分请求"""
    rating: int


class ForkRequest(BaseModel):
    """Fork请求"""
    name: Optional[str] = None


def _template_to_response(template: Template) -> TemplateResponse:
    """将Template模型转为TemplateResponse"""
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        icon=template.icon,
        difficulty=template.difficulty,
        agents_config=template.agents_config,
        tasks_config=template.tasks_config,
        connections_config=template.connections_config or [],
        process_type=template.process_type,
        tags=template.tags or [],
        use_count=template.use_count,
        rating=template.rating,
        is_builtin=template.is_builtin,
        user_id=template.user_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/categories", response_model=List[str])
async def list_categories(
    db: DatabaseSession,
):
    """获取模板分类列表"""
    result = await db.execute(
        select(distinct(Template.category)).where(Template.category.isnot(None))
    )
    categories = result.scalars().all()
    return [c for c in categories if c]


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    db: DatabaseSession,
    current_user: CurrentUser,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query(None, pattern="^(popular|newest|recommended)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取模板列表（内置模板 + 当前用户的自定义模板）"""
    query = select(Template).where(
        (Template.is_builtin == True) | (Template.user_id == current_user.id)
    )

    if category:
        query = query.where(Template.category == category)

    if search:
        query = query.where(
            (Template.name.ilike(f"%{search}%"))
            | (Template.description.ilike(f"%{search}%"))
        )

    # 排序
    if sort_by == "newest":
        query = query.order_by(Template.created_at.desc())
    elif sort_by == "recommended":
        query = query.order_by(Template.rating.desc(), Template.use_count.desc())
    else:  # popular (默认)
        query = query.order_by(Template.use_count.desc())

    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    templates = result.scalars().all()

    return TemplateListResponse(
        items=[_template_to_response(t) for t in templates],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取模板详情（内置模板或当前用户的自定义模板）"""
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    # 仅允许访问内置模板或当前用户的自定义模板
    if not template.is_builtin and template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该模板",
        )

    return _template_to_response(template)


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建自定义模板"""
    template = Template(
        **template_data.model_dump(),
        is_builtin=False,
        user_id=current_user.id,
    )
    db.add(template)
    await db.flush()
    await db.commit()
    await db.refresh(template)

    return _template_to_response(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新自定义模板（仅创建者可更新）"""
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    if template.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能修改内置模板",
        )

    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能修改自己的模板",
        )

    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.flush()
    await db.commit()
    await db.refresh(template)

    return _template_to_response(template)


# ─── 模板市场功能 ───


@router.get("/marketplace/popular")
async def get_popular_templates(
    db: DatabaseSession,
    limit: int = Query(10, ge=1, le=50),
    days: Optional[int] = Query(None, description="时间范围（天）"),
):
    """获取热门模板"""
    service = TemplateMarketplaceService(db)
    templates = await service.get_popular_templates(limit=limit, days=days)

    return {
        "templates": templates,
        "total": len(templates),
    }


@router.get("/marketplace/trending")
async def get_trending_templates(
    db: DatabaseSession,
    limit: int = Query(10, ge=1, le=50),
):
    """获取趋势模板"""
    service = TemplateMarketplaceService(db)
    templates = await service.get_trending_templates(limit=limit)

    return {
        "templates": templates,
        "total": len(templates),
    }


@router.get("/marketplace/recommended")
async def get_recommended_templates(
    db: DatabaseSession,
    current_user: CurrentUser,
    limit: int = Query(10, ge=1, le=50),
):
    """获取推荐模板"""
    service = TemplateMarketplaceService(db)
    templates = await service.get_recommended_templates(
        user_id=current_user.id,
        limit=limit,
    )

    return {
        "templates": templates,
        "total": len(templates),
    }


@router.post("/{template_id}/star")
async def star_template(
    template_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """收藏模板"""
    service = TemplateMarketplaceService(db)
    result = await service.star_template(template_id, current_user.id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/{template_id}/fork")
async def fork_template(
    template_id: str,
    request: ForkRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """Fork模板（复制为自己的模板）"""
    service = TemplateMarketplaceService(db)
    result = await service.fork_template(
        template_id=template_id,
        user_id=current_user.id,
        new_name=request.name,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/{template_id}/rate")
async def rate_template(
    template_id: str,
    request: RatingRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """评分模板"""
    service = TemplateMarketplaceService(db)
    result = await service.rate_template(
        template_id=template_id,
        user_id=current_user.id,
        rating=request.rating,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/{template_id}/toggle-public")
async def toggle_template_public(
    template_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """切换模板公开状态"""
    service = TemplateMarketplaceService(db)
    result = await service.toggle_public(template_id, current_user.id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/my")
async def list_my_templates(
    db: DatabaseSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取当前用户的模板列表"""
    service = TemplateMarketplaceService(db)
    result = await service.get_user_templates(
        user_id=current_user.id,
        page=page,
        limit=limit,
    )

    return result


@router.delete("/{template_id}", status_code=status.HTTP_200_OK)
async def delete_template(
    template_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除自定义模板（仅创建者可删除）"""
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    if template.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能删除内置模板",
        )

    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能删除自己的模板",
        )

    await db.delete(template)
    return {"message": "模板已删除"}


@router.post("/{template_id}/use", response_model=dict, status_code=status.HTTP_201_CREATED)
async def use_template(
    template_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """使用模板创建工作流（创建Crew、Agents、Tasks）"""
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    # 仅允许使用内置模板或当前用户的自定义模板
    if not template.is_builtin and template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权使用该模板",
        )

    # 1. 创建 Crew
    crew = Crew(
        name=template.name,
        description=template.description,
        user_id=current_user.id,
        process=ProcessType(template.process_type) if template.process_type else ProcessType.SEQUENTIAL,
        is_template="false",
        template_category=template.category,
    )
    db.add(crew)
    await db.flush()
    await db.refresh(crew)

    # 2. 创建 Agents，记录索引到ID的映射
    agent_index_to_id: dict[int, str] = {}
    for idx, agent_config in enumerate(template.agents_config):
        agent = Agent(
            crew_id=crew.id,
            name=agent_config["name"],
            role=agent_config["role"],
            goal=agent_config["goal"],
            backstory=agent_config.get("backstory", ""),
            llm_provider=agent_config.get("llm_provider", "openai"),
            llm_model=agent_config.get("llm_model", "gpt-4o"),
            tools_config=agent_config.get("tools", []),
        )
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        agent_index_to_id[idx] = agent.id

    # 3. 创建 Tasks，建立索引到ID映射，处理 depends_on -> context_task_ids
    task_index_to_id: dict[int, str] = {}
    for idx, task_config in enumerate(template.tasks_config):
        task = Task(
            crew_id=crew.id,
            agent_id=agent_index_to_id.get(task_config.get("agent_index", 0)),
            name=task_config["name"],
            description=task_config["description"],
            expected_output=task_config.get("expected_output", ""),
            output_type=OutputType(task_config.get("output_type", "text")),
            context_task_ids=[],  # 先创建，后面再更新依赖
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)
        task_index_to_id[idx] = task.id

    # 4. 更新 tasks 的 context_task_ids（将 depends_on 索引映射为实际 task ID）
    for idx, task_config in enumerate(template.tasks_config):
        depends_on = task_config.get("depends_on", [])
        if depends_on:
            task_id = task_index_to_id[idx]
            task_result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = task_result.scalar_one_or_none()
            if task:
                task.context_task_ids = [
                    task_index_to_id[dep_idx]
                    for dep_idx in depends_on
                    if dep_idx in task_index_to_id
                ]

    # 5. 递增模板使用次数
    template.use_count = (template.use_count or 0) + 1

    await db.flush()

    return {
        "message": "工作流创建成功",
        "crew_id": crew.id,
        "agents_count": len(template.agents_config),
        "tasks_count": len(template.tasks_config),
    }
