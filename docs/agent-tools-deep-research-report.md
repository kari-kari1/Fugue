# AI Agent工具深度研究报告

> 研究日期：2026-06-09 | 研究方法：多Agent并行搜索 + 对抗验证 | 覆盖28个来源，45条可验证声明

---

## 1. 研究概述

本研究聚焦于2025-2026年主流AI Agent工具和多智能体编排框架，旨在为Fugue多智能体协作工作流平台提供具体可落地的改进方案。研究覆盖三个层面：

- **AI编码Agent工具**：Claude Code、OpenAI Codex CLI、Windsurf（原Codeium）、Cursor
- **多智能体编排框架**：CrewAI、LangGraph、AutoGen
- **核心技术标准与趋势**：MCP协议、Agent记忆系统、安全沙箱机制

---

## 2. 主流Agent工具分析

### 2.1 Claude Code

#### 架构设计与核心能力

Claude Code是Anthropic官方推出的命令行AI编码Agent，具备以下架构特点：

- **内置工具体系**：Bash（shell命令执行）、Read/Write/Edit（文件系统操作）、Grep/Glob（代码搜索）、Web Fetch/Search（在线资源获取）、Sub-agent spawning（委派任务给嵌套Claude实例）
- **多层次上下文记忆**：支持CLAUDE.md文件在多层级加载（项目根目录、父目录、home目录`~/.claude/CLAUDE.md`、子目录），每个会话启动时自动读取，提供持久化的跨会话记忆
- **无头/非交互模式**：通过`claude -p`支持headless模式，配合`--output-format json`或`stream-json`标志以及`--max-turns`限制Agent迭代次数，可集成到CI/CD流水线

#### MCP协议与工具调用机制

MCP（Model Context Protocol）是Anthropic创建并开源的开放标准，采用JSON-RPC 2.0作为其线协议。这是当前Agent工具互操作性领域最重要的标准化进展。

**三层架构**：Client-Host-Server架构中，Host创建并管理Client实例，每个Client与特定Server保持1:1关系，Server无法读取完整对话或看到其他Server

**两种传输机制**：
- Stdio：标准输入/输出流，适用于本地进程，零网络开销
- Streamable HTTP：HTTP POST + 可选SSE流式传输，替代了2024-11-05规范中的旧SSE传输

**生命周期三阶段**：初始化（能力协商通过initialize/initialized消息）、运行、关闭

**服务端原语**：
- Tools：模型控制的可执行函数，通过`tools/list`发现，`tools/call`调用
- Resources：上下文数据源，支持订阅
- Prompts：可复用模板

**客户端原语**：
- Sampling（`sampling/createMessage`允许Server请求Client的Host执行LLM补全）
- Elicitation（`elicitation/create`允许Server向用户请求信息）
- Logging

**版本演进**：
- 2024-11-05：初始规范，HTTP+SSE
- 2025-03-26：Streamable HTTP替代SSE，OAuth 2.1支持，工具注解
- 2025-11-25：最新版，Tasks支持，Elicitation增强，图标支持

#### 多智能体协作模式

Claude Code的子Agent系统具有以下特性：

- **独立上下文窗口**：每个子Agent拥有独立的上下文窗口，可并行工作
- **Git工作树集成**：通过Git worktree机制，每个子Agent拥有独立的隔离工作目录，避免文件冲突
- 这种设计实现了"一Agent一工作目录"的隔离模式，是当前AI编码Agent领域最先进的并行执行模型之一

### 2.2 OpenAI Codex CLI

#### 架构设计与沙箱模型

Codex CLI使用TypeScript/Node.js编写，采用Ink（React for CLI）构建终端UI，通过OpenAI Responses API通信，配置存储于`~/.codex/config.yaml`

**工具体系**（共4个工具）：
- `shell`：执行shell命令
- `apply_patch`：使用自定义patch格式的结构化文件diff应用
- `read_file`：返回带行号的文件内容
- `write_file`：创建或覆盖文件

**三级审批模式**：
- Suggest：所有操作需用户审批
- Auto-Edit：文件编辑自动执行，shell命令需审批
- Full-Auto：所有操作自动执行，但必须启用沙箱。有最大循环计数防止无限自主循环

**沙箱实现**：
- macOS：Apple Seatbelt沙箱框架（sandbox-exec）
- Linux：bubblewrap（bwrap）轻量级容器隔离，Docker容器作为更强隔离的替代方案
- 仅Full-Auto模式默认激活沙箱

