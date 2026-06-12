# Fugue Week 5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Week 5 features - authentication enhancement, template system, and UI polish for Fugue multi-agent workflow platform.

**Architecture:** Extend existing FastAPI + React stack with token refresh mechanism, template database and API, Apple-style UI components, and responsive design patterns.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, React 19, TypeScript, Zustand, TanStack Query, Tailwind CSS, Lucide React

---

## File Structure

### Backend Files (Create)
- `backend/app/models/template.py` - Template SQLAlchemy model
- `backend/app/schemas/template.py` - Template Pydantic schemas
- `backend/app/api/v1/templates.py` - Template CRUD API endpoints
- `backend/app/services/template_seeder.py` - Predefined template data seeder
- `backend/alembic/versions/add_templates_table.py` - Database migration

### Backend Files (Modify)
- `backend/app/api/v1/__init__.py` - Register templates router
- `backend/app/api/v1/auth.py` - Add token refresh endpoint
- `backend/app/core/security.py` - Add token expiry tracking
- `backend/app/schemas/user.py` - Add token expiry to response

### Frontend Files (Create)
- `frontend/src/pages/Templates.tsx` - Template marketplace page
- `frontend/src/components/templates/TemplateCard.tsx` - Template card component
- `frontend/src/components/templates/TemplateDetailModal.tsx` - Template preview modal
- `frontend/src/components/templates/TemplateSkeletonGrid.tsx` - Loading skeleton
- `frontend/src/components/ui/AppleButton.tsx` - Apple-style button
- `frontend/src/components/ui/AppleCard.tsx` - Apple-style card
- `frontend/src/components/ui/Skeleton.tsx` - Skeleton loading component
- `frontend/src/components/ui/EmptyState.tsx` - Empty state component
- `frontend/src/components/layout/MobileMenu.tsx` - Mobile navigation menu
- `frontend/src/api/templates.ts` - Template API client
- `frontend/src/stores/templateStore.ts` - Template state management
- `frontend/src/lib/responsive.ts` - Responsive hooks

### Frontend Files (Modify)
- `frontend/src/stores/authStore.ts` - Add token refresh logic
- `frontend/src/components/ErrorBoundary.tsx` - Enhance error boundary
- `frontend/src/App.tsx` - Add templates route
- `frontend/src/pages/Dashboard.tsx` - Add responsive design + empty state
- `frontend/src/api/client.ts` - Add error interceptor

---

## Task 1: Backend - Create Template Model

**Files:**
- Create: `backend/app/models/template.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create Template model file**

```python
# backend/app/models/template.py

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, JSON, Integer, Float, Boolean, DateTime
from sqlalchemy.sql import func

from app.models.base import Base


class Template(Base):
    """工作流模板模型"""
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    category = Column(String(50), index=True, comment="分类：research/code/analysis/document/literature")
    icon = Column(String(50), comment="图标标识（emoji）")
    difficulty = Column(String(20), comment="难度：beginner/intermediate/advanced")

    # 模板配置（JSON格式存储工作流结构）
    agents_config = Column(JSON, nullable=False, comment="Agent 配置列表")
    tasks_config = Column(JSON, nullable=False, comment="Task 配置列表")
    process_type = Column(String(20), default="sequential", comment="执行模式：sequential/parallel")

    # 元数据
    tags = Column(JSON, default=list, comment="标签列表")
    use_count = Column(Integer, default=0, comment="使用次数")
    rating = Column(Float, default=4.8, comment="评分（1-5）")
    is_builtin = Column(Boolean, default=True, comment="是否内置模板")
    user_id = Column(String(36), nullable=True, index=True, comment="创建者用户ID（用户自定义模板）")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"<Template {self.name}>"
```

- [ ] **Step 2: Update models __init__.py to export Template**

```python
# backend/app/models/__init__.py

from app.models.base import Base
from app.models.user import User
from app.models.crew import Crew
from app.models.agent import Agent
from app.models.task import Task
from app.models.execution import Execution, TaskExecution, ExecutionTrace
from app.models.llm_provider import LLMProviderConfig
from app.models.template import Template

__all__ = [
    "Base",
    "User",
    "Crew",
    "Agent",
    "Task",
    "Execution",
    "TaskExecution",
    "ExecutionTrace",
    "LLMProviderConfig",
    "Template",
]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/template.py backend/app/models/__init__.py
git commit -m "feat(models): add Template model for workflow templates"
```

---

## Task 2: Backend - Create Template Schemas

**Files:**
- Create: `backend/app/schemas/template.py`

- [ ] **Step 1: Create Pydantic schemas for Template**

```python
# backend/app/schemas/template.py

from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str
    role: str
    goal: str
    backstory: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    tools: List[str] = []


class TaskConfig(BaseModel):
    """Task 配置"""
    name: str
    description: str
    expected_output: str
    output_type: str = "text"
    agent_index: int  # 索引 agents_config 中的 Agent
    depends_on: List[int] = []  # 依赖的 task 索引


class TemplateBase(BaseModel):
    """模板基础字段"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(research|code|analysis|document|literature)$")
    icon: str = "📋"
    difficulty: str = Field("intermediate", pattern="^(beginner|intermediate|advanced)$")
    agents_config: List[AgentConfig]
    tasks_config: List[TaskConfig]
    process_type: str = Field("sequential", pattern="^(sequential|parallel)$")
    tags: List[str] = []


class TemplateCreate(TemplateBase):
    """创建自定义模板"""
    pass


class TemplateUpdate(BaseModel):
    """更新模板（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, pattern="^(research|code|analysis|document|literature)$")
    icon: Optional[str] = None
    difficulty: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    agents_config: Optional[List[AgentConfig]] = None
    tasks_config: Optional[List[TaskConfig]] = None
    process_type: Optional[str] = Field(None, pattern="^(sequential|parallel)$")
    tags: Optional[List[str]] = None


class TemplateResponse(TemplateBase):
    """模板响应"""
    id: str
    use_count: int
    rating: float
    is_builtin: bool
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    items: List[TemplateResponse]
    total: int
    page: int
    limit: int


class TemplateCategoryResponse(BaseModel):
    """模板分类响应"""
    categories: List[Dict[str, Any]]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/template.py
git commit -m "feat(schemas): add Template Pydantic schemas"
```

---

## Task 3: Backend - Create Database Migration

**Files:**
- Create: `backend/alembic/versions/add_templates_table.py`

- [ ] **Step 1: Generate migration**

Run:
```bash
cd backend
alembic revision --autogenerate -m "add templates table"
```

- [ ] **Step 2: Verify migration content**

The migration should create the `templates` table with all columns defined in the model. If autogenerate doesn't work, create manually:

```python
# backend/alembic/versions/add_templates_table.py

