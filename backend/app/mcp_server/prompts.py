"""MCP Prompt templates — workflow_analysis, agent_optimization, execution_debugging.

提供结构化提示词，辅助用户分析工作流、优化 Agent 和调试执行错误。
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """将提示词模板注册到 FastMCP 服务器。"""

    @server.prompt()
    def workflow_analysis(
        workflow_name: str,
        workflow_description: str,
    ) -> str:
        """Analyze a workflow for potential improvements.

        Args:
            workflow_name: Name of the workflow to analyze.
            workflow_description: Description of the workflow's purpose.

        Returns:
            Analysis prompt text.
        """
        return (
            f"请对以下多智能体工作流进行全面分析：\n\n"
            f"**工作流名称**: {workflow_name}\n"
            f"**工作流描述**: {workflow_description}\n\n"
            f"请从以下维度进行分析：\n"
            f"1. 任务分解合理性 — 各子任务是否粒度适当、职责清晰\n"
            f"2. Agent 分配 — 每个 Agent 的角色与任务是否匹配\n"
            f"3. 依赖关系 — 任务间的依赖是否形成合理的执行顺序\n"
            f"4. 并行潜力 — 是否存在可并行执行但未并行的任务\n"
            f"5. 潜在瓶颈 — 可能导致延迟或失败的单点\n"
            f"6. 改进建议 — 具体的优化方案"
        )

    @server.prompt()
    def agent_optimization(
        agent_role: str,
        agent_goal: str,
        current_tools: str,
    ) -> str:
        """Get optimization suggestions for an agent's configuration.

        Args:
            agent_role: The role of the agent (e.g. "researcher").
            agent_goal: The goal the agent is trying to achieve.
            current_tools: Comma-separated list of current tools.

        Returns:
            Optimization prompt text.
        """
        return (
            f"请优化以下 Agent 配置：\n\n"
            f"**角色**: {agent_role}\n"
            f"**目标**: {agent_goal}\n"
            f"**当前工具**: {current_tools}\n\n"
            f"请提供：\n"
            f"1. 角色定义优化 — 更精准的角色描述和背景设定\n"
            f"2. 目标细化 — 将目标拆解为可衡量的子目标\n"
            f"3. 工具推荐 — 建议增加或替换的工具\n"
            f"4. 提示词建议 — System prompt 改进建议\n"
            f"5. 协作模式 — 与其他 Agent 的最佳协作方式"
        )

    @server.prompt()
    def execution_debugging(
        execution_id: str,
        error_message: str,
    ) -> str:
        """Help debug a failed workflow execution.

        Args:
            execution_id: The ID of the failed execution.
            error_message: The error message from the execution.

        Returns:
            Debugging prompt text.
        """
        return (
            f"请帮助调试以下工作流执行失败：\n\n"
            f"**执行 ID**: {execution_id}\n"
            f"**错误信息**: {error_message}\n\n"
            f"请分析：\n"
            f"1. 错误根因 — 最可能的失败原因\n"
            f"2. 影响范围 — 该错误对后续任务的影响\n"
            f"3. 修复方案 — 具体的修复步骤（按优先级排序）\n"
            f"4. 预防措施 — 避免类似问题再次发生的建议\n"
            f"5. 重试策略 — 是否可以安全重试，以及重试注意事项"
        )
