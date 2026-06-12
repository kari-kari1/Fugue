"""模板种子服务 - 预置 5 个内置工作流模板"""

from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template


# ---------------------------------------------------------------------------
# 预置模板数据
# ---------------------------------------------------------------------------

PREDEFINED_TEMPLATES: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------
    # 1. 行业研究报告生成
    # ------------------------------------------------------------------
    {
        "name": "行业研究报告生成",
        "description": "由行业研究员收集数据并分析趋势，再由报告写手撰写结构化的研究报告，适用于市场分析、技术趋势等场景。",
        "category": "research",
        "icon": "📊",
        "difficulty": "intermediate",
        "process_type": "sequential",
        "tags": ["行业研究", "数据分析", "报告撰写"],
        "agents_config": [
            {
                "name": "行业研究员",
                "role": "资深行业研究员",
                "goal": "收集目标行业的关键数据，识别市场趋势和竞争格局，为报告提供可靠的数据支撑。",
                "backstory": "你是一位拥有10年行业研究经验的资深分析师，擅长从公开数据、行业报告和专家访谈中提取关键信息，并通过数据交叉验证确保结论的可靠性。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
            {
                "name": "报告写手",
                "role": "专业技术报告写手",
                "goal": "将研究员提供的数据和分析转化为结构清晰、逻辑严密、可读性强的行业研究报告。",
                "backstory": "你是一位资深技术写手，曾为多家咨询公司撰写行业白皮书。你擅长将复杂的数据转化为有洞察力的叙述，报告风格兼具专业性和可读性。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
        ],
        "tasks_config": [
            {
                "name": "数据收集",
                "description": "针对指定行业，收集市场规模、增长率、主要玩家、技术趋势等关键数据。需注明数据来源和时间范围。",
                "expected_output": "结构化的行业数据汇总，包含市场规模、增长率、主要参与者、技术趋势等维度，每个维度附数据来源。",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [],
            },
            {
                "name": "数据分析",
                "description": "基于收集的数据，进行深度分析：识别行业驱动力与阻力、SWOT分析、未来3-5年趋势预测。",
                "expected_output": "包含行业驱动力分析、SWOT总结、未来趋势预测的分析报告，附关键数据图表描述。",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [0],
            },
            {
                "name": "报告撰写",
                "description": "基于数据分析结果，撰写完整的行业研究报告。报告应包含：摘要、行业概述、市场分析、竞争格局、趋势预测、结论与建议。",
                "expected_output": "一篇2000-3000字的结构化行业研究报告，包含摘要、正文六大部分和结论建议。",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 2. 代码审查助手
    # ------------------------------------------------------------------
    {
        "name": "代码审查助手",
        "description": "自动审查代码质量、发现潜在问题，并提供优化建议。适用于代码评审、质量检查等场景。",
        "category": "code",
        "icon": "🔍",
        "difficulty": "beginner",
        "process_type": "sequential",
        "tags": ["代码审查", "代码质量", "最佳实践"],
        "agents_config": [
            {
                "name": "代码审查员",
                "role": "高级代码审查工程师",
                "goal": "全面审查代码质量，识别bug、安全漏洞、性能问题和代码规范违规。",
                "backstory": "你是一位有15年经验的高级软件工程师，参与过多个大型开源项目的代码审查。你对代码质量有极高的标准，擅长发现隐蔽的bug和安全隐患。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
            {
                "name": "优化建议员",
                "role": "代码优化顾问",
                "goal": "基于审查结果，提供具体、可执行的代码优化建议和重构方案。",
                "backstory": "你是一位专注于代码优化的技术顾问，擅长在保持功能不变的前提下提升代码的可读性、可维护性和性能。你总是提供具体的代码示例而非抽象建议。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
        ],
        "tasks_config": [
            {
                "name": "代码审查",
                "description": "对提交的代码进行全面审查，检查：1) 逻辑错误和边界条件 2) 安全漏洞（注入、XSS等）3) 性能瓶颈 4) 代码规范和命名 5) 测试覆盖率不足之处。",
                "expected_output": "代码审查报告，按严重程度（Critical/Major/Minor）分类列出所有发现的问题，每个问题附行号和说明。",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [],
            },
            {
                "name": "优化建议",
                "description": "基于代码审查结果，为每个发现的问题提供具体的优化建议：1) 问题根因分析 2) 推荐的解决方案 3) 优化后的代码示例 4) 相关最佳实践参考。",
                "expected_output": "优化建议文档，每个问题包含根因分析、解决方案、优化代码示例和最佳实践说明。",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [0],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 3. 竞品分析报告
    # ------------------------------------------------------------------
    {
        "name": "竞品分析报告",
        "description": "多维度竞品分析：收集竞品信息、对比产品特性、制定竞争策略，最终生成专业分析报告。",
        "category": "analysis",
        "icon": "📈",
        "difficulty": "advanced",
        "process_type": "sequential",
        "tags": ["竞品分析", "市场研究", "竞争策略"],
        "agents_config": [
            {
                "name": "市场研究员",
                "role": "资深市场研究分析师",
                "goal": "全面收集竞品的公开信息，包括产品特性、定价策略、市场份额、用户评价等。",
                "backstory": "你是一位专注于科技行业的市场研究分析师，擅长从公开渠道、行业报告和用户反馈中挖掘竞品关键信息，数据敏感度极高。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
            {
                "name": "产品分析师",
                "role": "高级产品分析师",
                "goal": "从产品维度深度对比分析各竞品的优劣势，识别差异化机会。",
                "backstory": "你是一位拥有丰富产品分析经验的专家，曾在多家头部互联网公司负责竞品分析工作。你擅长从用户视角评估产品，善于发现被忽视的差异化机会。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
            {
                "name": "报告写手",
                "role": "商业分析报告专家",
                "goal": "将竞品研究和分析结果整合为专业的竞品分析报告，提出可执行的竞争策略建议。",
                "backstory": "你是一位资深商业分析师，长期为企业高管撰写战略分析报告。你的报告以逻辑清晰、数据驱动、建议可执行而著称。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
        ],
        "tasks_config": [
            {
                "name": "竞品信息收集",
                "description": "针对指定的竞品列表，全面收集各竞品的公开信息：产品功能矩阵、定价模式、目标用户群、市场份额、融资情况、最新动态。",
                "expected_output": "各竞品的基础信息卡片，包含产品定位、核心功能、定价、市场份额等结构化数据。",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [],
            },
            {
                "name": "产品对比分析",
                "description": "基于收集的竞品信息，从产品功能、用户体验、技术架构、商业模式四个维度进行深度对比分析，绘制竞品定位图。",
                "expected_output": "多维度竞品对比矩阵和竞品定位分析，包含功能对比表、优劣势分析和差异化机会识别。",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [0],
            },
            {
                "name": "竞争策略建议",
                "description": "基于产品对比分析结果，制定针对性的竞争策略：差异化定位建议、功能优先级排序、定价策略参考、市场切入方案。",
                "expected_output": "竞争策略建议书，包含差异化定位、功能路线图建议、定价策略和市场切入方案四部分。",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1],
            },
            {
                "name": "报告撰写",
                "description": "整合所有分析结果，撰写专业的竞品分析报告。报告结构：执行摘要、竞品概览、详细对比分析、竞争策略建议、附录。",
                "expected_output": "一篇3000-4000字的专业竞品分析报告，含执行摘要、详细分析和可执行的策略建议。",
                "output_type": "text",
                "agent_index": 2,
                "depends_on": [2],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 4. 产品需求文档
    # ------------------------------------------------------------------
    {
        "name": "产品需求文档",
        "description": "从需求分析到技术方案再到PRD撰写，系统化地产出高质量的产品需求文档。",
        "category": "document",
        "icon": "📄",
        "difficulty": "intermediate",
        "process_type": "sequential",
        "tags": ["PRD", "需求分析", "产品设计"],
        "agents_config": [
            {
                "name": "需求分析师",
                "role": "资深需求分析师",
                "goal": "深入理解用户需求和业务场景，提炼核心需求并设计技术实现方案。",
                "backstory": "你是一位有8年经验的需求分析师，曾在多家互联网公司主导过从0到1的产品需求分析。你擅长从业务目标出发，通过用户故事和场景分析提炼出精准的需求定义。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
            {
                "name": "文档写手",
                "role": "技术文档专家",
                "goal": "将需求分析和技术方案转化为规范、清晰、可执行的PRD文档。",
                "backstory": "你是一位资深技术文档专家，长期为产品和技术团队编写PRD。你深谙产品经理和技术团队的沟通痛点，能写出双方都易于理解的文档。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
        ],
        "tasks_config": [
            {
                "name": "需求分析",
                "description": "基于产品需求描述，进行系统化的需求分析：1) 用户画像和使用场景 2) 核心功能需求 3) 非功能需求（性能、安全、兼容性） 4) 需求优先级排序（MoSCoW法）。",
                "expected_output": "需求分析文档，包含用户画像、核心功能列表、非功能需求、优先级矩阵。",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [],
            },
            {
                "name": "技术方案设计",
                "description": "基于需求分析结果，设计技术实现方案：1) 系统架构概览 2) 核心模块划分 3) 数据模型设计 4) API接口概要 5) 技术选型建议。",
                "expected_output": "技术方案文档，包含架构图描述、模块划分、数据模型、API设计和技术选型。",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [0],
            },
            {
                "name": "PRD撰写",
                "description": "整合需求分析和技术方案，撰写完整的PRD文档。结构：文档概述、项目背景、需求详述、功能规格、技术方案、里程碑计划、风险评估。",
                "expected_output": "一份完整的PRD文档（2500-3500字），包含所有标准章节，附用户故事和验收标准。",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1],
            },
        ],
    },

    # ------------------------------------------------------------------
    # 5. 文献综述生成
    # ------------------------------------------------------------------
    {
        "name": "文献综述生成",
        "description": "自动检索、分析学术文献，并生成结构化的文献综述，适用于学术研究和课题调研。",
        "category": "literature",
        "icon": "📚",
        "difficulty": "advanced",
        "process_type": "sequential",
        "tags": ["文献综述", "学术研究", "课题调研"],
        "agents_config": [
            {
                "name": "文献检索员",
                "role": "学术文献检索专家",
                "goal": "围绕研究主题，系统性地检索和筛选高相关性的学术文献，建立文献清单。",
                "backstory": "你是一位图书馆学与情报学专业出身的文献检索专家，精通各大学术数据库的检索策略。你擅长使用布尔逻辑、主题词扩展等高级检索技巧，确保文献检索的全面性和精准性。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
            {
                "name": "综述写手",
                "role": "学术论文写作专家",
                "goal": "基于检索到的文献，进行批判性分析和综合，撰写逻辑严密的文献综述。",
                "backstory": "你是一位在核心期刊发表过多篇综述论文的学术写作专家。你擅长从大量文献中提炼研究脉络，识别研究空白，并以规范的学术语言组织综述内容。",
                "llm_provider": "openai",
                "llm_model": "gpt-4o",
                "tools": [],
            },
        ],
        "tasks_config": [
            {
                "name": "文献检索",
                "description": "围绕指定研究主题，设计系统化的检索策略：1) 确定关键词及其同义词/相关词 2) 制定检索式 3) 模拟检索并筛选高相关性文献 4) 输出文献清单（标题、作者、年份、摘要、来源）。",
                "expected_output": "结构化文献清单，包含每篇文献的标题、作者、年份、摘要、来源期刊/会议，以及检索策略说明。",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [],
            },
            {
                "name": "文献分析",
                "description": "对检索到的文献进行深度分析：1) 按主题/方法/结论分类 2) 识别研究趋势和热点 3) 发现研究空白和争议点 4) 提炼核心观点和理论框架。",
                "expected_output": "文献分析报告，包含文献分类、研究趋势、研究空白和核心理论框架四个部分。",
                "output_type": "text",
                "agent_index": 0,
                "depends_on": [0],
            },
            {
                "name": "综述撰写",
                "description": "基于文献分析结果，撰写规范的文献综述。结构：引言（研究背景与目的）、主体（按主题分节综述）、讨论（研究趋势与空白）、结论（总结与展望）。",
                "expected_output": "一篇3000-4000字的学术文献综述，包含引言、主体、讨论和结论四部分，引用格式规范。",
                "output_type": "text",
                "agent_index": 1,
                "depends_on": [1],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Seed 逻辑
# ---------------------------------------------------------------------------


async def seed_templates(db: AsyncSession) -> Dict[str, Any]:
    """
    向数据库写入预置模板。

    - 如果某个模板名称已存在则跳过（幂等）。
    - 返回本次操作的统计信息。
    """

    created: List[str] = []
    skipped: List[str] = []

    for tpl in PREDEFINED_TEMPLATES:
        # 检查是否已存在同名内置模板
        result = await db.execute(
            select(Template).where(
                Template.name == tpl["name"],
                Template.is_builtin == True,  # noqa: E712
            )
        )
        if result.scalar_one_or_none() is not None:
            skipped.append(tpl["name"])
            continue

        template = Template(
            name=tpl["name"],
            description=tpl["description"],
            category=tpl["category"],
            icon=tpl["icon"],
            difficulty=tpl["difficulty"],
            agents_config=tpl["agents_config"],
            tasks_config=tpl["tasks_config"],
            connections_config=[],
            process_type=tpl["process_type"],
            tags=tpl["tags"],
            is_builtin=True,
            use_count=0,
            rating=4.8,
        )
        db.add(template)
        created.append(tpl["name"])

    await db.commit()

    return {
        "created": created,
        "skipped": skipped,
        "total_created": len(created),
        "total_skipped": len(skipped),
    }
