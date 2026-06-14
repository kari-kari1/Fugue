"""迭代引擎单元测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engine.executor import ExecutionEngine


def _make_bare_engine():
    """创建带有必需属性的裸引擎实例（跳过 __init__）"""
    engine = ExecutionEngine.__new__(ExecutionEngine)
    engine.llm_api_keys = {}
    engine.llm_base_urls = {}
    return engine


def test_executor_has_run_iteration():
    """测试执行引擎有run_iteration方法"""
    engine = _make_bare_engine()
    assert hasattr(engine, 'run_iteration')
    assert hasattr(engine, '_incremental_refine')
    assert hasattr(engine, '_reexecute_with_feedback')
    assert hasattr(engine, '_call_llm')
    assert hasattr(engine, '_call_llm_with_tools')
    assert hasattr(engine, '_get_agent_context')


def test_run_iteration_is_coroutine():
    """run_iteration 及其辅助方法应为协程"""
    import asyncio
    engine = _make_bare_engine()
    assert asyncio.iscoroutinefunction(engine.run_iteration)
    assert asyncio.iscoroutinefunction(engine._incremental_refine)
    assert asyncio.iscoroutinefunction(engine._reexecute_with_feedback)
    assert asyncio.iscoroutinefunction(engine._call_llm)
    assert asyncio.iscoroutinefunction(engine._call_llm_with_tools)
    assert asyncio.iscoroutinefunction(engine._get_agent_context)


@pytest.mark.asyncio
async def test_incremental_refine_demo_mode():
    """测试增量优化在演示模式（无API keys）下返回正确结构"""
    engine = _make_bare_engine()
    result = await engine._incremental_refine("原始输出", "请优化措辞")
    assert "output" in result
    assert "tokens_used" in result
    assert "cost_usd" in result
    # 演示模式返回 0 tokens 和 0 cost
    assert result["tokens_used"] == 0
    assert result["cost_usd"] == 0.0
    assert "[演示模式]" in result["output"]


@pytest.mark.asyncio
async def test_incremental_refine_with_history():
    """测试增量优化能通过 execution_id 注入历史上下文"""
    engine = _make_bare_engine()

    # mock _call_llm_with_tools 以捕获 prompt 内容
    captured_prompts = []

    async def mock_call(prompt, model=None, execution_id=None, **kwargs):
        captured_prompts.append(prompt)
        return {"output": "优化结果", "tokens_used": 100, "cost_usd": 0.02}

    with patch.object(engine, '_call_llm_with_tools', side_effect=mock_call):
        # 传入 execution_id，但历史查询会因数据库不可用而失败
        # 此时应静默降级，不影响执行
        result = await engine._incremental_refine("输出", "反馈", execution_id="fake-id")
        assert result["output"] == "优化结果"
        assert len(captured_prompts) == 1
        # 由于历史查询失败（数据库不可用），prompt 中应不包含历史部分
        assert "历史迭代记录" not in captured_prompts[0]


@pytest.mark.asyncio
async def test_reexecute_with_feedback_demo_mode():
    """测试重新执行模式在演示模式下返回正确结构"""
    engine = _make_bare_engine()

    # mock get_db_session 返回一个虚拟 session
    mock_execution = MagicMock()
    mock_execution.crew_id = "crew-001"
    mock_execution.results = {"outputs": {"task-1": "输出1"}}

    mock_crew = MagicMock()
    mock_crew.tasks = []
    mock_crew.agents = []

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_execution)

    # 构建 select 返回的 scalars mock
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = mock_crew
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch('app.engine.executor.get_db_session', return_value=mock_ctx):
        result = await engine._reexecute_with_feedback("exec-001", "不满意结果")

    assert "output" in result
    assert "tokens_used" in result
    assert "cost_usd" in result


@pytest.mark.asyncio
async def test_call_llm():
    """测试 LLM 调用（演示模式，无 API keys）"""
    engine = _make_bare_engine()
    result = await engine._call_llm("测试提示")
    assert "output" in result
    assert "tokens_used" in result
    assert "cost_usd" in result
    # 演示模式返回 0 tokens 和 0 cost
    assert result["tokens_used"] == 0
    assert result["cost_usd"] == 0.0
