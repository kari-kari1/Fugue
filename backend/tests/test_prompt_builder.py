"""Prompt 构建器单元测试"""
from unittest.mock import MagicMock

import pytest

from app.engine.prompt_builder import (
    _build_tool_capability_prompt,
    build_memory_context,
    build_messages,
)

# ── 辅助工厂函数 ──────────────────────────────────

def _make_mock_agent(**kwargs):
    agent = MagicMock()
    agent.name = kwargs.get("name", "测试Agent")
    agent.role = kwargs.get("role", "研究员")
    agent.goal = kwargs.get("goal", "分析数据并撰写报告")
    agent.backstory = kwargs.get("backstory", "资深数据分析师")
    agent.system_prompt_template = kwargs.get("system_prompt_template", None)
    agent.id = kwargs.get("id", "agent-001")
    return agent


def _make_mock_task(**kwargs):
    task = MagicMock()
    task.name = kwargs.get("name", "数据分析任务")
    task.description = kwargs.get("description", "分析销售数据并生成CSV报告")
    task.expected_output = kwargs.get("expected_output", "CSV文件包含汇总统计")
    return task


# ── build_messages 测试 ────────────────────────────

def test_build_messages_includes_agent_info():
    """测试 build_messages 在 system prompt 中包含 Agent 信息"""
    agent = _make_mock_agent()
    task = _make_mock_task()
    messages = build_messages(agent, task, [])
    system = messages[0]["content"]
    assert agent.name in system
    assert agent.role in system
    assert agent.goal in system


def test_build_messages_includes_react_instructions():
    """测试 build_messages 包含 ReAct 推理框架指令"""
    agent = _make_mock_agent()
    task = _make_mock_task()
    messages = build_messages(agent, task, [])
    system = messages[0]["content"]
    assert "ReAct" in system or "推理" in system
    assert "Thought" in system or "分析" in system


def test_build_messages_includes_tools():
    """测试 build_messages 包含工具能力说明"""
    agent = _make_mock_agent()
    task = _make_mock_task()
    messages = build_messages(agent, task, [])
    system = messages[0]["content"]
    # 应包含工具相关章节
    assert "工具" in system
    assert any(kw in system for kw in ["fs_read", "file_read", "web_search"])


def test_build_messages_user_content():
    """测试 build_messages user 消息包含任务信息"""
    agent = _make_mock_agent()
    task = _make_mock_task()
    messages = build_messages(agent, task, [])
    user_msg = messages[1]["content"]
    assert task.name in user_msg
    assert task.description in user_msg
    assert task.expected_output in user_msg


def test_build_messages_with_context_parts():
    """测试 build_messages 正确处理上下文片段"""
    agent = _make_mock_agent()
    task = _make_mock_task()
    context = ["前置任务输出: 数据已清洗", "记忆: 上次使用了 pandas"]
    messages = build_messages(agent, task, context)
    user_msg = messages[1]["content"]
    assert "前置任务输出" in user_msg
    assert "记忆" in user_msg


def test_build_messages_with_workspace():
    """测试 build_messages 注入工作空间信息"""
    agent = _make_mock_agent()
    task = _make_mock_task()
    messages = build_messages(agent, task, [], workspace_dir="/tmp/test_ws")
    system = messages[0]["content"]
    assert "/tmp/test_ws" in system


def test_build_messages_with_system_prompt_template():
    """测试 system_prompt_template 存在时替代默认 system prompt"""
    agent = _make_mock_agent(
        system_prompt_template="你是自定义的 {role}，严格遵守安全规范。"
    )
    task = _make_mock_task()
    messages = build_messages(agent, task, [])
    system = messages[0]["content"]
    # system_prompt_template 替换了整个系统提示
    assert "严格遵守安全规范" in system


# ── _build_tool_capability_prompt 测试 ─────────────

def test_build_tool_capability_prompt_has_memory_tools():
    """测试工具能力提示包含记忆工具"""
    prompt = _build_tool_capability_prompt()
    assert "remember" in prompt
    assert "recall" in prompt
    assert "search_knowledge" in prompt
    assert "记忆管理" in prompt or "记忆" in prompt


def test_build_tool_capability_prompt_has_categories():
    """测试工具能力提示按分类组织"""
    prompt = _build_tool_capability_prompt()
    assert "文件操作" in prompt or "文档处理" in prompt or "网络与Web" in prompt


# ── build_memory_context 测试 ──────────────────────

@pytest.mark.asyncio
async def test_build_memory_context_handles_none_config():
    """测试 build_memory_context 在 memory_config 为 None 时返回空字符串"""
    agent = _make_mock_agent()
    task = _make_mock_task()
    execution = MagicMock()
    execution.crew_id = "crew-001"
    execution.id = "exec-001"

    result = await build_memory_context(None, agent, task, execution, None)
    assert result == ""


@pytest.mark.asyncio
async def test_build_memory_context_handles_disabled_config():
    """测试 build_memory_context 在记忆功能禁用时返回空字符串"""
    agent = _make_mock_agent()
    task = _make_mock_task()
    execution = MagicMock()
    execution.crew_id = "crew-001"

    config = MagicMock()
    config.short_term_enabled = False
    config.long_term_enabled = False

    result = await build_memory_context(None, agent, task, execution, config)
    assert result == ""
