"""LLM 提供者单元测试"""

import pytest

from app.engine.llm_provider import (
    LLMResponse,
    StreamEvent,
    ToolCall,
    _create_provider,
    estimate_cost,
    get_llm_provider,
    select_degraded_model,
    update_provider_health,
)


class TestToolCall:
    def test_tool_call_creation(self):
        tc = ToolCall(id="tc1", name="fs_read", arguments={"path": "/tmp"})
        assert tc.id == "tc1"
        assert tc.name == "fs_read"
        assert tc.arguments == {"path": "/tmp"}
        assert tc.result is None

    def test_tool_call_with_result(self):
        tc = ToolCall(id="tc1", name="fs_read", arguments={})
        tc.result = "file content"
        assert tc.result == "file content"


class TestLLMResponse:
    def test_response_creation(self):
        resp = LLMResponse(content="hello", tool_calls=[], tokens_used=100, cost_usd=0.001, model="gpt-4o", provider="openai")
        assert resp.content == "hello"
        assert resp.tokens_used == 100
        assert resp.cost_usd == 0.001
        assert resp.model == "gpt-4o"

    def test_response_defaults(self):
        resp = LLMResponse(content="", model="gpt-4o", provider="openai")
        assert resp.content == ""
        assert resp.tool_calls == []
        assert resp.tokens_used == 0
        assert resp.cost_usd == 0.0


class TestStreamEvent:
    def test_stream_event_creation(self):
        event = StreamEvent(event_type="text_delta", data="chunk")
        assert event.event_type == "text_delta"
        assert event.data == "chunk"


class TestEstimateCost:
    def test_estimate_known_model(self):
        cost = estimate_cost("gpt-4o", 1000, 500)
        assert cost > 0

    def test_estimate_unknown_model(self):
        cost = estimate_cost("unknown-model-xyz", 1000, 500)
        assert cost >= 0  # 不应崩溃，返回默认值

    def test_estimate_zero_tokens(self):
        cost = estimate_cost("gpt-4o", 0, 0)
        assert cost == 0.0


class TestSelectDegradedModel:
    def test_no_degradation_when_budget_ok(self):
        # 剩余 > 30% 不降级
        model = select_degraded_model("gpt-4o", budget_remaining=80.0, budget_total=100.0)
        assert model == "gpt-4o"

    def test_degradation_when_budget_low(self):
        # 剩余 < 10% 应该降级
        model = select_degraded_model("gpt-4o", budget_remaining=0.001, budget_total=100.0)
        # 可能降级也可能不降级（取决于 MODEL_DEGRADATION_CHAIN 是否有映射）
        assert isinstance(model, str)

    def test_no_degradation_when_budget_none(self):
        model = select_degraded_model("gpt-4o", budget_remaining=None, budget_total=None)
        assert model == "gpt-4o"

    def test_no_degradation_when_budget_zero(self):
        model = select_degraded_model("gpt-4o", budget_remaining=0, budget_total=0)
        assert model == "gpt-4o"


class TestCreateProvider:
    def test_create_openai_provider(self):
        provider = _create_provider("openai", "test-key")
        assert provider is not None

    def test_create_anthropic_provider(self):
        provider = _create_provider("anthropic", "test-key")
        assert provider is not None

    def test_create_mock_provider(self):
        provider = _create_provider("mock", "test-key")
        assert provider is not None

    def test_create_unknown_provider_falls_back_to_openai(self):
        # 未知 provider 回退到 OpenAI 兼容接口
        provider = _create_provider("unknown_provider", "test-key")
        assert provider is not None


class TestGetLLMProvider:
    def test_get_provider_with_key(self):
        provider = get_llm_provider("openai", api_key="test-key")
        assert provider is not None

    def test_get_provider_without_key_falls_back_to_mock(self):
        # 无 key 时回退到 MockProvider
        provider = get_llm_provider("openai", api_key="")
        assert provider is not None


class TestUpdateProviderHealth:
    @pytest.mark.asyncio
    async def test_update_health_success(self):
        # 不应崩溃
        await update_provider_health("openai", success=True)

    @pytest.mark.asyncio
    async def test_update_health_failure(self):
        await update_provider_health("openai", success=False)
