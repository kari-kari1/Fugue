"""Prompt 构建器 — 组装发送给 LLM 的消息"""

import logging

from sqlalchemy import select

logger = logging.getLogger(__name__)


def _build_tool_capability_prompt(workspace_dir: str = None) -> str:
    """构建工具能力说明，注入到 system prompt 中

    动态收集所有已注册的工具（插件 + 内置），生成完整的能力说明。
    """
    # 核心工具描述 — 始终包含（不依赖插件系统）
    core_tool_descriptions = {
        "fs_read": "- **fs_read**: 读取本地文件内容。参数：path(文件路径), offset(起始行), limit(行数), encoding(编码)。支持所有文本文件。**请使用绝对路径**。",
        "fs_write": "- **fs_write**: 写入本地文件。参数：path(目标路径), content(内容), append(是否追加)。**这是首选的文件写入工具，可写入用户计算机的任意位置**（桌面、文档等）。请使用绝对路径如 C:/Users/xxx/Desktop/answer.txt。",
        "fs_list": "- **fs_list**: 列出目录内容。参数：path(目录路径)。浏览文件和目录结构。请使用绝对路径。",
        "file_read": "- **file_read**: 读取文件内容。参数：file_path(文件路径)。读取工作区内的文件。",
        # file_write 不再推荐 — 有沙箱限制，用 fs_write 代替
        "remember": "- **remember**: 记录重要信息到长期记忆。当你学到关键信息、得出结论或发现模式时使用。参数：content(内容), memory_type(conclusion/feedback/pattern), importance(0-5)。",
        "recall": "- **recall**: 搜索你的长期记忆库，检索相关历史信息。参数：query(搜索查询), top_k(返回数量)。",
        "search_knowledge": "- **search_knowledge**: 搜索知识库中的文档资料。参数：query(搜索查询), kb_name(知识库名，可选), top_k(返回数量)。",
    }

    # 增强工具描述
    enhanced_tool_descriptions = {
        "docx_read": "- **docx_read**: 读取 Word (.docx) 文档。参数：path(文件路径)。提取文档中的所有文本和表格内容。支持中文。",
        "docx_create": "- **docx_create**: 创建 Word (.docx) 文档。参数：path(保存路径如 C:/Users/HP/Desktop/output.docx), title(标题), paragraphs(段落列表), headings(标题列表), table_data(表格数据)。**需要创建Word文档时必须使用此工具**。",
        "csv_create": "- **csv_create**: 创建 CSV 文件。参数：path(保存路径), rows(二维数组，第一行为表头)。",
        "xlsx_read": "- **xlsx_read**: 读取 Excel (.xlsx) 文件。参数：path(文件路径), sheet_name(工作表名), max_rows(最大行数)。读取表格数据。",
        "csv_analyze": "- **csv_analyze**: 读取并分析 CSV 文件。参数：path(文件路径), max_rows(最大行数)。自动检测编码和分隔符，提供数值列统计。",
        "pdf_read": "- **pdf_read**: 读取 PDF 文件。参数：path(文件路径), max_pages(最大页数)。提取PDF中的文本和表格。",
        "json_query": "- **json_query**: 查询JSON数据。参数：data(JSON字符串), query(路径查询如 key.subkey), filter_key/filter_value(过滤)。支持嵌套查询和数组过滤。",
        "yaml_parse": "- **yaml_parse**: 解析YAML文件。参数：path(文件路径)。读取并解析YAML配置文件。",
        "table_format": "- **table_format**: 格式化表格数据。参数：data(JSON数组), format(grid/pipe/markdown/html)。将数据格式化为美观表格。",
        "regex_extract": "- **regex_extract**: 正则表达式提取。参数：text(文本), pattern(正则表达式), flags(标志)。从文本中提取匹配模式的数据。",
        "text_diff": "- **text_diff**: 文本差异比较。参数：text_a(文本A), text_b(文本B)。比较两段文本的差异。",
        "text_transform": "- **text_transform**: 文本转换。参数：text(文本), operation(操作)。支持：upper/lower/title/reverse/trim/strip_html/word_count/char_count/base64_encode/decode/url_encode/decode。",
        "word_frequency": "- **word_frequency**: 词频分析。参数：text(文本), top_n(前N个)。分析文本中高频词。",
        "file_search": "- **file_search**: 文件搜索。参数：directory(目录), pattern(通配符如 *.docx), recursive(是否递归)。搜索匹配的文件。",
        "file_grep": "- **file_grep**: 内容搜索。参数：directory(目录), keyword(关键词), file_pattern(文件类型限定)。在文件内容中搜索关键词。",
        "zip_list": "- **zip_list**: 查看ZIP内容。参数：path(ZIP文件路径)。列出ZIP压缩包中的文件。",
        "sqlite_query": "- **sqlite_query**: 查询SQLite数据库。参数：db_path(数据库路径), query(SQL查询), max_rows(最大行数)。仅允许SELECT。",
        "hash_generate": "- **hash_generate**: 生成哈希值。参数：text(文本), algorithm(md5/sha1/sha256/sha512)。",
        "url_parse": "- **url_parse**: 解析URL。参数：url(URL地址)。解析URL的各个组成部分。",
        "process_info": "- **process_info**: 获取系统信息。无参数。返回当前系统和环境信息。",
        "html_extract": "- **html_extract**: 提取HTML文本。参数：html(HTML内容), selector(CSS选择器)。从HTML中提取纯文本。",
        "markdown_render": "- **markdown_render**: Markdown转HTML。参数：markdown_text(Markdown文本)。",
        "image_info": "- **image_info**: 图片信息。参数：path(图片路径)。获取图片尺寸、格式、EXIF等信息。",
        "web_search": "- **web_search**: 互联网搜索。参数：query(搜索词), max_results(最大结果数)。搜索实时网络信息。",
        "api_call": "- **api_call**: 调用外部API。参数：url(地址), method(GET/POST等), headers(头), body(请求体)。发送HTTP请求。",
        "code_execute": "- **code_execute**: 执行代码。参数：language(python/javascript), code(代码)。在沙箱中执行代码。",
        "text_analysis": "- **text_analysis**: 文本分析。参数：text(文本), analysis_type(summarize/sentiment/keywords/classify/translate), target_language(翻译目标语言)。",
        "image_generation": "- **image_generation**: 生成图片。参数：prompt(描述), size(尺寸), style(风格)。使用DALL-E生成图片。",
    }

    # 收集可用工具（插件工具 + 内置工具）
    available_plugin_tools = set()
    try:
        from app.plugins.manager import get_plugin_manager
        manager = get_plugin_manager()
        available_plugin_tools = set(manager.tools.keys())
    except Exception as e:
        logger.debug(f"Plugin manager not available for tool capability: {e}")

    from app.engine.tools import _TOOL_REGISTRY
    available_builtin = set(_TOOL_REGISTRY.keys())

    all_available = available_plugin_tools | available_builtin

    # 构建工具说明
    all_descriptions = {**core_tool_descriptions, **enhanced_tool_descriptions}

    parts = ["\n\n## 你可用的工具"]
    parts.append("你拥有丰富的工具集，可以在执行任务时主动调用。以下是你可以使用的工具：")

    # 按分类组织
    categories = {
        "📁 文件操作": ["fs_read", "fs_write", "fs_list", "file_read", "file_search", "file_grep", "zip_list"],
        "📄 文档处理": ["docx_read", "docx_create", "xlsx_read", "csv_analyze", "csv_create", "pdf_read"],
        "🔧 数据处理": ["json_query", "yaml_parse", "table_format", "sqlite_query"],
        "✏️ 文本处理": ["regex_extract", "text_diff", "text_transform", "word_frequency", "text_analysis"],
        "🌐 网络与Web": ["web_search", "api_call", "url_parse", "html_extract", "markdown_render"],
        "💻 代码执行": ["code_execute"],
        "🖼️ 媒体工具": ["image_info", "image_generation"],
        "⚙️ 系统工具": ["process_info", "hash_generate"],
        "🧠 记忆管理": ["remember", "recall", "search_knowledge"],
    }

    for cat_name, tool_names in categories.items():
        cat_tools = []
        for name in tool_names:
            if name in all_descriptions and name in all_available:
                cat_tools.append(all_descriptions[name])
        if cat_tools:
            parts.append(f"\n### {cat_name}")
            parts.extend(cat_tools)

    parts.append("\n## 工具使用指南")
    parts.append("1. **读取文件**：用 fs_read 或 docx_read 读取文件。**必须使用绝对路径**如 C:/Users/HP/Desktop/test.docx")
    parts.append("2. **保存结果到文件**：**必须使用 fs_write**。格式：fs_write(path='完整路径', content='内容')")
    parts.append("3. **搜索文件**：用 file_search 搜索文件，file_grep 搜索文件内容")
    parts.append("4. **处理数据**：用 json_query 处理JSON，csv_analyze 分析CSV")
    parts.append("5. **代码执行**：用 code_execute 运行Python/JavaScript代码")

    parts.append("\n## 严格规则（违反将导致任务失败）")
    if workspace_dir:
        parts.append(f"- 🔴 **工作空间限制**：所有文件必须保存在 {workspace_dir} 内，禁止保存到其他位置")
    parts.append("- **写文件用 fs_write**：需要创建或写入文件时，必须调用 fs_write 工具，不要用 code_execute 写文件")
    parts.append("- **复用已知路径**：当 file_search 或 fs_list 返回了文件的完整路径后，后续操作直接使用该路径，不要再次搜索")
    parts.append("- **最少工具调用**：每一步只调用必要的工具，避免冗余搜索")

    parts.append("\n## 文本工具调用协议（备用）")
    parts.append("如果你无法通过 function calling 调用工具，请使用以下格式在回复中嵌入工具调用：")
    parts.append("```tool_call")
    parts.append('{"tool": "工具名", "args": {"参数名": "参数值"}}')
    parts.append("```")
    parts.append("示例：读取文件")
    parts.append("```tool_call")
    parts.append('{"tool": "docx_read", "args": {"path": "C:/Users/HP/Desktop/test.docx"}}')
    parts.append("```")
    parts.append("系统会自动执行工具调用并将结果返回给你。每轮只能嵌入一个 tool_call。")

    return "\n".join(parts)