#### 任务执行与并行能力

**Codex Cloud Agent**：在临时容器中运行，每个任务分配独立容器（clone仓库->执行->销毁），默认隔离无网络访问，使用最小系统权限，支持约5个并发Agent实例

#### Responses API内置工具

OpenAI Responses API（2025年3月发布）内置三大工具：web_search（实时网络搜索+来源引用）、code_interpreter（沙箱Python执行）、file_search（RAG文档检索），原生管理Agent循环无需手动实现工具调用迭代

#### 与Claude Code的对比

| 维度 | Claude Code | Codex CLI |
|------|-------------|-----------|
| 工具数量 | 7+类（Bash, Read, Write, Edit, Grep, Glob, Web等） | 4个（shell, apply_patch, read_file, write_file） |
| 文件修改方式 | Edit工具精确替换 | apply_patch自定义patch格式 |
| 并行能力 | 子Agent + Git worktree并行 | Cloud Agent ~5并发，CLI无并行 |
| 工具扩展 | MCP协议开放扩展 | Responses API内置工具 |
| 沙箱模型 | 依赖外部配置 | 原生seatbelt/bwrap集成 |
| 上下文管理 | CLAUDE.md多层加载 | config.yaml单一配置 |

### 2.3 Workbuddy/Windsurf/Cursor

#### Windsurf的Cascade引擎

Windsurf（由Codeium开发，2025年初被OpenAI以约30亿美元收购）采用独特的"Flow"范式：

- **持续上下文流**：维持持久化的上下文流而非传统的提示-响应交互模式
- **多层记忆系统**：跨越文件级、动作级、项目级和持久化Cascade Memories四个层次

#### Cursor的Agent模式

Cursor采用Plan-Act-Observe-Repeat循环：

- **RAG增强上下文**：使用索引嵌入的检索增强生成来构建上下文，而非将整个代码库加载到上下文中
- **Background Agents**：在独立的云VM/容器中生成，每个任务clone仓库并在独立Git分支上工作，支持异步执行（用户关闭笔记本后Agent继续工作）

---

## 3. 多智能体编排框架分析

### 3.1 CrewAI

#### 核心架构

CrewAI的四大核心组件：

- **Agent**：具有role（角色）、goal（目标）、backstory（背景故事）、tools（工具）
- **Task**：包含description（描述）、expected_output（预期输出）、output_pydantic（Pydantic输出模型）
- **Crew**：协调Agent并管理流程
- **Flow**：事件驱动编排层，使用@start、@listen、@router装饰器

#### 三种流程模式

- **Sequential**：Agent按顺序执行任务
- **Hierarchical**：Manager Agent自动协调任务分配并审查输出
- **Consensus**：实验性，Agent协作达成共识

#### 统一记忆系统（v1.14.6+）

CrewAI在v1.14.6版本实现了重大记忆系统升级：

- 用单一Memory类替代了之前分离的短期、长期、实体和外部记忆类型
- 保存时通过LLM分析推断scope、categories和importance
- 支持自适应深度召回，可配置recency（时间衰减）、semantic（语义相似度）和importance（重要性）权重

**记忆API**：
- `remember()`：存储
- `recall()`：复合评分检索
- `forget()`：基于scope的删除
- `extract_memories()`：从原始文本提取原子事实
- 支持基于路径的scope组织（如`/agent/researcher`），`memory.tree()`查看scope结构

### 3.2 LangGraph

#### 有向图/状态机模型

LangGraph将多智能体系统建模为有向图/状态机：

- **Nodes**（计算步骤）：每个节点是一个计算单元
- **Edges**（状态转移）：支持确定性和条件性转移
- **State**（共享数据结构）：在节点间传递的TypedDict/Pydantic结构

#### Command API（2025年引入）

实现显式的Agent间交接：
- `Command(goto='target_agent')`：Agent间任务转交
- `Command(update={...})`：交接前的状态更新
- `Command(resume=value)`：人机协作场景的状态注入

#### 检查点持久化

提供多级存储后端：
- MemorySaver（内存）、SqliteSaver、PostgresSaver、AsyncPostgresSaver
- 核心能力：基于thread_id的状态隔离、时间旅行调试（从任意检查点重放）、故障恢复

#### 人机协作（Human-in-the-Loop）

通过`interrupt_before`和`interrupt_after`参数在图节点上设置中断点，通过`update_state()`注入人类反馈后恢复执行

