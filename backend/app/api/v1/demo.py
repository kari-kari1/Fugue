"""演示数据API - 创建示例工作流供用户测试"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentSuperUser, DatabaseSession
from app.models.agent import Agent
from app.models.crew import Crew, ProcessType
from app.models.task import Task
from app.services.template_seeder import seed_templates

router = APIRouter()


@router.post("/seed-demo-workflow", status_code=status.HTTP_201_CREATED)
async def seed_demo_workflow(db: DatabaseSession, current_user: CurrentSuperUser):
    """创建一个示例工作流，包含2个Agent和2个Task，可直接运行测试"""

    # 检查是否已有演示工作流
    existing = await db.execute(
        select(Crew).where(Crew.user_id == current_user.id, Crew.name == "📚 AI研究报告（示例）")
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="演示工作流已存在，请勿重复创建")

    # 创建工作流
    crew = Crew(
        name="📚 AI研究报告（示例）",
        description="一个完整的示例工作流：研究Agent收集信息，写作Agent撰写报告。可直接运行测试执行引擎。",
        user_id=current_user.id,
        process=ProcessType.SEQUENTIAL,
    )
    db.add(crew)
    await db.flush()

    # 创建Agent 1: 研究员
    researcher = Agent(
        crew_id=crew.id,
        name="研究员",
        role="资深AI行业研究员",
        goal="收集和分析AI行业的最新趋势和数据",
        backstory="你是一位在AI领域有10年经验的资深研究员，擅长数据分析和行业趋势预测。",
        llm_provider="mock",
        llm_model="mock-model",
        temperature=0.7,
        max_tokens=2048,
        position_x=100,
        position_y=100,
    )
    db.add(researcher)

    # 创建Agent 2: 写手
    writer = Agent(
        crew_id=crew.id,
        name="报告写手",
        role="专业技术内容写手",
        goal="基于研究结果撰写清晰、专业的分析报告",
        backstory="你是一位资深技术写手，擅长将复杂的技术概念转化为通俗易懂的报告。",
        llm_provider="mock",
        llm_model="mock-model",
        temperature=0.7,
        max_tokens=2048,
        position_x=100,
        position_y=350,
    )
    db.add(writer)
    await db.flush()

    # 创建Task 1: 市场研究
    research_task = Task(
        crew_id=crew.id,
        agent_id=researcher.id,
        name="AI市场研究",
        description="研究2026年AI Agent市场的最新趋势，包括市场规模、主要玩家、技术发展方向。重点关注多智能体协作领域的发展。",
        expected_output="一份包含市场规模、趋势分析、竞争格局的研究摘要",
        output_type="text",
        position_x=400,
        position_y=100,
    )
    db.add(research_task)

    # 创建Task 2: 撰写报告（依赖Task 1）
    writing_task = Task(
        crew_id=crew.id,
        agent_id=writer.id,
        name="撰写分析报告",
        description="基于市场研究结果，撰写一篇专业的AI行业分析报告。报告需要包含引言、核心分析、数据支撑和结论建议。",
        expected_output="一篇结构完整、数据详实的分析报告（800-1200字）",
        output_type="text",
        context_task_ids=[research_task.id],  # 依赖研究任务
        position_x=400,
        position_y=350,
    )
    db.add(writing_task)

    await db.commit()

    return {
        "message": "演示工作流创建成功",
        "crew_id": crew.id,
        "workflow": {
            "name": crew.name,
            "agents": 2,
            "tasks": 2,
            "description": "研究员收集AI行业数据 → 写手基于研究结果撰写报告",
        },
    }


@router.post("/seed-templates", status_code=status.HTTP_201_CREATED)
async def seed_templates_endpoint(db: DatabaseSession, admin: CurrentSuperUser):
    """种子接口：写入5个预置内置模板（幂等，已存在则跳过）"""

    result = await seed_templates(db)

    return {
        "message": f"模板种子完成：新增 {result['total_created']} 个，跳过 {result['total_skipped']} 个",
        "created": result["created"],
        "skipped": result["skipped"],
    }