def build_messages(agent, task, context_parts: list[str], workspace_dir: str = None) -> list[dict[str, str]]:
    """构建 system + user 消息。

    Args:
        agent: Agent 模型实例
        task: Task 模型实例
        context_parts: 上下文片段列表（依赖输出、记忆等）
        workspace_dir: 工作空间目录（可选）

    Returns:
        OpenAI 格式的消息列表
    """
    system = f"你是{agent.name}，你的角色是{agent.role}。"
    if agent.goal:
        system += f"\n你的目标：{agent.goal}"
    if agent.backstory:
        system += f"\n你的背景：{agent.backstory}"
    if agent.system_prompt_template:
        system = agent.system_prompt_template

    # 注入工作空间信息
    if workspace_dir:
        system += "\n\n## ⚠️ 工作空间（强制）\n"
        system += f"你的工作空间目录是：**{workspace_dir}**\n"
        system += "所有文件的读取和写入必须在此目录下进行。\n"
        system += f"保存文件时，路径必须以 {workspace_dir} 开头，例如：{workspace_dir}/output.docx\n"
        system += "禁止在工作空间以外的任何路径创建或修改文件。\n"

    # 注入常用路径提示（减少无效搜索）
    import os
    home = os.path.expanduser("~")
    common_dirs = {
        "桌面": os.path.join(home, "Desktop"),
        "文档": os.path.join(home, "Documents"),
        "下载": os.path.join(home, "Downloads"),
    }
    system += "\n\n## 常用目录\n"
    for label, path in common_dirs.items():
        if os.path.isdir(path):
            system += f"- {label}: {path}\n"
    system += "当任务涉及文件时，优先在这些目录中搜索，不要从根目录开始盲目遍历。"

    # ReAct 推理框架指令 — 提升 Agent 推理链深度
    system += "\n\n## 推理方法（ReAct — 推理+行动）"
    system += "\n在执行任务时，请遵循以下推理循环："
    system += "\n1. **分析**（Thought）：思考当前状态、已获得的信息、还需要什么"
    system += "\n2. **行动**（Action）：选择合适的工具并调用它"
    system += "\n3. **观察**（Observation）：分析工具返回的结果，判断是否满足需求"
    system += "\n4. **决策**：如果任务完成 → 给出最终答案；如果还需要更多信息 → 回到步骤1"
    system += "\n\n## Chain-of-Thought 引导"
    system += "\n- 在调用任何工具之前，先在心中逐步推理：我需要什么信息？哪些工具能提供它？"
    system += "\n- 每次获得工具结果后，评估：这个结果有用吗？我还缺什么？下一步该做什么？"
    system += "\n- 任务完成时自检：我是否满足了所有要求？输出格式是否符合预期？"

    # 注入工具能力说明
    system += _build_tool_capability_prompt(workspace_dir=workspace_dir)

    user_msg = f"请执行以下任务：\n\n**{task.name}**\n\n{task.description}"
    if task.expected_output:
        user_msg += f"\n\n期望的输出格式：{task.expected_output}"
    if context_parts:
        user_msg += "\n\n--- 上下文信息 ---\n" + "\n\n".join(context_parts)

    return [{"role": "system", "content": system}, {"role": "user", "content": user_msg}]