### 3.3 AutoGen

#### 事件驱动架构（0.4重写版）

AutoGen 0.4进行了完全重写：
- **AgentRuntime**：中央运行时，管理Agent生命周期和消息路由
- **Topics/Subscriptions**：发布/订阅模型，实现灵活的消息路由

#### 四种群聊编排模式

- **RoundRobinGroupChat**：确定性轮询
- **SelectorGroupChat**：基于LLM的发言者选择
- **Swarm**：动态Agent-to-Agent交接
- **MagenticOne**：高级多智能体编排

#### Magentic-One架构

由五个Agent组成：
- **Orchestrator**：规划、任务分配、进度跟踪、错误恢复，使用DAG-based Task Ledger跟踪子任务
- **WebSurfer**：网络导航/交互
- **FileSurfer**：本地文件操作（PDF/Word/Excel）
- **Coder**：代码编写和分析
- **ComputerTerminal**：代码和shell命令执行

---

## 4. 关键技术趋势（2025-2026）

### 4.1 工具调用标准化：MCP协议成为事实标准

MCP协议正迅速成为Agent工具互操作的行业标准。其关键设计决策包括：

- JSON-RPC 2.0线协议降低了集成门槛
- Client-Host-Server三层架构保证了安全隔离
- 从SSE到Streamable HTTP的传输演进适应了云原生部署需求
- Tasks扩展解决了长时间运行操作的状态管理问题
- 官方TypeScript和Python SDK降低了采用门槛

### 4.2 记忆与上下文管理演进

Agent记忆系统经历了三代演进：

**第一代 - 固定上下文窗口**：简单的对话历史截断，受限于模型上下文长度

**第二代 - 分层记忆**：Stanford Generative Agents开创的Memory Stream设计，基于recency（时间衰减）、importance（LLM推断评分）、relevance（语义相似度）三维检索，被CrewAI等框架广泛采用

**第三代 - 操作式记忆**：
- CrewAI统一记忆系统（v1.14.6+）：LLM驱动的自动scope/categorize/importance推断，路径式scope组织，复合评分召回
- Letta（原MemGPT）：受OS虚拟内存启发，将上下文窗口视为RAM，外部存储视为磁盘，通过函数调用在两者间交换数据，实现"无限"对话长度
- Mem0：三类记忆（用户记忆、Agent记忆、会话记忆），支持add/search/update/delete + 记忆评估

### 4.3 ReAct与工作流编排范式

**ReAct范式**（Reasoning + Acting）：扩展LLM的动作空间，包含任务特定离散动作和语言空间，遵循Thought -> Action -> Observation循环。Reflexion在此基础上增加动态记忆和自反思，将反思存储在工作记忆中（最多3条）

**Anthropic工作流模式**（五种）：
- Prompt Chaining（提示链）
- Routing（路由）
- Parallelization（并行化，含Sectioning和Voting变体）
- Orchestrator-Workers（编排者-工人）
- Evaluator-Optimizer（评估者-优化者）

关键洞察：最成功的实现避免复杂框架，倾向于简单可组合的模式。

### 4.4 安全与沙箱机制

行业共识正在形成：
- **Codex CLI**：原生集成OS级沙箱（macOS Seatbelt + Linux bwrap），Full-Auto模式强制沙箱
- **Codex Cloud**：默认空气隔离（无网络）、最小权限、临时容器
- **MCP**：Server间隔离（无法看到其他Server），Client-Server 1:1关系保证安全边界

### 4.5 异步与后台Agent

两种模式正在并行发展：
- **Cursor Background Agents**：云VM/容器中异步执行，用户可离线
- **Letta Sleep-time Agents**：用户空闲时执行后台处理
- **Codex Cloud Agent**：临时容器执行，支持~5并发

---

## 5. Fugue提升方案（18项具体建议）

### P0 — 核心架构改进（立即执行）

#### 建议1：实现完整的MCP Server层

**现状**：Fugue已集成MCP SDK 1.x，但仅用于基础连接，未实现标准MCP Server。

**改进方案**：将Fugue的Agent工具注册为标准MCP Server，暴露Tools、Resources、Prompts三类原语。
- Tools：每个Agent能力注册为MCP Tool（如"代码分析Agent"的`analyze_code`工具）
- Resources：将工作流模板、执行结果等注册为MCP Resources，支持订阅机制
- Prompts：将常用提示模板注册为MCP Prompts

