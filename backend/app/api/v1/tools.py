"""工具状态API — 返回内置工具的实现状态和能力信息"""

from typing import Dict, Any, List, Set
from fastapi import APIRouter

router = APIRouter()

# ─── 工具注册表 ───

_TOOL_STATUS: Dict[str, Dict[str, Any]] = {
    "file_read": {
        "name": "读取文件",
        "implemented": True,
        "description": "读取指定路径的文件内容，支持文本和常见格式",
        "required_capabilities": ["function_calling"],
    },
    "file_write": {
        "name": "写入文件",
        "implemented": True,
        "description": "将内容写入指定路径的文件",
        "required_capabilities": ["function_calling"],
    },
    "code_execute": {
        "name": "执行代码",
        "implemented": True,
        "description": "在沙箱环境中执行 Python/JavaScript/Bash 代码",
        "required_capabilities": ["function_calling"],
    },
    "api_call": {
        "name": "API调用",
        "implemented": True,
        "description": "向指定 URL 发送 HTTP 请求",
        "required_capabilities": ["function_calling"],
    },
    "web_search": {
        "name": "网络搜索",
        "implemented": True,
        "description": "通过 DuckDuckGo 搜索互联网获取实时信息",
        "required_capabilities": ["function_calling"],
    },
    "database_query": {
        "name": "数据库查询",
        "implemented": True,
        "description": "连接数据库并执行 SELECT 查询，返回格式化结果",
        "required_capabilities": ["function_calling"],
    },
    "image_generation": {
        "name": "图像生成",
        "implemented": True,
        "description": "调用 DALL-E API 根据文字描述生成图片（需配置 OPENAI_API_KEY）",
        "required_capabilities": ["function_calling", "image_generation"],
    },
    "text_analysis": {
        "name": "文本分析",
        "implemented": True,
        "description": "通过 LLM 进行摘要、情感分析、关键词提取、分类和翻译",
        "required_capabilities": ["function_calling"],
    },
}

# ─── 模型能力注册表 ───

# 不支持 function calling 的模型
_NO_TOOL_MODELS = {"deepseek-r1", "qwen-vl", "qwen-audio", "cogview", "cogvideo"}

# 支持 function calling 的已知提供商
_TOOL_CAPABLE_PROVIDERS = {
    "openai", "anthropic", "deepseek", "moonshot", "qwen", "zhipu",
}

# 模型级别的具体能力 (provider/model -> capabilities)
_MODEL_CAPABILITIES: Dict[str, List[str]] = {
    "openai/gpt-4o":          ["function_calling", "image_generation"],
    "openai/gpt-4o-mini":     ["function_calling", "image_generation"],
    "openai/gpt-4-turbo":     ["function_calling", "image_generation"],
    "openai/gpt-3.5-turbo":   ["function_calling"],
    "openai/o1":              ["function_calling"],
    "openai/o3":              ["function_calling"],
    "anthropic/claude-sonnet-4-20250514":   ["function_calling"],
    "anthropic/claude-3-5-sonnet-20241022": ["function_calling"],
    "anthropic/claude-3-5-haiku-20241022":  ["function_calling"],
    "anthropic/claude-3-opus-20240229":     ["function_calling"],
    "deepseek/deepseek-chat":   ["function_calling"],
    "deepseek/deepseek-coder":  ["function_calling"],
    "moonshot/moonshot-v1-8k":  ["function_calling"],
    "moonshot/moonshot-v1-32k": ["function_calling"],
    "moonshot/moonshot-v1-128k":["function_calling"],
    "qwen/qwen-turbo":  ["function_calling"],
    "qwen/qwen-plus":   ["function_calling"],
    "qwen/qwen-max":    ["function_calling"],
    "zhipu/glm-4-flash":  ["function_calling"],
    "zhipu/glm-4":        ["function_calling"],
    "mock/mock-model":    ["function_calling"],
}


def _model_supports_tools(provider: str, model: str) -> bool:
    """检查模型是否支持 function calling"""
    if not provider or not model:
        return False
    provider = provider.lower().strip()
    model = model.lower().strip()

    for pattern in _NO_TOOL_MODELS:
        if pattern in model:
            return False

    if provider in _TOOL_CAPABLE_PROVIDERS:
        return True

    tool_capable_patterns = ["gpt-4", "gpt-3.5", "claude", "qwen-", "glm-4", "gemini"]
    for pattern in tool_capable_patterns:
        if pattern in model:
            return True

    return True


def _get_model_capabilities(provider: str, model: str) -> List[str]:
    """获取模型的具体能力列表"""
    if not provider or not model:
        return []
    key = f"{provider.lower().strip()}/{model.lower().strip()}"
    return _MODEL_CAPABILITIES.get(key, ["function_calling"])


@router.get("/status")
async def get_tools_status() -> Dict[str, Any]:
    """获取所有内置工具的状态信息"""
    tools = []
    for tool_id, info in _TOOL_STATUS.items():
        tools.append({
            "id": tool_id,
            "name": info["name"],
            "implemented": info["implemented"],
            "description": info["description"],
            "required_capabilities": info["required_capabilities"],
        })

    return {
        "tools": tools,
        "total": len(tools),
        "implemented_count": sum(1 for t in tools if t["implemented"]),
        "stub_count": sum(1 for t in tools if not t["implemented"]),
    }


@router.get("/availability/{provider}/{model}")
async def get_tool_availability(provider: str, model: str) -> Dict[str, Any]:
    """检测指定模型对各工具的可用性"""
    model_ok = _model_supports_tools(provider, model)
    model_caps = set(_get_model_capabilities(provider, model))

    tools = []
    for tool_id, info in _TOOL_STATUS.items():
        # 1) 工具是否已实现
        if not info["implemented"]:
            tools.append({
                "id": tool_id,
                "name": info["name"],
                "available": False,
                "reason": "not_implemented",
                "reason_text": "该工具尚未接入真实 API，暂时不可用",
            })
            continue

        # 2) 模型是否支持 function calling
        if not model_ok:
            tools.append({
                "id": tool_id,
                "name": info["name"],
                "available": False,
                "reason": "model_no_tools",
                "reason_text": f"模型 {provider}/{model} 不支持 Function Calling",
            })
            continue

        # 3) 模型是否具备该工具所需的具体能力
        required = set(info["required_capabilities"])
        missing = required - model_caps
        if missing:
            tools.append({
                "id": tool_id,
                "name": info["name"],
                "available": False,
                "reason": "missing_capability",
                "reason_text": f"模型缺少能力: {', '.join(sorted(missing))}",
            })
            continue

        tools.append({
            "id": tool_id,
            "name": info["name"],
            "available": True,
            "reason": None,
            "reason_text": None,
        })

    return {
        "provider": provider,
        "model": model,
        "model_supports_tools": model_ok,
        "model_capabilities": sorted(model_caps),
        "tools": tools,
        "available_count": sum(1 for t in tools if t["available"]),
    }