async def build_memory_context(db, agent, task, execution, memory_config) -> str:
    """构建记忆上下文（短期记忆 + RAG 知识库），失败时优雅降级返回空字符串。

    Args:
        db: 数据库会话
        agent: Agent 模型实例
        task: Task 模型实例
        execution: Execution 模型实例
        memory_config: MemoryConfig 模型实例（可为 None）

    Returns:
        格式化的记忆上下文字符串，无记忆时返回空字符串
    """
    if not memory_config:
        return ""

    if not memory_config.short_term_enabled and not memory_config.long_term_enabled:
        return ""

    try:
        from app.services.memory_service import MemoryService
        memory_service = MemoryService(db)

        parts = []

        # ── 分层项目记忆（数据库 + 文件系统）─────────────────
        # 1) 项目级记忆：优先数据库，其次文件系统 AGENTS.md
        try:
            from app.models.crew import Crew
            crew_result = await db.execute(
                select(Crew).where(Crew.id == execution.crew_id)
            )
            crew = crew_result.scalar_one_or_none()
            if crew and getattr(crew, 'project_memory', None):
                parts.append("[项目约定]\n" + crew.project_memory[:4000])

            # 文件系统：扫描 workspace_dir 下的 AGENTS.md 和 .fugue/ 目录
            workspace = getattr(crew, 'workspace_dir', None) if crew else None
            if workspace:
                import os as _os
                ws_path = _os.path.expanduser(workspace)

                # AGENTS.md — 先检查 .fugue/AGENTS.md，其次工作空间根目录
                af_dir = _os.path.join(ws_path, '.fugue')
                agents_md_paths = [
                    _os.path.join(af_dir, 'AGENTS.md'),
                    _os.path.join(ws_path, 'AGENTS.md'),
                ]
                for agents_md in agents_md_paths:
                    if _os.path.isfile(agents_md):
                        try:
                            content = open(agents_md, encoding='utf-8').read()[:4000]
                            if content.strip():
                                parts.append(f"[项目约定]\n{content}")
                            break
                        except Exception as e:
                            logger.debug(f"Failed to read project convention file: {e}")

                # .fugue/ 目录 — Agent级经验文件和输出文件
                if _os.path.isdir(af_dir):
                    for fname in sorted(_os.listdir(af_dir)):
                        fpath = _os.path.join(af_dir, fname)
                        if _os.path.isfile(fpath) and fname.endswith(('.md', '.txt')):
                            try:
                                content = open(fpath, encoding='utf-8').read()[:2000]
                                if content.strip():
                                    label = fname.replace('.md', '').replace('.txt', '').replace('-', ' ').replace('_', ' ')
                                    parts.append(f"[{label}]\n{content}")
                            except Exception as e:
                                logger.debug(f"Failed to read agent experience file: {e}")
                    # 也扫描 outputs/ 子目录中的历史输出文件
                    outputs_dir = _os.path.join(af_dir, 'outputs')
                    if _os.path.isdir(outputs_dir):
                        for fname in sorted(_os.listdir(outputs_dir))[-3:]:  # 最多取最近3个
                            fpath = _os.path.join(outputs_dir, fname)
                            if _os.path.isfile(fpath) and fname.endswith('.md'):
                                try:
                                    content = open(fpath, encoding='utf-8').read()[:1500]
                                    if content.strip():
                                        parts.append(f"[上次输出: {fname}]\n{content}")
                                except Exception as e:
                                    logger.debug(f"Failed to read historical output: {e}")
        except Exception as e:
            logger.warning(f"Failed to load filesystem memory context: {e}")

        # 2) Agent级经验（数据库）
        if getattr(agent, 'agent_experience', None):
            parts.append(f"[Agent {agent.name} 经验]\n" + agent.agent_experience[:2000])

        # 3) 系统记忆（短期记忆 + RAG 知识库检索）
        ctx = await memory_service.build_agent_context(
            agent_id=str(agent.id),
            execution_id=str(execution.id),
            current_task={"description": task.description or ""},
            memory_config=memory_config,
        )

        # 短期记忆
        short_term = ctx.get("short_term_memory", [])
        if short_term:
            lines = []
            for item in short_term:
                result_text = (item.get("result") or "")[:500]
                if result_text:
                    lines.append(f"- {result_text}")
            if lines:
                parts.append("[短期记忆 - 最近任务结果]\n" + "\n".join(lines))

        # RAG 知识库检索
        kb_results = ctx.get("knowledge_base_results", [])
        if kb_results:
            lines = []
            for item in kb_results:
                content = (item.get("content") or "")[:500]
                if content:
                    lines.append(f"- {content}")
            if lines:
                parts.append("[知识库参考]\n" + "\n".join(lines))

        # P1-2: Agent 长期记忆召回
        if memory_config.long_term_enabled:
            try:
                query = current_task.get("description", "") if 'current_task' in dir() else ""
                if not query:
                    query = task.description or ""
                if query:
                    memories = await memory_service.recall_memories_scored(
                        agent_id=str(agent.id),
                        query=query,
                        top_k=memory_config.top_k,
                    )
                    if memories:
                        mem_lines = []
                        for m in memories:
                            mem_lines.append(f"- [{m.get('memory_type', '记忆')}] {m['content'][:200]}")
                        parts.append("[Agent 记忆]\n" + "\n".join(mem_lines))
            except Exception as mem_err:
                logger.warning(f"记忆召回失败（已跳过）: {mem_err}")

        return "\n\n".join(parts) if parts else ""

    except Exception as e:
        logger.warning(f"记忆上下文构建失败（已跳过）: {e}")
        return ""
