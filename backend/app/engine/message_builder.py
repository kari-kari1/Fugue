"""消息构建器 — 从 executor.py 拆分

负责: 上下文构建、LLM provider 初始化、工具 schema 聚合、消息历史管理。
报告 P0-4 要求拆分 executor.py 为独立模块。
"""

import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.execution import Execution
from app.models.task import Task
from app.engine.tools import get_openai_tools, get_anthropic_tools, get_plugin_tool_schemas
from app.services.event_publisher import event_publisher

logger = logging.getLogger(__name__)


async def prepare_task_context(
    engine,
    db: AsyncSession,
    execution: Execution,
    task: Task,
    agent: Agent,
    task_outputs: Dict[str, str],
    attempt: int,
    max_retries: int,
) -> Tuple[list, object, list, bool, int, str]:
    """准备任务执行上下文。

    Returns: (messages, llm, tool_schemas, is_anthropic, timeout, effective_model)
    """
    from app.engine.llm_provider import get_llm_provider, MockProvider, select_degraded_model

    # 构建上下文
    context_parts = []
    for dep_id in (task.context_task_ids or []):
        if dep_id in task_outputs:
            context_parts.append(f"[依赖任务输出]:\n{task_outputs[dep_id]}")

    memory_context = await engine._build_memory_context(db, agent, task, execution)
    if memory_context:
        context_parts.append(memory_context)

    context_parts = await engine._inject_attachments(task, context_parts)
    messages = engine._build_messages(agent, task, context_parts)

    engine._add_trace(execution, "agent.thinking", agent_name=agent.name,
                      data={"step": f"调用LLM (尝试 {attempt+1}/{max_retries})"})

    await event_publisher.publish_agent_thinking(
        execution_id=engine.execution_id,
        agent_name=agent.name,
        thought=f"准备调用LLM (尝试 {attempt+1}/{max_retries})",
        step="llm_call",
    )

    # LLM provider
    provider_key = engine.llm_api_keys.get(agent.llm_provider)
    provider_url = engine.llm_base_urls.get(agent.llm_provider)
    llm = get_llm_provider(
        agent.llm_provider,
        api_key=provider_key,
        base_url=provider_url,
        all_keys=engine.llm_api_keys,
        all_base_urls=engine.llm_base_urls,
    )

    if isinstance(llm, MockProvider):
        warning_msg = (
            f"Agent [{agent.name}] 的 LLM Provider '{agent.llm_provider}' "
            f"未找到有效 API Key，已回退到演示模式（Mock）。"
            f"输出为模拟数据，请在「设置」中配置 API Key。"
        )
        logger.warning(warning_msg)
        engine._add_trace(execution, "agent.warning", agent_name=agent.name, data={"step": warning_msg})

    timeout = task.timeout_seconds or 300
    is_anthropic = agent.llm_provider == "anthropic"
    tool_schemas = build_tool_schemas(agent, is_anthropic)

    effective_model = select_degraded_model(
        agent.llm_model,
        budget_remaining=(getattr(engine, '_cost_budget', None) or 0) - (execution.total_cost_usd or 0),
        budget_total=getattr(engine, '_cost_budget', None),
    )

    return messages, llm, tool_schemas, is_anthropic, timeout, effective_model


def build_tool_schemas(agent: Agent, is_anthropic: bool) -> list:
    """聚合 agent 配置、MCP、插件的工具 schema"""
    agent_tool_names = agent.tools_config or []
    tool_schemas = []

    if agent_tool_names:
        tool_schemas = get_anthropic_tools(agent_tool_names) if is_anthropic else get_openai_tools(agent_tool_names)

    from app.engine.mcp_adapter import get_mcp_adapter
    mcp_schemas = get_mcp_adapter().get_tool_schemas()
    if mcp_schemas:
        tool_schemas = (tool_schemas or []) + mcp_schemas

    provider_fmt = "anthropic" if is_anthropic else "openai"
    plugin_schemas = get_plugin_tool_schemas(provider_fmt)
    if plugin_schemas:
        tool_schemas = (tool_schemas or []) + plugin_schemas

    if not agent_tool_names and not tool_schemas:
        builtin = get_openai_tools(["web_search", "file_read", "file_write", "code_execute", "api_call", "text_analysis", "pdf_create", "remember", "recall", "search_knowledge"])
        if builtin:
            tool_schemas = builtin

    logger.info(
        "[EXECUTOR] Agent '%s' tools: agent_config=%d, plugin=%d, total=%d",
        agent.name, len(agent_tool_names), len(plugin_schemas or 0), len(tool_schemas or 0),
    )
    return tool_schemas


def append_tool_messages(messages: list, llm_response, is_anthropic: bool):
    """将工具调用和结果追加到消息历史"""
    import json

    if is_anthropic:
        assistant_blocks = []
        if llm_response.content:
            assistant_blocks.append({"type": "text", "text": llm_response.content})
        for tc in llm_response.tool_calls:
            assistant_blocks.append({"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.arguments})
        messages.append({"role": "assistant", "content": assistant_blocks})
        tool_result_blocks = []
        for tc in llm_response.tool_calls:
            tool_result_blocks.append({
                "type": "tool_result", "tool_use_id": tc.id,
                "content": (tc.result or "")[:8000],
            })
        messages.append({"role": "user", "content": tool_result_blocks})
    else:
        assistant_msg = {"role": "assistant", "content": llm_response.content or ""}
        assistant_msg["tool_calls"] = [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)}}
            for tc in llm_response.tool_calls
        ]
        messages.append(assistant_msg)
        for tc in llm_response.tool_calls:
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": (tc.result or "")[:8000]})
