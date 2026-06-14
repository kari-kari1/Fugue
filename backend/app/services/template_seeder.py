"""模板种子服务 - 预置 5 个内置工作流模板"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template

# ---------------------------------------------------------------------------
# 预置模板数据
# ---------------------------------------------------------------------------

PREDEFINED_TEMPLATES: list[dict[str, Any]] = [
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
    # 1b. 市场调研分析 (research)
    # ------------------------------------------------------------------
    {
        "name": "市场调研分析",
        "description": "系统化地进行市场调研：从数据采集到洞察提炼，帮助快速了解目标市场现状和机会点。",
        "category": "research",
        "icon": "📊",
        "difficulty": "beginner",
        "process_type": "sequential",
        "tags": ["市场调研", "数据分析", "商业洞察"],
        "agents_config": [
            {"name": "数据采集员", "role": "市场数据采集专家", "goal": "从多渠道收集目标市场的定量和定性数据，确保数据全面可靠。", "backstory": "你是一位经验丰富的市场调研专家，擅长从行业报告、公开数据、社交媒体等多渠道高效采集市场信息。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "分析师", "role": "商业分析师", "goal": "将采集的数据转化为可执行的商业洞察，识别市场机会和风险。", "backstory": "你是一位资深商业分析师，擅长从复杂数据中提炼出清晰的市场洞察，帮助决策者快速理解市场全貌。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "数据采集", "description": "收集目标市场的数据：市场规模、增长率、消费者行为、竞争格局、政策环境。", "expected_output": "结构化市场数据汇总表", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "洞察分析", "description": "基于采集的数据，分析市场机会点、风险因素和趋势预判，形成商业洞察。", "expected_output": "市场洞察分析报告，包含机会、风险、趋势三维度分析。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "技术趋势扫描",
        "description": "追踪和扫描特定技术领域的最新发展动态、专利趋势、论文热点，辅助技术决策。",
        "category": "research",
        "icon": "🔬",
        "difficulty": "intermediate",
        "process_type": "sequential",
        "tags": ["技术趋势", "专利分析", "科技前沿"],
        "agents_config": [
            {"name": "技术侦察员", "role": "技术趋势分析师", "goal": "追踪技术领域的前沿动态，识别关键技术突破和创新方向。", "backstory": "你是一位专注于前沿技术的分析师，常年追踪AI、云计算、半导体等领域的技术进展，能从海量信息中识别真正的技术趋势。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "趋势解读员", "role": "技术趋势解读专家", "goal": "将技术趋势数据转化为易懂的趋势报告，为技术决策提供参考。", "backstory": "你擅长将复杂的技术发展脉络梳理成清晰的趋势图景，为技术管理者和投资人提供决策参考。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "技术扫描", "description": "收集指定技术领域的最新动态：学术论文热点、专利申请趋势、开源项目动态、企业研发方向。", "expected_output": "技术动态扫描报告，按论文、专利、开源、企业四个维度整理。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "趋势报告", "description": "基于扫描结果，撰写技术趋势报告，识别Top5关键技术方向及其成熟度评估。", "expected_output": "技术趋势报告，含Top5方向详细分析和Gartner成熟度评估。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "用户研究分析",
        "description": "通过用户访谈数据分析、用户画像构建、体验痛点识别，为产品设计提供用户洞察。",
        "category": "research",
        "icon": "👥",
        "difficulty": "intermediate",
        "process_type": "sequential",
        "tags": ["用户研究", "用户画像", "体验设计"],
        "agents_config": [
            {"name": "用户研究员", "role": "用户研究专家", "goal": "分析用户行为数据和反馈，构建精准的用户画像和使用场景。", "backstory": "你是一位UX研究专家，擅长通过定性+定量方法理解用户需求，构建生动的用户画像。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "洞察分析师", "role": "用户洞察分析师", "goal": "从用户研究数据中提炼核心洞察，识别用户痛点和未满足需求。", "backstory": "你擅长从用户数据中发现隐藏的需求模式，将零散的用户反馈转化为系统化的产品改进建议。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "用户分析", "description": "分析用户行为数据、反馈和访谈记录，构建用户画像和使用场景地图。", "expected_output": "用户画像文档（2-3个典型画像）和核心使用场景描述。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "洞察报告", "description": "基于用户分析结果，提炼核心洞察，识别Top10用户痛点和产品改进机会。", "expected_output": "用户洞察报告，包含痛点矩阵和改进机会优先级排序。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },

    # ------------------------------------------------------------------
    # 2b. 代码生成器 (code)
    # ------------------------------------------------------------------
    {
        "name": "API接口生成器",
        "description": "根据需求描述自动设计RESTful API接口，生成完整的代码和文档，遵循行业最佳实践。",
        "category": "code",
        "icon": "🔌",
        "difficulty": "intermediate",
        "process_type": "sequential",
        "tags": ["API设计", "代码生成", "RESTful"],
        "agents_config": [
            {"name": "API设计师", "role": "API架构设计师", "goal": "基于需求设计符合RESTful规范的API接口，包含路径、参数、响应格式。", "backstory": "你是一位API设计专家，精通OpenAPI规范，设计过多个大型系统的API接口。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "代码生成员", "role": "后端代码生成专家", "goal": "将API设计转化为可运行的后端代码，支持Python/FastAPI和Node.js/Express。", "backstory": "你是一位全栈工程师，能将API设计快速转化为生产就绪的后端代码。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "API设计", "description": "分析需求并设计完整的RESTful API，包含端点列表、请求/响应格式、错误码定义。", "expected_output": "OpenAPI规范的API设计文档。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "代码生成", "description": "基于API设计，生成后端代码框架，包含路由、验证、错误处理和文档。", "expected_output": "完整的后端代码，可直接运行。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "单元测试生成器",
        "description": "自动为现有代码生成高质量的单元测试用例，覆盖边界条件和异常路径，提升代码质量。",
        "category": "code",
        "icon": "🧪",
        "difficulty": "beginner",
        "process_type": "sequential",
        "tags": ["单元测试", "测试覆盖", "代码质量"],
        "agents_config": [
            {"name": "测试分析师", "role": "测试策略分析师", "goal": "分析源码结构和逻辑分支，制定覆盖全面的测试策略。", "backstory": "你是一位资深测试工程师，擅长分析代码逻辑并设计高覆盖率的测试用例集合。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "测试代码生成员", "role": "测试代码编写专家", "goal": "根据测试策略生成完整、可运行的测试代码，遵循最佳实践。", "backstory": "你是一位精通pytest/Jest的测试开发专家，能写出清晰、可维护的测试代码。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "测试分析", "description": "分析代码结构，识别所有逻辑分支、边界条件和异常路径，制定测试策略。", "expected_output": "测试策略文档，包含测试用例矩阵和优先级。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "测试生成", "description": "基于测试策略生成完整的测试代码，覆盖正常路径、边界条件、异常处理和Mock。", "expected_output": "完整可运行的测试文件。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "代码重构顾问",
        "description": "分析现有代码库，识别需要重构的模块，提供具体的重构方案和代码示例。",
        "category": "code",
        "icon": "♻️",
        "difficulty": "advanced",
        "process_type": "sequential",
        "tags": ["代码重构", "技术债务", "设计模式"],
        "agents_config": [
            {"name": "代码分析师", "role": "代码架构分析师", "goal": "深度分析代码，识别技术债务、代码异味和架构问题。", "backstory": "你是一位拥有15年经验的软件架构师，擅长通过代码分析发现深层设计问题和重构机会。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "重构建议员", "role": "重构方案设计师", "goal": "为每个识别出的问题提供具体的重构方案，包含设计模式推荐和代码前后对比。", "backstory": "你是一位重构教练，善于用设计模式解决实际问题，提供渐进式的重构路线图。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "代码分析", "description": "分析代码库，按严重程度分类识别技术债务点，生成重构优先级列表。", "expected_output": "技术债务分析报告，含优先级排序和每个问题的根因分析。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "重构方案", "description": "为Top优先级问题设计重构方案，包含设计模式选择、代码示例和迁移步骤。", "expected_output": "重构方案文档，每个方案含前后对比代码和迁移步骤。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },

    # ------------------------------------------------------------------
    # 3b. 产品发布策略 (analysis)
    # ------------------------------------------------------------------
    {
        "name": "产品发布策略",
        "description": "制定全面的产品发布策略，包含目标用户定位、渠道规划、推广方案和效果评估框架。",
        "category": "analysis",
        "icon": "🚀",
        "difficulty": "intermediate",
        "process_type": "sequential",
        "tags": ["产品发布", "市场策略", "推广计划"],
        "agents_config": [
            {"name": "策略分析师", "role": "产品策略分析师", "goal": "分析市场和用户数据，制定产品发布的目标定位和核心策略。", "backstory": "你是一位产品发布策略专家，曾主导多款成功产品的发布策略制定。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "方案撰写员", "role": "策略方案撰写专家", "goal": "将策略分析转化为结构化的发布方案文档，确保可执行性。", "backstory": "你擅长将策略框架转化为具体的执行计划，考虑周全、细节到位。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "策略分析", "description": "分析目标市场、用户特征和竞争环境，制定产品发布的核心定位和差异化策略。", "expected_output": "发布策略分析报告，包含定位、目标用户分层和核心卖点。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "方案撰写", "description": "基于策略分析，撰写完整的发布方案，包含渠道规划、推广计划和时间线。", "expected_output": "产品发布方案文档，含执行时间线和资源需求。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "用户反馈分析",
        "description": "系统化分析用户反馈数据（评论、工单、NPS等），提取核心洞察和产品改进方向。",
        "category": "analysis",
        "icon": "💬",
        "difficulty": "beginner",
        "process_type": "sequential",
        "tags": ["用户反馈", "情感分析", "产品改进"],
        "agents_config": [
            {"name": "反馈分析员", "role": "用户反馈分析专家", "goal": "从多渠道收集的用户反馈中提取关键主题和情感趋势。", "backstory": "你是一位专注用户反馈的数据分析师，能从海量用户评论中识别出最有价值的洞察。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "改进建议员", "role": "产品改进顾问", "goal": "基于反馈分析结果，提出优先级排序的产品改进建议。", "backstory": "你是一位经验丰富的产品经理，擅长将用户反馈转化为具体的产品改进方案。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "反馈分析", "description": "分析用户反馈数据，按主题聚类、情感打分、频次排序，识别Top问题和趋势。", "expected_output": "用户反馈分析报告，含主题聚类、情感分析和频次统计。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "改进建议", "description": "基于反馈分析，按影响力和实现成本排序，提出具体的产品改进建议。", "expected_output": "产品改进建议清单，含优先级、影响评估和实现方案建议。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "风险评估报告",
        "description": "识别和分析项目/产品的潜在风险，评估影响和可能性，制定缓解策略和应急预案。",
        "category": "analysis",
        "icon": "⚠️",
        "difficulty": "advanced",
        "process_type": "sequential",
        "tags": ["风险评估", "项目管理", "决策支持"],
        "agents_config": [
            {"name": "风险识别员", "role": "风险管理专家", "goal": "系统化识别项目全生命周期的潜在风险，覆盖技术、市场、运营、合规四个维度。", "backstory": "你是一位PMP认证的项目管理专家，在多个大型项目中负责风险管理工作。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "评估分析师", "role": "风险量化分析师", "goal": "对识别出的风险进行影响评估和可能性分析，生成风险矩阵。", "backstory": "你擅长将定性风险转化为可量化的评估，帮助管理层做出明智的决策。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "风险识别", "description": "从技术、市场、运营、合规四个维度识别项目潜在风险，每个风险附详细描述。", "expected_output": "风险登记册，包含至少20个潜在风险的详细描述。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "风险评估", "description": "量化评估每个风险的影响程度和发生概率，生成风险矩阵和Top10风险清单。", "expected_output": "风险评估矩阵和Top10风险清单，含缓解策略建议。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },

    # ------------------------------------------------------------------
    # 4b. SOP流程文档 (document)
    # ------------------------------------------------------------------
    {
        "name": "SOP流程文档",
        "description": "为标准操作流程自动生成规范化的SOP文档，包含流程图描述、角色职责、检查清单。",
        "category": "document",
        "icon": "📋",
        "difficulty": "beginner",
        "process_type": "sequential",
        "tags": ["SOP", "流程文档", "标准化"],
        "agents_config": [
            {"name": "流程分析师", "role": "业务流程分析专家", "goal": "梳理业务流程的关键步骤、决策点和角色职责，设计高效的流程。", "backstory": "你是一位流程优化专家，擅长将复杂业务流程标准化和文档化。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "文档撰写员", "role": "技术文档撰写专家", "goal": "将流程分析结果转化为规范SOP文档，确保清晰易执行。", "backstory": "你是一位技术文档专家，撰写的SOP文档以清晰、完整、易执行而著称。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "流程分析", "description": "梳理目标流程的完整步骤，识别关键决策点、角色职责和输入输出。", "expected_output": "流程图描述和角色职责矩阵。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "SOP撰写", "description": "基于流程分析，撰写标准SOP文档：目的、范围、术语、流程图、详细步骤、检查清单。", "expected_output": "标准SOP文档，含所有必需章节。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "技术方案评审",
        "description": "对技术方案进行全面评审，评估架构合理性、技术选型、安全性和可扩展性，输出评审报告。",
        "category": "document",
        "icon": "📝",
        "difficulty": "advanced",
        "process_type": "sequential",
        "tags": ["技术评审", "架构评估", "技术选型"],
        "agents_config": [
            {"name": "架构评审员", "role": "技术架构评审专家", "goal": "从架构设计、技术选型、性能、安全、可扩展性等维度全面评审技术方案。", "backstory": "你是一位资深架构师，参与过多个大型系统的技术评审，对架构质量有敏锐的判断力。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "评审报告员", "role": "评审报告撰写专家", "goal": "将评审意见整理为结构化的评审报告，提供具体的改进建议。", "backstory": "你擅长将技术评审意见整理为清晰的报告，确保建议具体可执行。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "方案评审", "description": "按架构、安全、性能、可扩展性、可维护性五个维度评审技术方案，每个维度评分。", "expected_output": "技术方案评审意见，含五维度评分和具体问题描述。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "报告撰写", "description": "整理评审意见，撰写正式评审报告，包含评审结论、问题清单和改进建议。", "expected_output": "技术方案评审报告，含评审结论、问题清单和优先级排序的改进建议。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "会议纪要生成器",
        "description": "从会议录音文本或要点中自动生成结构化会议纪要，包含决议、行动项和责任人。",
        "category": "document",
        "icon": "🎙️",
        "difficulty": "beginner",
        "process_type": "sequential",
        "tags": ["会议纪要", "文档生成", "效率工具"],
        "agents_config": [
            {"name": "纪要整理员", "role": "会议纪要整理专家", "goal": "从会议内容中提取关键讨论点、决议和行动项。", "backstory": "你是一位专业会议记录员，擅长从冗长讨论中提炼核心要点和关键决策。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "纪要生成", "description": "基于会议内容，生成结构化纪要：会议主题、参与者、讨论要点、决议、行动项（含责任人和截止日期）。", "expected_output": "结构化会议纪要，含所有标准字段和行动项追踪表。", "output_type": "text", "agent_index": 0, "depends_on": []},
        ],
    },

    # ------------------------------------------------------------------
    # 5b. 学术论文润色 (literature)
    # ------------------------------------------------------------------
    {
        "name": "学术论文润色",
        "description": "对学术论文进行语言润色和格式规范化，提升论文的学术表达质量和发表成功率。",
        "category": "literature",
        "icon": "✍️",
        "difficulty": "beginner",
        "process_type": "sequential",
        "tags": ["论文润色", "学术写作", "语言优化"],
        "agents_config": [
            {"name": "论文润色师", "role": "学术论文润色专家", "goal": "优化论文的学术语言表达，确保语法、用词、句式符合高水平期刊标准。", "backstory": "你是一位资深学术编辑，为多本SCI期刊提供语言润色服务，精通英文学术写作规范。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "论文润色", "description": "润色论文全文，修正语法错误、优化句式结构、规范学术用语，保持原意的同时提升表达质量。", "expected_output": "润色后的论文全文，附修改说明。", "output_type": "text", "agent_index": 0, "depends_on": []},
        ],
    },
    {
        "name": "研究方法设计",
        "description": "根据研究课题设计科学的研究方法，包含实验设计、数据采集方案和分析方法选择。",
        "category": "literature",
        "icon": "🔬",
        "difficulty": "advanced",
        "process_type": "sequential",
        "tags": ["研究方法", "实验设计", "学术规范"],
        "agents_config": [
            {"name": "方法学顾问", "role": "研究方法学专家", "goal": "为研究课题设计科学合理的研究方法，确保方法论的严谨性和可行性。", "backstory": "你是一位研究方法学教授，精通定量和定性研究方法，帮助过众多博士生完成论文方法论设计。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
            {"name": "方案撰写员", "role": "研究方案撰写专家", "goal": "将方法论设计转化为规范的研究方案文档。", "backstory": "你擅长将方法论设计整理为结构清晰、论证充分的研究方案。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "方法设计", "description": "基于研究课题，设计研究方法：研究范式选择、实验/调查设计、采样方案、数据分析方法。", "expected_output": "研究方法设计文档，含方法论选择论证和详细执行方案。", "output_type": "text", "agent_index": 0, "depends_on": []},
            {"name": "方案撰写", "description": "撰写完整的研究方案，包含研究背景、方法设计、数据分析计划、预期结果和局限性讨论。", "expected_output": "完整的研究方案文档，符合学术规范。", "output_type": "text", "agent_index": 1, "depends_on": [0]},
        ],
    },
    {
        "name": "论文摘要生成",
        "description": "从论文全文中自动提取关键信息，生成符合期刊标准的精炼摘要，突出研究创新点和贡献。",
        "category": "literature",
        "icon": "📄",
        "difficulty": "beginner",
        "process_type": "sequential",
        "tags": ["论文摘要", "学术辅助", "内容提炼"],
        "agents_config": [
            {"name": "摘要撰写员", "role": "学术摘要撰写专家", "goal": "从论文中提炼核心内容，撰写精炼且有影响力的摘要。", "backstory": "你是一位学术写作专家，擅长将长篇论文浓缩为精炼的摘要，突出研究的创新点和学术贡献。", "llm_provider": "openai", "llm_model": "gpt-4o", "tools": []},
        ],
        "tasks_config": [
            {"name": "摘要生成", "description": "分析论文内容，提取背景、目的、方法、结果、结论五个核心要素，生成200-300字的规范摘要。", "expected_output": "符合期刊格式的论文摘要，200-300字。", "output_type": "text", "agent_index": 0, "depends_on": []},
        ],
    },

    # ------------------------------------------------------------------
    # 5. 文献综述生成 (original)
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


async def seed_templates(db: AsyncSession) -> dict[str, Any]:
    """
    向数据库写入预置模板。

    - 如果某个模板名称已存在则跳过（幂等）。
    - 返回本次操作的统计信息。
    """

    created: list[str] = []
    skipped: list[str] = []

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
