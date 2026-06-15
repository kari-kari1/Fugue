"""LLM提供商抽象层 - 直接调用各厂商API"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """工具调用请求"""
    id: str
    name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None


@dataclass
class LLMResponse:
    """LLM响应标准化"""
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw_response: Dict[str, Any] = field(default_factory=dict)


class StreamEvent:
    """流式事件"""
    def __init__(self, event_type: str, data: Any = None):
        self.event_type = event_type  # 'text_delta', 'tool_call_start', 'tool_call_delta', 'tool_call_end', 'done'
        self.data = data

class BaseLLMProvider(ABC):
    """LLM提供商基类"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        ...

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        """流式聊天 — 默认回退到非流式"""
        resp = await self.chat(messages, model, temperature, max_tokens, tools)
        if resp.content:
            yield StreamEvent("text_delta", resp.content)
        for tc in resp.tool_calls:
            yield StreamEvent("tool_call_start", {"id": tc.id, "name": tc.name})
            yield StreamEvent("tool_call_delta", {"id": tc.id, "arguments": json.dumps(tc.arguments, ensure_ascii=False)})
            yield StreamEvent("tool_call_end", {"id": tc.id})
        yield StreamEvent("done", resp)

    @abstractmethod
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        ...


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API提供商"""

    BASE_URL = "https://api.openai.com/v1"

    # 每1000 token的价格（美元）
    PRICING = {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        start = time.monotonic()

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        duration = int((time.monotonic() - start) * 1000)

        message = data["choices"][0]["message"]
        content = message.get("content") or ""

        # 解析 tool_calls
        parsed_tool_calls = []
        raw_calls = message.get("tool_calls") or []
        for tc in raw_calls:
            func = tc.get("function", {})
            import json as _json
            try:
                args = _json.loads(func.get("arguments", "{}"))
            except _json.JSONDecodeError:
                args = {}
            parsed_tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                arguments=args,
            ))

        return LLMResponse(
            content=content,
            model=model,
            provider="openai",
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=self.calculate_cost(model, prompt_tokens, completion_tokens),
            duration_ms=duration,
            tool_calls=parsed_tool_calls,
            raw_response=data,
        )

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = self.PRICING.get(model, self.PRICING.get("gpt-4o"))
        return (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1000

    async def chat_stream(self, messages, model="gpt-4o", temperature=0.7, max_tokens=4096, tools=None):
        """流式聊天 — 逐 token 返回文本和工具调用。流式失败时自动回退到非流式。"""
        import json as _json

        try:
            payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
            if tools:
                payload["tools"] = tools

            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                ) as resp:
                    resp.raise_for_status()

                    content_buffer = ""
                    tool_calls_state = {}
                    prompt_tokens = 0
                    completion_tokens = 0

                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = _json.loads(data_str)
                        except _json.JSONDecodeError:
                            continue

                        usage = chunk.get("usage")
                        if usage:
                            prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                            completion_tokens = usage.get("completion_tokens", completion_tokens)

                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        text = delta.get("content") or ""
                        if text:
                            content_buffer += text
                            yield StreamEvent("text_delta", text)

                        for tc_delta in delta.get("tool_calls", []):
                            idx = tc_delta.get("index", 0)
                            tc_id = tc_delta.get("id", "")
                            func = tc_delta.get("function", {})
                            func_name = func.get("name", "")
                            func_args_delta = func.get("arguments", "")
                            if tc_id and idx not in tool_calls_state:
                                tool_calls_state[idx] = {"id": tc_id, "name": func_name, "args_buffer": ""}
                                yield StreamEvent("tool_call_start", {"id": tc_id, "name": func_name})
                            if idx in tool_calls_state:
                                if func_name:
                                    tool_calls_state[idx]["name"] = func_name
                                tool_calls_state[idx]["args_buffer"] += func_args_delta

                        finish = chunk.get("choices", [{}])[0].get("finish_reason")
                        if finish == "tool_calls":
                            for idx in sorted(tool_calls_state.keys()):
                                tc = tool_calls_state[idx]
                                yield StreamEvent("tool_call_delta", {"id": tc["id"], "arguments": tc["args_buffer"]})
                                yield StreamEvent("tool_call_end", {"id": tc["id"]})

                    parsed_tool_calls = []
                    for idx in sorted(tool_calls_state.keys()):
                        tc = tool_calls_state[idx]
                        try:
                            args = _json.loads(tc["args_buffer"] or "{}")
                        except _json.JSONDecodeError:
                            args = {}
                        parsed_tool_calls.append(ToolCall(id=tc["id"], name=tc["name"], arguments=args))

                    total = prompt_tokens + completion_tokens
                    final_resp = LLMResponse(
                        content=content_buffer, model=model, provider="openai",
                        tokens_used=total, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                        cost_usd=self.calculate_cost(model, prompt_tokens, completion_tokens),
                        tool_calls=parsed_tool_calls,
                    )
                    yield StreamEvent("done", final_resp)

        except Exception as e:
            # 流式失败 → 回退到非流式
            logger.warning(f"Streaming failed ({e}), falling back to non-streaming")
            resp = await self.chat(messages, model, temperature, max_tokens, tools)
            if resp.content:
                yield StreamEvent("text_delta", resp.content)
            for tc in resp.tool_calls:
                yield StreamEvent("tool_call_start", {"id": tc.id, "name": tc.name})
                yield StreamEvent("tool_call_end", {"id": tc.id})
            yield StreamEvent("done", resp)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API提供商"""

    BASE_URL = "https://api.anthropic.com/v1"

    PRICING = {
        "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    }

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        start = time.monotonic()

        # Anthropic API要求system消息单独传
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)

        body: Dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_msg:
            body["system"] = system_msg

        # Anthropic tools 格式
        if tools:
            body["tools"] = tools

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens
        duration = int((time.monotonic() - start) * 1000)

        content = ""
        parsed_tool_calls = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            elif block.get("type") == "tool_use":
                parsed_tool_calls.append(ToolCall(
                    id=block.get("id", ""),
                    name=block.get("name", ""),
                    arguments=block.get("input", {}),
                ))

        return LLMResponse(
            content=content,
            model=model,
            provider="anthropic",
            tokens_used=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=self.calculate_cost(model, prompt_tokens, completion_tokens),
            duration_ms=duration,
            tool_calls=parsed_tool_calls,
            raw_response=data,
        )

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = self.PRICING.get(model, self.PRICING.get("claude-sonnet-4-20250514"))
        return (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1000


class MockProvider(BaseLLMProvider):
    """Mock提供商 - 用于演示和测试，无需API Key"""

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "mock-model",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        import asyncio
        start = time.monotonic()

        # 提取用户消息来生成有意义的回复
        user_msg = ""
        system_msg = ""
        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
            elif msg["role"] == "system":
                system_msg = msg["content"]

        # 模拟思考延迟
        await asyncio.sleep(0.5)

        # Mock模式不模拟工具调用，直接生成文本回复
        # （工具调用结果是假数据，会误导用户）

        # 根据角色和任务生成模拟回复
        role = "助手"
        if "角色是" in system_msg:
            role = system_msg.split("角色是")[1].split("。")[0].split("\n")[0].strip()

        task_name = ""
        if "**" in user_msg:
            parts = user_msg.split("**")
            if len(parts) >= 2:
                task_name = parts[1].strip()

        content = self._generate_response(role, task_name, user_msg)
        duration = int((time.monotonic() - start) * 1000)
        tokens = len(content) // 2

        return LLMResponse(
            content=content,
            model=model,
            provider="mock",
            tokens_used=tokens,
            prompt_tokens=tokens // 2,
            completion_tokens=tokens // 2,
            cost_usd=0.0,
            duration_ms=duration,
        )

    def _generate_response(self, role: str, task_name: str, user_msg: str) -> str:
        """根据实际任务内容生成模拟回复（明确标识为演示模式）"""
        # 从 user_msg 中提取任务描述
        task_desc = ""
        if user_msg:
            # 提取 "请执行以下任务：" 之后的内容
            if "请执行以下任务：" in user_msg:
                task_desc = user_msg.split("请执行以下任务：", 1)[1].strip()
            else:
                task_desc = user_msg[:500]

        header = f"## {task_name or '任务'}\n\n"
        warning = (
            "> **注意：当前为演示模式（Mock），未配置真实 LLM API Key。**\n"
            "> 以下内容为模拟输出，请在「设置」中配置 API Key 后重新运行以获取真实结果。\n\n"
        )

        if task_desc:
            body = (
                f"作为**{role}**，我已接收并理解了以下任务：\n\n"
                f"---\n{task_desc[:800]}\n---\n\n"
                f"### 当前状态\n"
                f"由于运行在演示模式，无法调用真实 LLM 进行处理。"
                f"请配置有效的 API Key（支持 OpenAI / Anthropic / DeepSeek 等）后重新执行此工作流。\n\n"
                f"### 如何配置\n"
                f"1. 点击右上角「设置」\n"
                f"2. 添加你的 LLM Provider 和 API Key\n"
                f"3. 确保 Agent 节点选择了对应的 Provider\n"
                f"4. 重新运行工作流"
            )
        else:
            body = (
                f"作为**{role}**，任务已接收但演示模式下无法实际执行。\n\n"
                f"请配置 API Key 后重试。"
            )

        return header + warning + body

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.0


def _create_provider(name: str, key: str, base_url: Optional[str] = None) -> BaseLLMProvider:
    """根据名称创建具体的 LLM provider 实例"""
    if name == "anthropic":
        return AnthropicProvider(api_key=key, base_url=base_url)
    if name == "openai":
        return OpenAIProvider(api_key=key, base_url=base_url)
    # DeepSeek、Moonshot、通义千问、智谱等 → OpenAI兼容接口
    return OpenAIProvider(api_key=key, base_url=base_url)


def get_llm_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    all_keys: Optional[Dict[str, str]] = None,
    all_base_urls: Optional[Dict[str, str]] = None,
) -> BaseLLMProvider:
    """根据提供商名称获取LLM实例。

    支持 fallback：如果主 provider 无 key，自动尝试其他已配置的 provider。
    """
    name = provider_name.lower()

    # Mock/演示模式
    if name in ("mock", "demo", "演示"):
        return MockProvider()

    # 优先使用用户传入的api_key，其次使用环境变量
    from app.core.config import settings
    key = api_key
    if not key:
        env_key_map = {"openai": settings.OPENAI_API_KEY, "anthropic": settings.ANTHROPIC_API_KEY}
        key = env_key_map.get(name)

    if key:
        return _create_provider(name, key, base_url)

    # 主 provider 无 key → 尝试 fallback
    if all_keys:
        for fallback_name, fallback_key in all_keys.items():
            if fallback_key and fallback_name.lower() != name:
                fb_url = (all_base_urls or {}).get(fallback_name)
                logger.info(f"Provider '{provider_name}' 无 key，fallback 到 '{fallback_name}'")
                return _create_provider(fallback_name.lower(), fallback_key, fb_url)

    logger.warning(f"Provider '{provider_name}' API key not configured, falling back to Mock provider")
    return MockProvider()


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """估算 LLM 调用成本（美元）"""
    pricing = {
        "gpt-4o": {"input": 2.5 / 1000, "output": 10 / 1000},
        "gpt-4o-mini": {"input": 0.15 / 1000, "output": 0.6 / 1000},
        "claude-sonnet-4-20250514": {"input": 3.0 / 1000, "output": 15.0 / 1000},
        "claude-haiku-4-5-20251001": {"input": 0.8 / 1000, "output": 4.0 / 1000},
    }
    rate = pricing.get(model, pricing.get("gpt-4o"))
    return (prompt_tokens * rate["input"] + completion_tokens * rate["output"])