**技术路径**：使用已安装的MCP SDK 1.x Python包，基于FastAPI SSE端点实现Streamable HTTP传输。

**对标**：Claude Code的MCP完整实现

**收益**：使Fugue Agent可被任何MCP Client（Claude Code、Cursor等）直接调用，实现生态互通。

---

#### 建议2：引入Git Worktree级别的执行隔离

**现状**：Fugue的执行引擎在共享文件系统上运行，多Agent并行执行时存在文件冲突风险。

**改进方案**：借鉴Claude Code的子Agent + Git worktree模型，为每个执行中的Agent分配独立的工作目录：
- 利用`git worktree add`为每个Agent创建隔离目录
- 执行完成后通过PR或merge操作合并结果
- 失败的工作树可安全丢弃，不影响其他Agent

**技术路径**：在Celery任务的`before_work`钩子中创建工作树，`after_work`中清理。需要引入`gitpython`库。

**收益**：从根本上解决多Agent并行执行的文件冲突问题，实现真正的并行安全。

---

#### 建议3：构建三层审批模式

**现状**：Fugue缺乏执行前的权限控制粒度，用户无法选择操作的自主级别。

**改进方案**：引入类似Codex CLI的三级审批模式：
- **Safe模式**：所有操作需用户确认（适合生产环境）
- **Semi-Auto模式**：低风险操作自动执行，高风险操作（如shell命令、外部API调用）需确认
- **Full-Auto模式**：所有操作自动执行，但强制启用沙箱和操作日志

**对标**：Codex CLI的Suggest/Auto-Edit/Full-Auto三模式

**技术路径**：在执行引擎的工具调用层（executor.py）中插入审批中间件，根据操作类型和当前模式决定是否暂停等待用户确认。通过WebSocket实时通知前端审批请求。

**收益**：用户可根据任务风险等级和信任程度灵活控制Agent自主权。

---

#### 建议4：实现Agent执行沙箱

**现状**：Fugue的Agent在无隔离环境中执行，存在安全风险。

**改进方案**：引入两级沙箱策略：
- **轻量级**：使用bubblewrap（bwrap）在Linux上实现文件系统和网络隔离
- **容器级**：对高风险操作使用Docker容器隔离，Air-gapped模式默认无网络

**对标**：Codex CLI的seatbelt/bwrap沙箱 + Codex Cloud的临时容器

**技术路径**：在Celery Worker中集成bwrap包装层，通过配置文件控制沙箱级别。可参考`subprocess`的`preexec_fn`参数实现。

**收益**：保障平台安全，特别是当Agent执行用户上传的工作流模板时。

---

### P1 — 功能特性增强（1-2月内）

#### 建议5：实现五种Anthropic工作流模式的可视化编排

**现状**：Fugue的ReactFlow画布主要支持线性Sequential流程。

**改进方案**：将Anthropic定义的五种工作流模式作为可视化节点类型：
- **Prompt Chain节点**：串行执行，前一个节点输出作为下一个节点输入
- **Router节点**：根据条件将任务路由到不同Agent分支
- **Parallel节点**：并行执行多个子分支（Sectioning变体）
- **Orchestrator节点**：动态分配任务给Worker Agent
- **Evaluator-Optimizer循环节点**：执行-评估-优化的自循环

**对标**：Anthropic "Building Effective Agents"五种模式 + LangGraph有向图模型

**技术路径**：扩展ReactFlow的自定义节点类型库，每个模式对应一种节点组件。后端executor.py中实现对应的执行逻辑。

**收益**：大幅扩展Fugue的编排能力覆盖范围，从"能用"到"好用"。

---

#### 建议6：实现基于路径scope的统一记忆系统

**现状**：Fugue Phase 2计划中的"记忆知识库"功能尚未实现。

**改进方案**：直接利用已集成的CrewAI v1.14.6+统一记忆系统，同时扩展路径式scope管理：
- 为每个Agent分配独立scope：`/project/{project_id}/agent/{agent_id}`
- 为每个任务创建临时scope：`/task/{task_id}`
- 跨Agent共享知识放在公共scope：`/project/{project_id}/shared`
- 支持`memory.tree()`查看scope结构

**对标**：CrewAI统一记忆系统的scope路径组织 + remember/recall/forget API

**技术路径**：在Fugue数据库中新增`agent_memories`表，使用向量数据库（如pgvector）存储记忆嵌入。通过CrewAI Memory API封装调用。