"""add templates table

Revision ID: xxx
Revises: [previous_revision]
Create Date: 2026-06-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'xxx'  # Will be auto-filled
down_revision: Union[str, None] = None  # Will be auto-filled
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('difficulty', sa.String(20), nullable=True),
        sa.Column('agents_config', sa.JSON(), nullable=False),
        sa.Column('tasks_config', sa.JSON(), nullable=False),
        sa.Column('process_type', sa.String(20), server_default='sequential'),
        sa.Column('tags', sa.JSON(), server_default='[]'),
        sa.Column('use_count', sa.Integer(), server_default='0'),
        sa.Column('rating', sa.Float(), server_default='4.8'),
        sa.Column('is_builtin', sa.Boolean(), server_default='true'),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_templates_category', 'templates', ['category'])
    op.create_index('ix_templates_user_id', 'templates', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_templates_user_id')
    op.drop_index('ix_templates_category')
    op.drop_table('templates')
```

- [ ] **Step 3: Run migration**

```bash
cd backend
alembic upgrade head
```

Expected output: `Running upgrade ... -> xxx, add templates table`

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/add_templates_table.py
git commit -m "feat(db): add templates table migration"
```

---

## Task 4: Backend - Create Template API Endpoints

**Files:**
- Create: `backend/app/api/v1/templates.py`
- Modify: `backend/app/api/v1/__init__.py`

- [ ] **Step 1: Create templates API router**

```python
# backend/app/api/v1/templates.py

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.api.deps import DatabaseSession, CurrentUser
from app.models.template import Template
from app.models.crew import Crew
from app.models.agent import Agent
from app.models.task import Task
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
)

router = APIRouter()


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    db: DatabaseSession,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("popular", pattern="^(popular|newest|recommended)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取模板列表"""
    query = select(Template)

    # 分类筛选
    if category:
        query = query.where(Template.category == category)

    # 搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Template.name.ilike(search_pattern)) |
            (Template.description.ilike(search_pattern))
        )

    # 排序
    if sort_by == "popular":
        query = query.order_by(Template.use_count.desc())
    elif sort_by == "newest":
        query = query.order_by(Template.created_at.desc())
    else:  # recommended
        query = query.order_by(Template.rating.desc(), Template.use_count.desc())

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    templates = result.scalars().all()

    return TemplateListResponse(
        items=[TemplateResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/categories")
async def list_categories(db: DatabaseSession):
    """获取模板分类列表"""
    result = await db.execute(
        select(Template.category, func.count(Template.id))
        .group_by(Template.category)
    )
    categories = [
        {"id": row[0], "count": row[1]}
        for row in result.all()
        if row[0] is not None
    ]
    return {"categories": categories}


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, db: DatabaseSession):
    """获取模板详情"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return TemplateResponse.model_validate(template)


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建自定义模板"""
    template = Template(
        **template_data.model_dump(),
        user_id=current_user.id,
        is_builtin=False,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)

    return TemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新自定义模板"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此模板")

    # 更新字段
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.flush()
    await db.refresh(template)

    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除自定义模板"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if template.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此模板")

    await db.delete(template)