# 模型降级链：高成本模型 → 低成本替代
MODEL_DEGRADATION_CHAIN = {
    "gpt-4o": "gpt-4o-mini",
    "gpt-4-turbo": "gpt-4o-mini",
    "claude-sonnet-4-20250514": "claude-haiku-4-5-20251001",
    "claude-opus-4-20250514": "claude-sonnet-4-20250514",
    "deepseek-chat": "deepseek-chat",  # 已经是最便宜的
}

# 模型成本等级（越高越贵）
MODEL_COST_TIER = {
    "gpt-4o-mini": 1,
    "claude-haiku-4-5-20251001": 1,
    "deepseek-chat": 1,
    "gpt-4o": 2,
    "claude-sonnet-4-20250514": 2,
    "gpt-4-turbo": 2,
    "claude-opus-4-20250514": 3,
}


async def update_provider_health(provider_name: str, success: bool):
    """更新 LLM Provider 的健康状态。

    Args:
        provider_name: 提供商名称
        success: 调用是否成功
    """
    try:
        from app.core.database import db_session_manager
        from app.models.llm_provider import LLMProvider
        from sqlalchemy import select

        async with db_session_manager.get_session() as db:
            result = await db.execute(
                select(LLMProvider).where(LLMProvider.provider == provider_name.lower())
            )
            provider = result.scalar_one_or_none()
            if not provider:
                return

            if success:
                provider.consecutive_failures = 0
                provider.is_healthy = True
            else:
                provider.consecutive_failures = (provider.consecutive_failures or 0) + 1
                # 连续失败 3 次标记为不健康
                if provider.consecutive_failures >= 3:
                    provider.is_healthy = False
                    logger.warning(f"Provider '{provider_name}' marked unhealthy after {provider.consecutive_failures} failures")

            await db.commit()
    except Exception as e:
        logger.debug(f"Failed to update provider health: {e}")


def select_degraded_model(model: str, budget_remaining: Optional[float], budget_total: Optional[float]) -> str:
    """根据预算剩余比例选择降级模型。

    Args:
        model: 当前模型名称
        budget_remaining: 剩余预算（美元）
        budget_total: 总预算（美元）

    Returns:
        模型名称（可能与输入相同，表示无需降级）
    """
    if not budget_total or not budget_remaining or budget_total <= 0:
        return model

    remaining_ratio = budget_remaining / budget_total

    # 剩余预算 > 30%：不降级
    if remaining_ratio > 0.3:
        return model

    # 剩余预算 10%-30%：降一级
    if remaining_ratio > 0.1:
        degraded = MODEL_DEGRADATION_CHAIN.get(model)
        if degraded:
            logger.info(f"预算紧张（剩余{remaining_ratio:.0%}），模型降级 {model} → {degraded}")
            return degraded
        return model

    # 剩余预算 < 10%：强制使用最低成本模型
    cheapest = min(MODEL_COST_TIER, key=MODEL_COST_TIER.get)
    if cheapest != model:
        logger.warning(f"预算严重不足（剩余{remaining_ratio:.0%}），强制降级 {model} → {cheapest}")
    return cheapest
