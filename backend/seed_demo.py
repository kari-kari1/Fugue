"""完整演示数据种子脚本

创建演示用户、工作流、Agent、Task等完整数据
"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models import Agent, Crew, Task, User
from app.services.template_seeder import seed_templates

# 演示用户配置
DEMO_USERS = [
    {
        "email": "demo@fugue.com",
        "username": "demo",
        "password": "Demo123456",
        "full_name": "演示用户",
        "is_active": True,
    },
    {
        "email": "admin@fugue.com",
        "username": "admin",
        "password": "Admin123456",
        "full_name": "管理员",
        "is_active": True,
        "is_superuser": True,
    },
]

# 演示工作流配置
DEMO_WORKFLOWS = [
    {
        "name": "AI行业周报生成器",
        "description": "自动收集AI行业最新动态，生成专业的行业周报。包含市场分析、技术趋势、融资动态等多个维度。",
        "process": "sequential",
        "agents": [
            {
                "name": "行业研究员",
                "role": "资深行业研究分析师",
                "goal": "收集和分析AI行业的最新数据和趋势",
                "backstory": "你是一位在AI行业研究领域有10年经验的资深分析师，擅长从海量信息中提取关键洞察，对行业趋势有敏锐的洞察力。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools_config": ["web_search", "file_read"],
            },
            {
                "name": "报告写手",
                "role": "专业技术内容写手",
                "goal": "基于研究结果撰写清晰、专业的行业周报",
                "backstory": "你是一位资深技术写手，擅长将复杂的数据和分析转化为通俗易懂、结构清晰的报告，曾为多家知名科技媒体撰写专栏。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools_config": ["file_write"],
            },
        ],
        "tasks": [
            {
                "name": "数据收集",
                "description": "收集本周AI行业的重大事件，包括：1) 融资动态 2) 产品发布 3) 技术突破 4) 政策法规 5) 人才变动",
                "expected_output": "结构化的行业数据报告，包含各类别的关键事件及其影响分析",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [],
            },
            {
                "name": "趋势分析",
                "description": "分析收集到的数据，识别本周的关键趋势、热点话题和潜在机会。",
                "expected_output": "趋势分析报告，包含3-5个关键趋势及其对行业的影响",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [0],
            },
            {
                "name": "周报撰写",
                "description": "基于数据分析结果，撰写完整的AI行业周报。包含：执行摘要、市场概况、重点事件、技术趋势、投资动态、下周展望等章节。",
                "expected_output": "一篇结构完整、数据详实的AI行业周报（2000-3000字）",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1],
            },
        ],
    },
    {
        "name": "竞品分析助手",
        "description": "深度分析竞争对手的产品、策略和市场表现，帮助制定竞争策略。适合产品经理、市场分析师和创业者。",
        "process": "sequential",
        "agents": [
            {
                "name": "市场研究员",
                "role": "资深市场研究分析师",
                "goal": "收集竞品的公开信息和市场数据",
                "backstory": "你是一位资深市场研究分析师，擅长从公开渠道收集和整理竞品信息，包括产品功能、定价策略、用户评价等。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools_config": ["web_search", "file_read"],
            },
            {
                "name": "产品分析师",
                "role": "高级产品分析师",
                "goal": "分析竞品的产品策略和用户体验",
                "backstory": "你是一位高级产品分析师，擅长从用户视角分析产品的优劣势，能够洞察产品背后的战略意图。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools_config": ["file_read"],
            },
            {
                "name": "报告写手",
                "role": "商业分析报告专家",
                "goal": "整合分析结果，撰写专业的竞品分析报告",
                "backstory": "你是一位商业分析报告专家，擅长将复杂的分析结果转化为清晰、可执行的商业洞察。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools_config": ["file_write"],
            },
        ],
        "tasks": [
            {
                "name": "竞品信息收集",
                "description": "收集主要竞品的基本信息：公司背景、产品功能、定价策略、用户规模、融资情况等。",
                "expected_output": "竞品信息汇总表，包含各竞品的核心数据",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [],
            },
            {
                "name": "产品对比分析",
                "description": "从功能、用户体验、技术架构、商业模式等维度对比分析各竞品，识别差异化优势和劣势。",
                "expected_output": "产品对比分析矩阵，包含各维度的详细对比",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [0],
            },
            {
                "name": "竞争策略建议",
                "description": "基于分析结果，提出针对性的竞争策略建议，包括差异化定位、功能优先级、市场进入策略等。",
                "expected_output": "竞争策略建议书，包含短期和长期策略建议",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1],
            },
            {
                "name": "报告撰写",
                "description": "整合所有分析结果，撰写完整的竞品分析报告，包含市场概况、竞品详情、对比分析、策略建议等章节。",
                "expected_output": "专业的竞品分析报告（3000-4000字）",
                "output_type": "text",
                "agent_index": 2,
                "depends_on": [2],
            },
        ],
    },
]


async def seed_demo_users(db):
    """创建演示用户"""
    print("\n👥 Creating demo users...")

    created_count = 0
    skipped_count = 0

    for user_data in DEMO_USERS:
        # 检查用户是否已存在
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"  ⏭️  Skipped: {user_data['email']} (already exists)")
            skipped_count += 1
            continue

        # 创建用户
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data.get("full_name"),
            is_active=user_data.get("is_active", True),
            is_superuser=user_data.get("is_superuser", False),
        )
        db.add(user)
        created_count += 1
        print(f"  ✅ Created: {user_data['email']}")

    await db.commit()
    return {"created": created_count, "skipped": skipped_count}


async def seed_demo_workflows(db):
    """创建工作流、Agent、Task"""
    print("\n🔄 Creating demo workflows...")

    # 获取演示用户
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.email == "demo@fugue.com")
    )
    demo_user = result.scalar_one_or_none()

    if not demo_user:
        print("  ❌ Demo user not found, skipping workflows")
        return {"created": 0, "skipped": 0}

    created_count = 0
    skipped_count = 0

    for workflow_data in DEMO_WORKFLOWS:
        # 检查工作流是否已存在
        result = await db.execute(
            select(Crew).where(
                Crew.user_id == demo_user.id,
                Crew.name == workflow_data["name"]
            )
        )
        existing_crew = result.scalar_one_or_none()

        if existing_crew:
            print(f"  ⏭️  Skipped: {workflow_data['name']} (already exists)")
            skipped_count += 1
            continue

        # 创建工作流
        crew = Crew(
            name=workflow_data["name"],
            description=workflow_data["description"],
            user_id=demo_user.id,
            process=workflow_data["process"],
        )
        db.add(crew)
        await db.flush()

        # 创建 Agent
        agents = []
        for agent_data in workflow_data["agents"]:
            agent = Agent(
                crew_id=crew.id,
                name=agent_data["name"],
                role=agent_data["role"],
                goal=agent_data["goal"],
                backstory=agent_data["backstory"],
                llm_provider=agent_data["llm_provider"],
                llm_model=agent_data["llm_model"],
                tools_config=agent_data.get("tools_config", []),
            )
            db.add(agent)
            await db.flush()
            agents.append(agent)

        # 创建 Task
        tasks = []
        for task_idx, task_data in enumerate(workflow_data["tasks"]):
            # 解析依赖
            context_task_ids = []
            for dep_idx in task_data.get("depends_on", []):
                if dep_idx < len(tasks):
                    context_task_ids.append(tasks[dep_idx].id)

            task = Task(
                crew_id=crew.id,
                agent_id=agents[task_data["agent_index"]].id,
                name=task_data["name"],
                description=task_data["description"],
                expected_output=task_data["expected_output"],
                output_type=task_data.get("output_type", "text"),
                context_task_ids=context_task_ids,
            )
            db.add(task)
            await db.flush()
            tasks.append(task)

        created_count += 1
        print(f"  ✅ Created: {workflow_data['name']} ({len(agents)} agents, {len(tasks)} tasks)")

    await db.commit()
    return {"created": created_count, "skipped": skipped_count}


async def main():
    """主函数"""
    print("🚀 Fugue Demo Data Seeder")
    print("=" * 50)

    async with AsyncSessionLocal() as db:
        try:
            # 1. 初始化模板
            print("\n📋 Initializing templates...")
            template_result = await seed_templates(db)
            print(f"   Created: {template_result['total_created']}, Skipped: {template_result['total_skipped']}")

            # 2. 创建演示用户
            user_result = await seed_demo_users(db)
            print(f"\n   Total users - Created: {user_result['created']}, Skipped: {user_result['skipped']}")

            # 3. 创建演示工作流
            workflow_result = await seed_demo_workflows(db)
            print(f"\n   Total workflows - Created: {workflow_result['created']}, Skipped: {workflow_result['skipped']}")

            print("\n" + "=" * 50)
            print("✅ Demo data initialization complete!")
            print("\n📝 Demo credentials:")
            print("   Email: demo@fugue.com")
            print("   Password: Demo123456")
            print("\n   Admin account:")
            print("   Email: admin@fugue.com")
            print("   Password: Admin123456")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