**收益**：实现Agent的知识积累和跨会话学习，是平台从"无状态工具"到"有状态助手"的关键跃迁。

---

#### 建议7：实现时间旅行调试

**现状**：Fugue有执行历史和迭代功能，但不支持从中间状态恢复执行。

**改进方案**：借鉴LangGraph的检查点机制，实现：
- 在每个Agent节点执行完毕后创建检查点（保存完整State）
- 支持从任意检查点重放（修改输入后重新执行后续节点）
- 故障恢复：执行失败时自动回退到最近的成功检查点

**对标**：LangGraph检查点持久化 + 时间旅行调试

**技术路径**：在executor.py的节点执行边界插入检查点逻辑。使用Redis存储快速检查点，PostgreSQL存储持久化检查点。前端在执行历史时间轴上标记检查点，支持"从此处重试"操作。

**收益**：显著提升调试体验，特别是对于复杂的多Agent工作流。

---

#### 建议8：实现Human-in-the-Loop中断点

**现状**：Fugue的迭代功能仅在执行完成后生效，执行过程中无法介入。

**改进方案**：支持在工作流节点上设置中断点：
- `interrupt_before`：节点执行前暂停等待人类输入
- `interrupt_after`：节点执行后暂停等待人类审查
- 通过WebSocket实时通知前端，前端提供"继续/修改/终止"操作
- 支持通过`update_state()`注入人类反馈后恢复执行

**对标**：LangGraph的interrupt机制 + Command(resume=value)

**技术路径**：利用已有的WebSocket执行监控通道，扩展支持双向交互。在executor.py中引入中断检查逻辑，配合Redis存储中断状态。

**收益**：使Fugue从"全自动"升级为"人机协作"，适配更多企业场景。

---

#### 建议9：实现CLAUDE.md式的分层项目记忆

**现状**：Fugue缺乏跨会话的项目级持久化记忆。

**改进方案**：实现多层级项目记忆文件系统：
- **项目级**：`AGENTS.md`文件存储项目约定、技术栈、编码规范
- **Agent级**：每个Agent可维护自己的经验文件
- **全局级**：用户偏好和常用配置
- 每次执行前自动加载相关记忆文件到上下文

**对标**：Claude Code的CLAUDE.md多层次加载机制

**技术路径**：在项目配置中增加`memory_files`字段，执行引擎在构建Agent上下文时自动注入。前端在项目设置页提供记忆文件编辑器。

**收益**：让Agent"记住"项目特定知识，减少重复解释，提升输出质量。

---

#### 建议10：实现无头模式API

**现状**：Fugue仅支持Web UI交互。

**改进方案**：提供完整的无头/非交互执行API：
- RESTful API触发工作流执行
- 支持JSON和流式JSON输出格式
- 通过`max_turns`参数限制Agent迭代次数
- 集成到CI/CD流水线（如GitHub Actions）

**对标**：Claude Code的`claude -p`无头模式

**技术路径**：扩展现有FastAPI端点，新增`/api/v1/workflows/{id}/run`端点，支持同步和异步两种模式。异步模式通过Celery执行，回调URL通知结果。

**收益**：支持Fugue融入DevOps流程，扩展使用场景。

---

### P2 — 高级特性（3-6月内）

#### 建议11：实现MCP Elicitation用户交互

利用MCP的Elicitation能力，允许Agent在执行过程中向用户请求确认、补充输入或选择项。对标MCP Elicitation原语（`elicitation/create`）。

#### 建议12：实现Magentic-One式Orchestrator-Workers编排

实现完整的Orchestrator-Workers编排：Orchestrator Agent负责任务分解、分配、进度跟踪和错误恢复，使用DAG-based Task Ledger跟踪子任务依赖关系。对标Magentic-One的五Agent架构。

#### 建议13：实现Agent-to-Agent显式交接

引入Command API式的Agent间交接：`goto(target_agent)`、`update(state_updates)`、`resume(value)`。对标LangGraph Command API。

#### 建议14：实现RAG增强的上下文构建

对项目代码库进行索引和嵌入，Agent执行时自动检索最相关的代码片段。对标Cursor的RAG增强上下文构建 + Responses API的file_search工具。

#### 建议15：实现事件驱动的Flow编排

引入事件驱动的Flow编排层：@start、@listen(event)、@router装饰器，支持跨Flow的事件传播。对标CrewAI Flow的事件驱动编排。