@router.post("/{template_id}/use", response_model=dict)
async def use_template(
    template_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """使用模板创建工作流"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 创建工作流
    crew = Crew(
        name=f"{template.name} (基于模板)",
        description=template.description,
        user_id=current_user.id,
        process=template.process_type,
    )
    db.add(crew)
    await db.flush()

    # 创建 Agent
    agent_map = {}  # index -> agent_id
    for idx, agent_config in enumerate(template.agents_config):
        agent = Agent(
            crew_id=crew.id,
            name=agent_config["name"],
            role=agent_config["role"],
            goal=agent_config["goal"],
            backstory=agent_config["backstory"],
            llm_provider=agent_config.get("llm_provider", "openai"),
            llm_model=agent_config.get("llm_model", "gpt-4o"),
            tools_config=agent_config.get("tools", []),
        )
        db.add(agent)
        await db.flush()
        agent_map[idx] = agent.id

    # 创建 Task
    task_map = {}  # index -> task_id
    for idx, task_config in enumerate(template.tasks_config):
        # 解析依赖
        context_task_ids = []
        for dep_idx in task_config.get("depends_on", []):
            if dep_idx in task_map:
                context_task_ids.append(task_map[dep_idx])

        task = Task(
            crew_id=crew.id,
            agent_id=agent_map[task_config["agent_index"]],
            name=task_config["name"],
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            output_type=task_config.get("output_type", "text"),
            context_task_ids=context_task_ids,
        )
        db.add(task)
        await db.flush()
        task_map[idx] = task.id

    # 更新使用次数
    template.use_count += 1

    await db.commit()

    return {
        "message": "工作流创建成功",
        "crew_id": crew.id,
        "crew_name": crew.name,
    }
```

- [ ] **Step 2: Register templates router**

```python
# backend/app/api/v1/__init__.py

from fastapi import APIRouter

from app.api.v1 import auth, crews, agents, tasks, executions, demo, validation, templates

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(crews.router, prefix="/crews", tags=["工作流"])
api_router.include_router(agents.router, prefix="/agents", tags=["智能体"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务"])
api_router.include_router(executions.router, prefix="/executions", tags=["执行"])
api_router.include_router(demo.router, prefix="/demo", tags=["演示"])
api_router.include_router(validation.router, prefix="/validation", tags=["校验"])
api_router.include_router(templates.router, prefix="/templates", tags=["模板"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/templates.py backend/app/api/v1/__init__.py
git commit -m "feat(api): add template CRUD endpoints"
```

---

## Task 5: Backend - Create Template Seeder

**Files:**
- Create: `backend/app/services/template_seeder.py`
- Modify: `backend/app/api/v1/demo.py`

- [ ] **Step 1: Create template seeder service**

```python
# backend/app/services/template_seeder.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template


PREDEFINED_TEMPLATES = [
    {
        "name": "行业研究报告生成",
        "description": "自动生成专业的行业研究报告，包含数据收集、分析和报告撰写三个阶段。适合需要快速了解行业动态的研究人员和分析师。",
        "category": "research",
        "icon": "📊",
        "difficulty": "intermediate",
        "tags": ["研究报告", "行业分析", "数据收集", "商业分析"],
        "process_type": "sequential",
        "agents_config": [
            {
                "name": "行业研究员",
                "role": "资深行业研究员",
                "goal": "收集和分析目标行业的最新数据和趋势",
                "backstory": "你是一位在行业研究领域有10年经验的资深研究员，擅长数据收集和趋势分析，能够从海量信息中提取关键洞察。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["web_search", "file_read"]
            },
            {
                "name": "报告写手",
                "role": "专业技术内容写手",
                "goal": "基于研究结果撰写清晰、专业的行业研究报告",
                "backstory": "你是一位资深技术写手，擅长将复杂的数据和分析转化为通俗易懂、结构清晰的报告，曾为多家知名咨询公司撰写研究报告。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["file_write"]
            }
        ],
        "tasks_config": [
            {
                "name": "数据收集",
                "description": "收集目标行业的市场规模、增长趋势、主要玩家、技术发展方向等数据。重点关注最近6个月的最新动态。",
                "expected_output": "结构化的行业数据报告，包含市场规模、增长率、主要玩家、技术趋势等关键指标",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": []
            },
            {
                "name": "数据分析",
                "description": "分析收集到的数据，提取关键洞察和趋势，识别行业机会和挑战。",
                "expected_output": "数据分析报告，包含关键指标解读、趋势分析、机会识别和风险提示",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [0]
            },
            {
                "name": "报告撰写",
                "description": "基于数据分析结果，撰写完整的行业研究报告。报告应包含执行摘要、市场概况、竞争格局、技术趋势、机会与挑战、结论建议等章节。",
                "expected_output": "一篇结构完整、数据详实的行业研究报告（2000-3000字）",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1]
            }
        ],
    },
    {
        "name": "代码审查助手",
        "description": "自动审查代码质量，发现潜在问题并提供优化建议。支持多种编程语言，帮助提升代码质量和可维护性。",
        "category": "code",
        "icon": "🔍",
        "difficulty": "beginner",
        "tags": ["代码审查", "代码质量", "最佳实践", "重构建议"],
        "process_type": "sequential",
        "agents_config": [
            {
                "name": "代码审查员",
                "role": "高级代码审查工程师",
                "goal": "全面审查代码质量，发现潜在问题和改进空间",
                "backstory": "你是一位有15年经验的高级软件工程师，精通多种编程语言和设计模式，对代码质量有极高的要求。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["file_read"]
            },
            {
                "name": "优化建议员",
                "role": "代码优化专家",
                "goal": "基于审查结果提供具体的优化建议和重构方案",
                "backstory": "你是一位代码优化专家，擅长将复杂的代码重构为简洁、高效、可维护的版本，同时保持功能不变。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["file_write"]
            }
        ],
        "tasks_config": [
            {
                "name": "代码审查",
                "description": "全面审查代码，检查：1) 代码风格和规范 2) 潜在的bug和错误 3) 性能问题 4) 安全漏洞 5) 可维护性问题",
                "expected_output": "详细的代码审查报告，列出所有发现的问题及其严重程度",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": []
            },
            {
                "name": "优化建议",
                "description": "基于审查结果，为每个问题提供具体的优化建议，包括：1) 问题描述 2) 影响分析 3) 解决方案 4) 重构代码示例",
                "expected_output": "完整的优化建议文档，包含问题清单和重构方案",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [0]
            }
        ],
    },
    {
        "name": "竞品分析报告",
        "description": "深度分析竞争对手的产品、策略和市场表现，帮助制定竞争策略。适合产品经理、市场分析师和创业者。",
        "category": "analysis",
        "icon": "📈",
        "difficulty": "advanced",
        "tags": ["竞品分析", "市场研究", "竞争策略", "产品分析"],
        "process_type": "sequential",
        "agents_config": [
            {
                "name": "市场研究员",
                "role": "资深市场研究分析师",
                "goal": "收集竞品的公开信息和市场数据",
                "backstory": "你是一位资深市场研究分析师，擅长从公开渠道收集和整理竞品信息，包括产品功能、定价策略、用户评价等。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["web_search", "file_read"]
            },
            {
                "name": "产品分析师",
                "role": "高级产品分析师",
                "goal": "分析竞品的产品策略和用户体验",
                "backstory": "你是一位高级产品分析师，擅长从用户视角分析产品的优劣势，能够洞察产品背后的战略意图。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["file_read"]
            },
            {
                "name": "报告写手",
                "role": "商业分析报告专家",
                "goal": "整合分析结果，撰写专业的竞品分析报告",
                "backstory": "你是一位商业分析报告专家，擅长将复杂的分析结果转化为清晰、 actionable 的商业洞察。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["file_write"]
            }
        ],
        "tasks_config": [
            {
                "name": "竞品信息收集",
                "description": "收集主要竞品的基本信息：公司背景、产品功能、定价策略、用户规模、融资情况等。",
                "expected_output": "竞品信息汇总表，包含各竞品的核心数据",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": []
            },
            {
                "name": "产品对比分析",
                "description": "从功能、用户体验、技术架构、商业模式等维度对比分析各竞品，识别差异化优势和劣势。",
                "expected_output": "产品对比分析矩阵，包含各维度的详细对比",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [0]
            },
            {
                "name": "竞争策略建议",
                "description": "基于分析结果，提出针对性的竞争策略建议，包括差异化定位、功能优先级、市场进入策略等。",
                "expected_output": "竞争策略建议书，包含短期和长期策略建议",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1]
            },
            {
                "name": "报告撰写",
                "description": "整合所有分析结果，撰写完整的竞品分析报告，包含市场概况、竞品详情、对比分析、策略建议等章节。",
                "expected_output": "专业的竞品分析报告（3000-4000字）",
                "output_type": "text",
                "agent_index": 2,
                "depends_on": [2]
            }
        ],
    },
    {
        "name": "产品需求文档",
        "description": "帮助产品经理快速生成专业的产品需求文档（PRD），包含需求分析、功能设计、技术方案等内容。",
        "category": "document",
        "icon": "📄",
        "difficulty": "intermediate",
        "tags": ["PRD", "需求文档", "产品设计", "功能规格"],
        "process_type": "sequential",
        "agents_config": [
            {
                "name": "需求分析师",
                "role": "资深需求分析师",
                "goal": "分析和整理产品需求，识别核心功能和优先级",
                "backstory": "你是一位资深需求分析师，擅长从用户反馈和业务目标中提取核心需求，并将其转化为清晰的功能规格。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["file_read"]
            },
            {
                "name": "文档写手",
                "role": "技术文档专家",
                "goal": "撰写专业、清晰的产品需求文档",
                "backstory": "你是一位技术文档专家，擅长将复杂的需求和技术方案转化为易于理解的文档，曾为多家科技公司撰写PRD。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["file_write"]
            }
        ],
        "tasks_config": [
            {
                "name": "需求分析",
                "description": "分析产品需求，识别：1) 核心功能 2) 用户故事 3) 验收标准 4) 优先级排序 5) 依赖关系",
                "expected_output": "需求分析文档，包含功能清单、用户故事和优先级排序",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": []
            },
            {
                "name": "技术方案设计",
                "description": "基于需求分析，设计技术实现方案，包括：1) 系统架构 2) 数据模型 3) API设计 4) 技术选型",
                "expected_output": "技术方案设计文档",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [0]
            },
            {
                "name": "PRD撰写",
                "description": "整合需求分析和技术方案，撰写完整的产品需求文档，包含：项目背景、需求概述、功能规格、技术方案、里程碑计划等。",
                "expected_output": "专业的产品需求文档（3000-5000字）",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1]
            }
        ],
    },
    {
        "name": "文献综述生成",
        "description": "帮助研究人员快速生成学术文献综述，包含文献检索、整理和综述撰写。适合学术研究和论文写作。",
        "category": "literature",
        "icon": "📚",
        "difficulty": "advanced",
        "tags": ["文献综述", "学术研究", "论文写作", "文献分析"],
        "process_type": "sequential",
        "agents_config": [
            {
                "name": "文献检索员",
                "role": "学术文献检索专家",
                "goal": "检索和收集相关领域的学术文献",
                "backstory": "你是一位学术文献检索专家，精通各种学术数据库的使用，能够快速找到高质量的相关文献。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["web_search", "file_read"]
            },
            {
                "name": "综述写手",
                "role": "学术写作专家",
                "goal": "基于文献分析结果撰写高质量的文献综述",
                "backstory": "你是一位学术写作专家，曾在顶级期刊发表多篇论文，擅长将复杂的文献综合为逻辑清晰的综述文章。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": ["file_write"]
            }
        ],
        "tasks_config": [
            {
                "name": "文献检索",
                "description": "检索相关领域的学术文献，重点关注：1) 近5年的高引用论文 2) 综述类文章 3) 代表性研究 4) 最新进展",
                "expected_output": "文献清单，包含每篇文献的基本信息、研究内容和重要性说明",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": []
            },
            {
                "name": "文献分析",
                "description": "分析收集的文献，识别：1) 研究主题分类 2) 主要观点和结论 3) 研究方法 4) 研究趋势 5) 研究空白",
                "expected_output": "文献分析报告，包含主题分类和关键发现",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [0]
            },
            {
                "name": "综述撰写",
                "description": "基于文献分析结果，撰写文献综述，包含：引言、研究现状、主题分析、研究趋势、结论与展望等章节。",
                "expected_output": "高质量的文献综述（3000-5000字）",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1]
            }
        ],
    },
]


async def seed_templates(db: AsyncSession) -> dict:
    """初始化预设模板数据"""
    # 检查是否已有预设模板
    result = await db.execute(
        select(Template).where(Template.is_builtin == True).limit(1)
    )
    if result.scalar_one_or_none():
        return {"message": "预设模板已存在，跳过初始化", "count": 0}

    # 创建预设模板
    count = 0
    for template_data in PREDEFINED_TEMPLATES:
        template = Template(**template_data, is_builtin=True)
        db.add(template)
        count += 1

    await db.commit()

    return {"message": f"成功初始化 {count} 个预设模板", "count": count}
```

- [ ] **Step 2: Add seed endpoint to demo API**

```python
# Add to backend/app/api/v1/demo.py

from app.services.template_seeder import seed_templates


@router.post("/seed-templates", status_code=status.HTTP_201_CREATED)
async def seed_templates_endpoint(db: DatabaseSession, current_user: CurrentUser):
    """初始化预设模板数据"""
    result = await seed_templates(db)
    return result
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/template_seeder.py backend/app/api/v1/demo.py
git commit -m "feat(seeder): add predefined template seeder with 5 templates"
```

---

## Task 6: Backend - Add Token Refresh Endpoint

**Files:**
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/core/security.py`
- Modify: `backend/app/schemas/user.py`

- [ ] **Step 1: Update Token schema to include expiry**

```python
# Add to backend/app/schemas/user.py

class Token(BaseModel):
    """JWT Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token 有效期（秒）")


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str
    exp: int
```

- [ ] **Step 2: Add get_token_expiry function**

```python
# Add to backend/app/core/security.py

from datetime import datetime


def get_token_expiry(token: str) -> Optional[datetime]:
    """获取 Token 的过期时间"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
        return None
    except JWTError:
        return None


def get_token_remaining_seconds(token: str) -> int:
    """获取 Token 剩余有效时间（秒）"""
    exp_time = get_token_expiry(token)
    if not exp_time:
        return 0
    remaining = (exp_time - datetime.utcnow()).total_seconds()
    return max(0, int(remaining))
```

- [ ] **Step 3: Add refresh endpoint**

```python
# Add to backend/app/api/v1/auth.py

from app.core.security import get_token_remaining_seconds


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: CurrentUser):
    """刷新 Token"""
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/token-info")
async def get_token_info(current_user: CurrentUser, authorization: str = Header(...)):
    """获取 Token 信息（包括剩余时间）"""
    token = authorization.replace("Bearer ", "")
    remaining = get_token_remaining_seconds(token)
    return {
        "user_id": str(current_user.id),
        "expires_in": remaining,
        "is_expiring_soon": remaining < 300,  # 5分钟内过期
    }
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/auth.py backend/app/core/security.py backend/app/schemas/user.py
git commit -m "feat(auth): add token refresh and token info endpoints"
```

---

## Task 7: Frontend - Create Template API Client

**Files:**
- Create: `frontend/src/api/templates.ts`

- [ ] **Step 1: Create templates API client**

```typescript
// frontend/src/api/templates.ts

import apiClient from './client';
import type { Crew } from '../types';

export interface Template {
  id: string;
  name: string;
  description: string | null;
  category: string;
  icon: string;
  difficulty: string;
  agents_config: AgentConfig[];
  tasks_config: TaskConfig[];
  process_type: string;
  tags: string[];
  use_count: number;
  rating: number;
  is_builtin: boolean;
  user_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AgentConfig {
  name: string;
  role: string;
  goal: string;
  backstory: string;
  llm_provider: string;
  llm_model: string;
  tools: string[];
}

export interface TaskConfig {
  name: string;
  description: string;
  expected_output: string;
  output_type: string;
  agent_index: number;
  depends_on: number[];
}

export interface TemplateListResponse {
  items: Template[];
  total: number;
  page: number;
  limit: number;
}

export interface TemplateCreateData {
  name: string;
  description?: string;
  category: string;
  icon?: string;
  difficulty?: string;
  agents_config: AgentConfig[];
  tasks_config: TaskConfig[];
  process_type?: string;
  tags?: string[];
}

export const templatesApi = {
  // 获取模板列表
  list: async (params?: {
    category?: string;
    search?: string;
    sort_by?: string;
    page?: number;
    limit?: number;
  }): Promise<TemplateListResponse> => {
    const response = await apiClient.get('/templates', { params });
    return response.data;
  },

  // 获取模板详情
  get: async (id: string): Promise<Template> => {
    const response = await apiClient.get(`/templates/${id}`);
    return response.data;
  },

  // 创建自定义模板
  create: async (data: TemplateCreateData): Promise<Template> => {
    const response = await apiClient.post('/templates', data);
    return response.data;
  },

  // 更新模板
  update: async (id: string, data: Partial<TemplateCreateData>): Promise<Template> => {
    const response = await apiClient.put(`/templates/${id}`, data);
    return response.data;
  },

  // 删除模板
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/templates/${id}`);
  },

  // 使用模板创建工作流
  use: async (id: string): Promise<{ message: string; crew_id: string; crew_name: string }> => {
    const response = await apiClient.post(`/templates/${id}/use`);
    return response.data;
  },

  // 获取分类列表
  categories: async (): Promise<{ categories: Array<{ id: string; count: number }> }> => {
    const response = await apiClient.get('/templates/categories');
    return response.data;
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/templates.ts
git commit -m "feat(api): add templates API client"
```

---

## Task 8: Frontend - Create UI Components

**Files:**
- Create: `frontend/src/components/ui/AppleButton.tsx`
- Create: `frontend/src/components/ui/AppleCard.tsx`
- Create: `frontend/src/components/ui/Skeleton.tsx`
- Create: `frontend/src/components/ui/EmptyState.tsx`

- [ ] **Step 1: Create AppleButton component**

```tsx
// frontend/src/components/ui/AppleButton.tsx

import React from 'react';
import { Loader2 } from 'lucide-react';

interface AppleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const AppleButton: React.FC<AppleButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const baseClasses = "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2";

  const variantClasses = {
    primary: "bg-[#007AFF] text-white hover:bg-[#0056CC] shadow-md hover:shadow-lg focus:ring-blue-500",
    secondary: "bg-[#F2F2F7] text-[#1C1C1E] hover:bg-[#E5E5EA] focus:ring-gray-500",
    ghost: "bg-transparent text-[#007AFF] hover:bg-[#F2F2F7] focus:ring-blue-500",
    danger: "bg-[#FF3B30] text-white hover:bg-[#D63027] shadow-md hover:shadow-lg focus:ring-red-500",
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2.5 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className} ${
        disabled || isLoading ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
      {children}
    </button>
  );
};
```

- [ ] **Step 2: Create AppleCard component**

```tsx
// frontend/src/components/ui/AppleCard.tsx

import React from 'react';

interface AppleCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export const AppleCard: React.FC<AppleCardProps> = ({
  children,
  className = '',
  hover = true,
  onClick,
}) => {
  return (
    <div
      className={`
        bg-white rounded-2xl shadow-md
        ${hover ? 'hover:shadow-lg transition-shadow duration-250' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        overflow-hidden ${className}
      `}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export const AppleCardHeader: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`px-6 py-4 border-b border-gray-100 ${className}`}>
    {children}
  </div>
);

export const AppleCardContent: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`px-6 py-4 ${className}`}>
    {children}
  </div>
);

export const AppleCardFooter: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`px-6 py-4 bg-gray-50 border-t border-gray-100 ${className}`}>
    {children}
  </div>
);
```

- [ ] **Step 3: Create Skeleton component**

```tsx
// frontend/src/components/ui/Skeleton.tsx

import React from 'react';

interface SkeletonProps {
  className?: string;
  count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`animate-pulse bg-gray-200 rounded ${className}`}
        />
      ))}
    </>
  );
};
```

- [ ] **Step 4: Create EmptyState component**

```tsx
// frontend/src/components/ui/EmptyState.tsx

import React from 'react';
import { AppleButton } from './AppleButton';

interface EmptyStateProps {
  icon: string;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  secondaryAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="text-6xl mb-6">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-center max-w-md mb-8">{description}</p>
      <div className="flex gap-3">
        {action && (
          <AppleButton onClick={action.onClick}>
            {action.label}
          </AppleButton>
        )}
        {secondaryAction && (
          <AppleButton variant="secondary" onClick={secondaryAction.onClick}>
            {secondaryAction.label}
          </AppleButton>
        )}
      </div>
    </div>
  );
};
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ui/AppleButton.tsx frontend/src/components/ui/AppleCard.tsx frontend/src/components/ui/Skeleton.tsx frontend/src/components/ui/EmptyState.tsx
git commit -m "feat(ui): add Apple-style UI components (Button, Card, Skeleton, EmptyState)"
```

---

## Task 9: Frontend - Create Template Components

**Files:**
- Create: `frontend/src/components/templates/TemplateCard.tsx`
- Create: `frontend/src/components/templates/TemplateDetailModal.tsx`
- Create: `frontend/src/components/templates/TemplateSkeletonGrid.tsx`

- [ ] **Step 1: Create TemplateCard component**

```tsx
// frontend/src/components/templates/TemplateCard.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Users, ArrowRight } from 'lucide-react';
import { templatesApi, type Template } from '../../api/templates';
import toast from 'react-hot-toast';

interface TemplateCardProps {
  template: Template;
  onClick: () => void;
}

export const TemplateCard: React.FC<TemplateCardProps> = ({ template, onClick }) => {
  const navigate = useNavigate();

  const handleUseTemplate = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const result = await templatesApi.use(template.id);
      toast.success('工作流创建成功');
      navigate(`/crew/${result.crew_id}`);
    } catch (error) {
      toast.error('创建失败');
    }
  };

  const difficultyLabel = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级',
  }[template.difficulty] || '中级';

  const difficultyColor = {
    beginner: 'bg-green-100 text-green-700',
    intermediate: 'bg-yellow-100 text-yellow-700',
    advanced: 'bg-red-100 text-red-700',
  }[template.difficulty] || 'bg-yellow-100 text-yellow-700';

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-2xl shadow-md hover:shadow-lg transition-all duration-250 cursor-pointer overflow-hidden group"
    >
      {/* 卡片头部 */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center text-2xl">
            {template.icon}
          </div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${difficultyColor}`}>
            {difficultyLabel}
          </span>
        </div>

        <h3 className="text-lg font-semibold text-gray-900 mb-2">{template.name}</h3>
        <p className="text-sm text-gray-600 line-clamp-2 mb-4">{template.description}</p>

        {/* 标签 */}
        <div className="flex flex-wrap gap-2 mb-4">
          {template.tags?.slice(0, 3).map((tag) => (
            <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 rounded-md text-xs">
              {tag}
            </span>
          ))}
        </div>

        {/* 统计信息 */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            {template.use_count.toLocaleString()} 次使用
          </span>
          <span className="flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-500" />
            {template.rating.toFixed(1)}
          </span>
        </div>
      </div>

      {/* 卡片底部 */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
        <button
          onClick={handleUseTemplate}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors group-hover:bg-blue-600"
        >
          使用此模板
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Create TemplateDetailModal component**

```tsx
// frontend/src/components/templates/TemplateDetailModal.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Users, Star, Clock, GitBranch } from 'lucide-react';
import { templatesApi, type Template } from '../../api/templates';
import { AppleButton } from '../ui/AppleButton';
import toast from 'react-hot-toast';

interface TemplateDetailModalProps {
  template: Template;
  onClose: () => void;
}

export const TemplateDetailModal: React.FC<TemplateDetailModalProps> = ({
  template,
  onClose,
}) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = React.useState(false);

  const handleUseTemplate = async () => {
    setIsLoading(true);
    try {
      const result = await templatesApi.use(template.id);
      toast.success('工作流创建成功');
      navigate(`/crew/${result.crew_id}`);
    } catch (error) {
      toast.error('创建失败');
    } finally {
      setIsLoading(false);
    }
  };

  const difficultyLabel = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级',
  }[template.difficulty] || '中级';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        {/* 头部 */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center text-xl">
              {template.icon}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{template.name}</h2>
              <p className="text-sm text-gray-500">{template.category}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6">
          {/* 描述 */}
          <p className="text-gray-700 mb-6">{template.description}</p>

          {/* 元信息 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="flex items-center gap-2 text-sm">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">{template.use_count.toLocaleString()} 次使用</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Star className="w-4 h-4 text-yellow-500" />
              <span className="text-gray-600">{template.rating.toFixed(1)} 分</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Clock className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">{difficultyLabel}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <GitBranch className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">{template.process_type === 'sequential' ? '顺序执行' : '并行执行'}</span>
            </div>
          </div>

          {/* 标签 */}
          <div className="flex flex-wrap gap-2 mb-6">
            {template.tags?.map((tag) => (
              <span key={tag} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                {tag}
              </span>
            ))}
          </div>

          {/* 工作流预览 */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">工作流结构</h3>
            <div className="bg-gray-50 rounded-xl p-4">
              {/* Agents */}
              <div className="mb-4">
                <p className="text-xs text-gray-500 mb-2">包含 {template.agents_config.length} 个 Agent：</p>
                <div className="flex flex-wrap gap-2">
                  {template.agents_config.map((agent, idx) => (
                    <div key={idx} className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg text-sm">
                      {agent.name}
                    </div>
                  ))}
                </div>
              </div>

              {/* Tasks */}
              <div>
                <p className="text-xs text-gray-500 mb-2">包含 {template.tasks_config.length} 个 Task：</p>
                <div className="space-y-2">
                  {template.tasks_config.map((task, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="w-6 h-6 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center text-xs font-medium">
                        {idx + 1}
                      </span>
                      <span className="text-sm text-gray-700">{task.name}</span>
                      {task.depends_on.length > 0 && (
                        <span className="text-xs text-gray-400">
                          (依赖任务 {task.depends_on.map(d => d + 1).join(', ')})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 底部操作 */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <AppleButton variant="secondary" onClick={onClose}>
            取消
          </AppleButton>
          <AppleButton onClick={handleUseTemplate} isLoading={isLoading}>
            使用此模板
          </AppleButton>
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Create TemplateSkeletonGrid component**

```tsx
// frontend/src/components/templates/TemplateSkeletonGrid.tsx

import React from 'react';
import { Skeleton } from '../ui/Skeleton';

const TemplateCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-2xl shadow-md p-6">
    <div className="flex items-start justify-between mb-4">
      <Skeleton className="w-12 h-12 rounded-xl" />
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
    <Skeleton className="h-6 w-3/4 mb-2" />
    <Skeleton className="h-4 w-full mb-4" />
    <div className="flex gap-2 mb-4">
      <Skeleton className="h-6 w-16 rounded-md" />
      <Skeleton className="h-6 w-16 rounded-md" />
      <Skeleton className="h-6 w-16 rounded-md" />
    </div>
    <Skeleton className="h-4 w-24 mb-4" />
    <Skeleton className="h-10 w-full rounded-xl" />
  </div>
);

export const TemplateSkeletonGrid: React.FC = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mt-6">
    {Array.from({ length: 8 }).map((_, i) => (
      <TemplateCardSkeleton key={i} />
    ))}
  </div>
);
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/templates/
git commit -m "feat(templates): add template card, detail modal, and skeleton components"
```

---

## Task 10: Frontend - Create Templates Page

**Files:**
- Create: `frontend/src/pages/Templates.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create Templates page**

```tsx
// frontend/src/pages/Templates.tsx

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowLeft } from 'lucide-react';
import { templatesApi, type Template } from '../api/templates';
import { TemplateCard } from '../components/templates/TemplateCard';
import { TemplateDetailModal } from '../components/templates/TemplateDetailModal';
import { TemplateSkeletonGrid } from '../components/templates/TemplateSkeletonGrid';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';

const CATEGORIES = [
  { id: 'all', label: '全部', icon: '🎯' },
  { id: 'research', label: '研究分析', icon: '📊' },
  { id: 'code', label: '代码开发', icon: '🔍' },
  { id: 'analysis', label: '数据分析', icon: '📈' },
  { id: 'document', label: '文档撰写', icon: '📄' },
  { id: 'literature', label: '文献研究', icon: '📚' },
];

const Templates: React.FC = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [sortBy, setSortBy] = useState('popular');
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates', category, search, sortBy],
    queryFn: () => templatesApi.list({
      category: category === 'all' ? undefined : category,
      search: search || undefined,
      sort_by: sortBy,
    }),
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
              <ArrowLeft className="w-4 h-4 mr-1" /> 返回
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">模板市场</h1>
              <p className="text-gray-600 mt-1">选择一个模板快速开始</p>
            </div>
          </div>
        </div>
      </header>

      {/* 搜索和筛选 */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* 搜索框 */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索模板..."
              className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* 分类筛选 */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id)}
                className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                  category === cat.id
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {cat.icon} {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* 排序选项 */}
        <div className="flex justify-end mt-4">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm"
          >
            <option value="popular">最热门</option>
            <option value="newest">最新</option>
            <option value="recommended">推荐</option>
          </select>
        </div>

        {/* 模板网格 */}
        {isLoading ? (
          <TemplateSkeletonGrid />
        ) : templates?.items.length === 0 ? (
          <EmptyState
            icon="🔍"
            title="未找到匹配的模板"
            description="尝试使用其他关键词，或浏览所有模板"
            action={{ label: '清除搜索', onClick: () => setSearch('') }}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mt-6">
            {templates?.items.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onClick={() => setSelectedTemplate(template)}
              />
            ))}
          </div>
        )}
      </div>

      {/* 模板详情弹窗 */}
      {selectedTemplate && (
        <TemplateDetailModal
          template={selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
        />
      )}
    </div>
  );
};

export default Templates;
```

- [ ] **Step 2: Add templates route to App.tsx**

```tsx
// Add to frontend/src/App.tsx

import Templates from './pages/Templates';

// Add route inside <Routes>
<Route
  path="/templates"
  element={
    <ProtectedRoute>
      <Templates />
    </ProtectedRoute>
  }
/>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Templates.tsx frontend/src/App.tsx
git commit -m "feat(pages): add Templates marketplace page with routing"
```

---

## Task 11: Frontend - Add Token Refresh to Auth Store

**Files:**
- Modify: `frontend/src/stores/authStore.ts`

- [ ] **Step 1: Update authStore with token refresh logic**

```typescript
// frontend/src/stores/authStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import toast from 'react-hot-toast';
import type { User } from '../types';
import { authApi } from '../api/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  tokenExpiresAt: number | null;  // Token 过期时间戳（毫秒）
  isAuthenticated: boolean;
  isLoading: boolean;
  _hydrated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; username: string; password: string; full_name?: string }) => Promise<'ok' | 'need_login'>;
  logout: () => void;
  loadUser: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  checkTokenExpiry: () => { isExpired: boolean; isExpiringSoon: boolean; remainingSeconds: number };
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      tokenExpiresAt: null,
      isAuthenticated: false,
      isLoading: true,
      _hydrated: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const { access_token, expires_in } = await authApi.login({ email, password });
          const expiresAt = Date.now() + (expires_in * 1000);
          set({ token: access_token, tokenExpiresAt: expiresAt });
          const user = await authApi.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ user: null, token: null, tokenExpiresAt: null, isAuthenticated: false, isLoading: false });
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true });
        try {
          await authApi.register(data);
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
        try {
          await get().login(data.email, data.password);
          return 'ok';
        } catch {
          set({ isLoading: false });
          return 'need_login';
        }
      },

      logout: () => {
        set({ user: null, token: null, tokenExpiresAt: null, isAuthenticated: false, isLoading: false });
      },

      loadUser: async () => {
        const token = get().token;
        if (!token) {
          set({ isAuthenticated: false, isLoading: false, _hydrated: true });
          return;
        }
        set({ isLoading: true });
        try {
          const user = await authApi.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false, _hydrated: true });
        } catch {
          if (get().token) {
            toast.error('会话已过期，请重新登录');
          }
          set({ user: null, token: null, tokenExpiresAt: null, isAuthenticated: false, isLoading: false, _hydrated: true });
        }
      },

      refreshToken: async () => {
        try {
          const { access_token, expires_in } = await authApi.refreshToken();
          const expiresAt = Date.now() + (expires_in * 1000);
          set({ token: access_token, tokenExpiresAt: expiresAt });
          return true;
        } catch {
          return false;
        }
      },

      checkTokenExpiry: () => {
        const { tokenExpiresAt } = get();
        if (!tokenExpiresAt) {
          return { isExpired: true, isExpiringSoon: false, remainingSeconds: 0 };
        }
        const now = Date.now();
        const remainingMs = tokenExpiresAt - now;
        const remainingSeconds = Math.max(0, Math.floor(remainingMs / 1000));
        return {
          isExpired: remainingSeconds <= 0,
          isExpiringSoon: remainingSeconds > 0 && remainingSeconds < 300, // 5分钟内
          remainingSeconds,
        };
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, tokenExpiresAt: state.tokenExpiresAt }),
      onRehydrateStorage: () => {
        return (state) => {
          if (state?.token) {
            state.isLoading = true;
            state._hydrated = false;
          } else {
            state.isLoading = false;
            state._hydrated = true;
          }
        };
      },
    }
  )
);
```

- [ ] **Step 2: Update authApi to include refresh**

```typescript
// Add to frontend/src/api/auth.ts

export const authApi = {
  // ... existing methods ...

  refreshToken: async (): Promise<{ access_token: string; token_type: string; expires_in: number }> => {
    const response = await apiClient.post('/auth/refresh');
    return response.data;
  },
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/authStore.ts frontend/src/api/auth.ts
git commit -m "feat(auth): add token refresh logic to auth store"
```

---

## Task 12: Frontend - Enhance ProtectedRoute with Token Refresh

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create TokenRefreshModal component**

```tsx
// Add to frontend/src/App.tsx or create separate file

const TokenRefreshModal: React.FC<{
  isOpen: boolean;
  onRefresh: () => void;
  onDismiss: () => void;
  remainingSeconds: number;
}> = ({ isOpen, onRefresh, onDismiss, remainingSeconds }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl p-6 max-w-sm mx-4 shadow-xl">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 bg-yellow-100 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            会话即将过期
          </h3>
          <p className="text-gray-600 mb-1">
            您的登录会话将在 <span className="font-bold text-yellow-600">{remainingSeconds}</span> 秒后过期
          </p>
          <p className="text-sm text-gray-500 mb-6">
            是否续期以继续使用？
          </p>
          <div className="flex gap-3">
            <button
              onClick={onDismiss}
              className="flex-1 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors"
            >
              稍后提醒
            </button>
            <button
              onClick={onRefresh}
              className="flex-1 px-4 py-2.5 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors"
            >
              立即续期
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 2: Update ProtectedRoute with token refresh**

```tsx
// Update ProtectedRoute in frontend/src/App.tsx

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, checkTokenExpiry, refreshToken, logout } = useAuthStore();
  const navigate = useNavigate();
  const [showRefreshModal, setShowRefreshModal] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [dismissed, setDismissed] = useState(false);

  // 检查 Token 过期
  useEffect(() => {
    if (!isAuthenticated) return;

    const checkExpiry = () => {
      const { isExpired, isExpiringSoon, remainingSeconds: remaining } = checkTokenExpiry();

      if (isExpired) {
        logout();
        navigate('/login');
        toast.error('会话已过期，请重新登录');
      } else if (isExpiringSoon && !dismissed) {
        setRemainingSeconds(remaining);
        setShowRefreshModal(true);
      }
    };

    checkExpiry();
    const interval = setInterval(checkExpiry, 1000);

    return () => clearInterval(interval);
  }, [isAuthenticated, dismissed]);

  const handleRefresh = async () => {
    const success = await refreshToken();
    if (success) {
      setShowRefreshModal(false);
      setDismissed(false);
      toast.success('会话已续期');
    } else {
      toast.error('续期失败，请重新登录');
      logout();
      navigate('/login');
    }
  };

  const handleDismiss = () => {
    setShowRefreshModal(false);
    setDismissed(true);
    // 5分钟后再次提醒
    setTimeout(() => setDismissed(false), 5 * 60 * 1000);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <>
      {children}
      <TokenRefreshModal
        isOpen={showRefreshModal}
        onRefresh={handleRefresh}
        onDismiss={handleDismiss}
        remainingSeconds={remainingSeconds}
      />
    </>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(auth): add token refresh modal to ProtectedRoute"
```

---

## Task 13: Frontend - Add Responsive Hooks

**Files:**
- Create: `frontend/src/lib/responsive.ts`

- [ ] **Step 1: Create responsive hooks**

```typescript
// frontend/src/lib/responsive.ts

import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

export function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 767px)');
}

export function useIsTablet(): boolean {
  return useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
}

export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1024px)');
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/responsive.ts
git commit -m "feat(lib): add responsive design hooks"
```

---

## Task 14: Frontend - Update Dashboard with Responsive Design

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Update Dashboard with responsive layout**

```tsx
// Update imports in frontend/src/pages/Dashboard.tsx

import { useIsMobile, useIsTablet } from '../lib/responsive';
import { EmptyState } from '../components/ui/EmptyState';
import { MobileMenu } from '../components/layout/MobileMenu';

// Update Dashboard component
const Dashboard: React.FC = () => {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  // ... existing code ...

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 - 响应式 */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Workflow className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">Fugue</span>
            </div>
            {isMobile ? (
              <MobileMenu />
            ) : (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">欢迎，{user?.username || '用户'}</span>
                <Button variant="ghost" size="sm" onClick={() => navigate('/settings')}>
                  <Key className="w-4 h-4 mr-1" /> API设置
                </Button>
                <Button variant="ghost" size="sm" onClick={handleLogout}>退出登录</Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 快速开始引导 - 空状态 */}
        {(!crews || crews.length === 0) && !isLoading && (
          <EmptyState
            icon="🚀"
            title="开始你的第一个工作流"
            description="创建一个多智能体协作工作流，让 AI 助手帮你完成复杂的任务"
            action={{ label: '创建示例工作流', onClick: () => demoMutation.mutate() }}
            secondaryAction={{ label: '浏览模板市场', onClick: () => navigate('/templates') }}
          />
        )}

        {/* 工作流列表 */}
        {crews && crews.length > 0 && (
          <>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
              <h2 className="text-2xl font-bold text-gray-900">我的工作流</h2>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => navigate('/templates')}>
                  <BookOpen className="w-4 h-4 mr-2" /> 浏览模板
                </Button>
                <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
                  <Plus className="h-4 w-4 mr-2" />
                  {createMutation.isPending ? '创建中...' : '新建工作流'}
                </Button>
              </div>
            </div>

            {/* 响应式卡片网格 */}
            <div className={`grid gap-6 ${
              isMobile ? 'grid-cols-1' :
              isTablet ? 'grid-cols-2' :
              'grid-cols-3'
            }`}>
              {crews.map((crew) => (
                // ... existing crew card code ...
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
};
```

- [ ] **Step 2: Create MobileMenu component**

```tsx
// frontend/src/components/layout/MobileMenu.tsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, X, Home, FileText, Settings, LogOut } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

export const MobileMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const { logout } = useAuthStore();

  const menuItems = [
    { icon: Home, label: '首页', path: '/' },
    { icon: FileText, label: '模板市场', path: '/templates' },
    { icon: Settings, label: '设置', path: '/settings' },
  ];

  const handleNavigate = (path: string) => {
    navigate(path);
    setIsOpen(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsOpen(false)}
          />

          <div className="fixed right-0 top-0 bottom-0 w-64 bg-white shadow-xl z-50">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-900">菜单</span>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <nav className="p-4">
              {menuItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => handleNavigate(item.path)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors mb-1"
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </button>
              ))}

              <hr className="my-4" />

              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
                退出登录
              </button>
            </nav>
          </div>
        </>
      )}
    </div>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx frontend/src/components/layout/MobileMenu.tsx
git commit -m "feat(dashboard): add responsive design and mobile menu"
```

---

## Task 15: Frontend - Enhance Error Boundary

**Files:**
- Modify: `frontend/src/components/ErrorBoundary.tsx`

- [ ] **Step 1: Update ErrorBoundary with Apple-style design**

```tsx
// frontend/src/components/ErrorBoundary.tsx

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#F2F2F7] p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-lg text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-xl font-semibold text-[#1C1C1E] mb-2">
              出现了一些问题
            </h2>
            <p className="text-[#8E8E93] mb-6">
              {this.state.error?.message || '请稍后重试'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#007AFF] text-white rounded-xl hover:bg-[#0056CC] transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              重试
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ErrorBoundary.tsx
git commit -m "feat(ui): enhance ErrorBoundary with Apple-style design"
```

---

## Task 16: Frontend - Add API Error Interceptor

**Files:**
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Add response interceptor for error handling**

```typescript
// Add to frontend/src/api/client.ts

import toast from 'react-hot-toast';

// Add response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error;

    if (!response) {
      // 网络错误
      toast.error('网络连接失败，请检查网络');
      return Promise.reject(error);
    }

    const { status, data } = response;

    // 不处理 401（由 authStore 处理）
    if (status === 401) {
      return Promise.reject(error);
    }

    switch (status) {
      case 403:
        toast.error('没有权限执行此操作');
        break;
      case 404:
        toast.error('请求的资源不存在');
        break;
      case 422:
        // 验证错误
        const validationErrors = data.detail;
        if (Array.isArray(validationErrors)) {
          validationErrors.forEach((err: any) => {
            toast.error(`${err.loc?.[1] || '参数'}: ${err.msg}`);
          });
        } else {
          toast.error(data.detail || '请求参数错误');
        }
        break;
      case 429:
        toast.error('请求过于频繁，请稍后重试');
        break;
      case 500:
        toast.error('服务器错误，请稍后重试');
        break;
      default:
        toast.error(data.detail || '请求失败');
    }

    return Promise.reject(error);
  }
);
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat(api): add response error interceptor with toast notifications"
```

---

## Task 17: Integration - Seed Template Data

**Files:**
- None (manual testing)

- [ ] **Step 1: Start backend server**

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Login and get token**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

- [ ] **Step 3: Seed templates**

```bash
curl -X POST http://localhost:8000/api/v1/demo/seed-templates \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Expected response:
```json
{
  "message": "成功初始化 5 个预设模板",
  "count": 5
}
```

- [ ] **Step 4: Verify templates API**

```bash
curl http://localhost:8000/api/v1/templates?limit=5 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

Expected: List of 5 templates

- [ ] **Step 5: Commit (if any fixes needed)**

```bash
# Only if changes were made
git add -A
git commit -m "fix: integration testing fixes"
```

---

## Task 18: Frontend Testing - Template Flow

**Files:**
- None (manual testing)

- [ ] **Step 1: Start frontend dev server**

```bash
cd frontend
npm run dev
```

- [ ] **Step 2: Test template marketplace**

1. Navigate to http://localhost:5173/templates
2. Verify 5 templates are displayed
3. Test category filtering
4. Test search functionality
5. Click on a template to see detail modal
6. Click "使用此模板" to create workflow

- [ ] **Step 3: Test token refresh**

1. Login to the application
2. Wait for token to approach expiry (or manually set short expiry for testing)
3. Verify refresh modal appears
4. Click "立即续期" - should refresh token
5. Click "稍后提醒" - should dismiss modal
6. Wait for token to expire - should redirect to login

- [ ] **Step 4: Test responsive design**

1. Open browser dev tools
2. Switch to mobile view (375px)
3. Verify mobile menu appears
4. Test navigation from mobile menu
5. Verify cards stack vertically

- [ ] **Step 5: Test error handling**

1. Disconnect network
2. Try to load templates
3. Verify error toast appears
4. Reconnect and verify recovery

- [ ] **Step 6: Commit final changes**

```bash
git add -A
git commit -m "feat: complete Week 5 implementation"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** All Week 5 features from design doc are covered
  - Token refresh mechanism ✅
  - Template system (5 templates, CRUD, marketplace) ✅
  - Apple-style UI components ✅
  - Responsive design ✅
  - Error handling ✅

- [x] **Placeholder scan:** No TBD, TODO, or incomplete sections found

- [x] **Type consistency:** All types, method signatures, and property names are consistent across tasks

- [x] **Test coverage:** Manual testing tasks included for integration verification

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-01-week5-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