#### 建议16：实现复合评分的记忆检索

在记忆检索中引入三维复合评分：recency（时间衰减因子）、semantic（语义相似度）、importance（LLM推断的重要性评分）。对标Stanford Generative Agents三维检索模型 + CrewAI自适应深度recall。

#### 建议17：实现采样与LLM反向调用

实现MCP Sampling机制：Agent（作为MCP Server）可向Host请求LLM补全。对标MCP Sampling原语 + SEP-1577。

#### 建议18：实现MCP Tasks持久化执行

集成MCP Tasks扩展：将长时间运行的Agent任务包装为MCP Task，支持延迟结果检索和状态查询。对标MCP Tasks实验性扩展。

---

## 6. 实施路线图

### 短期（1-2周）— 夯实基础

| 周次 | 任务 | 建议编号 |
|------|------|----------|
| Week 1 | 实现完整MCP Server层（Tools + Resources + Prompts） | #1 |
| Week 1 | 实现三层审批模式（Safe/Semi-Auto/Full-Auto） | #3 |
| Week 2 | 实现Git Worktree执行隔离 | #2 |
| Week 2 | 实现CLAUDE.md式分层项目记忆 | #9 |

**里程碑**：Fugue Agent可作为标准MCP Server被外部工具调用，执行安全性和隔离性达到生产标准。

### 中期（1-2月）— 核心能力跃迁

| 周次 | 任务 | 建议编号 |
|------|------|----------|
| Week 3-4 | 五种Anthropic工作流模式可视化编排 | #5 |
| Week 3-4 | 基于路径scope的统一记忆系统 | #6 |
| Week 5-6 | Human-in-the-Loop中断点 | #8 |
| Week 5-6 | 时间旅行调试 | #7 |
| Week 7-8 | 无头模式API | #10 |
| Week 7-8 | Agent执行沙箱（bwrap + Docker） | #4 |

**里程碑**：Fugue具备生产级多Agent编排能力，支持人机协作和安全执行。

### 长期（3-6月）— 生态与智能化

| 阶段 | 任务 | 建议编号 |
|------|------|----------|
| Month 3 | MCP Elicitation用户交互 | #11 |
| Month 3 | Magentic-One式Orchestrator-Workers | #12 |
| Month 4 | Agent-to-Agent显式交接（Command API） | #13 |
| Month 4 | RAG增强上下文构建 | #14 |
| Month 5 | 事件驱动Flow编排 | #15 |
| Month 5 | 复合评分记忆检索 | #16 |
| Month 6 | MCP Sampling + Tasks持久化执行 | #17, #18 |

**里程碑**：Fugue成为具备完整MCP生态互操作性、智能化记忆管理和高级编排能力的工业级多Agent平台。

---

## 附录：建议优先级总览

| 编号 | 建议 | 优先级 | 对标工具 | 复杂度 |
|------|------|--------|----------|--------|
| 1 | 完整MCP Server层 | P0 | Claude Code MCP | 中 |
| 2 | Git Worktree执行隔离 | P0 | Claude Code Sub-agents | 中 |
| 3 | 三层审批模式 | P0 | Codex CLI审批模式 | 低 |
| 4 | Agent执行沙箱 | P0 | Codex CLI沙箱 | 高 |
| 5 | 五种工作流模式可视化 | P1 | Anthropic工作流模式 | 高 |
| 6 | 统一记忆系统 | P1 | CrewAI Memory | 中 |
| 7 | 时间旅行调试 | P1 | LangGraph检查点 | 中 |
| 8 | Human-in-the-Loop | P1 | LangGraph interrupt | 中 |
| 9 | 分层项目记忆 | P1 | Claude Code CLAUDE.md | 低 |
| 10 | 无头模式API | P1 | Claude Code CLI | 低 |
| 11 | MCP Elicitation | P2 | MCP规范 | 中 |
| 12 | Orchestrator-Workers | P2 | Magentic-One | 高 |
| 13 | Agent显式交接 | P2 | LangGraph Command | 中 |
| 14 | RAG上下文构建 | P2 | Cursor RAG | 中 |
| 15 | 事件驱动Flow编排 | P2 | CrewAI Flow | 高 |
| 16 | 复合评分记忆检索 | P2 | Stanford Generative Agents | 中 |
| 17 | MCP Sampling | P2 | MCP规范 | 低 |
| 18 | MCP Tasks持久化 | P2 | MCP规范 | 中 |
