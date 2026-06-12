"""MCP Server HTTP 端点 — Streamable HTTP transport

遵循 MCP 规范 2025-03-26：
- POST /mcp-server/message — JSON-RPC 2.0 请求，响应通过同一 HTTP 连接返回
- GET  /mcp-server/sse    — SSE 流（可选，用于服务端推送通知）
- GET  /mcp-server/status — 服务器能力查询
"""

import asyncio
import base64
import json
import logging
import uuid
from typing import Dict

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.mcp_server.server import get_mcp_server
from app.schemas.mcp_server import MCPServerStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp-server"])

SERVER_NAME = "Fugue"
SERVER_VERSION = "0.1.0"

# ── SSE 连接管理 ────────────────────────────────────────────────

# session_id → asyncio.Queue，用于向 SSE 客户端推送事件
_sse_queues: Dict[str, asyncio.Queue] = {}


async def _broadcast_to_sse(event_type: str, data: dict):
    """向所有 SSE 连接广播事件"""
    for q in list(_sse_queues.values()):
        try:
            q.put_nowait({"event": event_type, "data": json.dumps(data)})
        except asyncio.QueueFull:
            pass


# ── SSE 端点（服务端推送通道）────────────────────────────────


@router.get("/sse")
async def mcp_server_sse(request: Request):
    """SSE 长连接 — 用于服务端向客户端推送通知（如 toolsChanged）。

    MCP Streamable HTTP: 客户端通过 POST /message 发送请求，
    此 SSE 端点仅用于接收服务端主动通知。
    """
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _sse_queues[session_id] = queue

    async def event_generator():
        # 发送连接确认
        yield {
            "event": "connected",
            "data": json.dumps({
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
                "sessionId": session_id,
            }),
        }
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30)
                    yield msg
                except asyncio.TimeoutError:
                    # 30 秒无事件，发送心跳保活
                    yield {"event": "ping", "data": "{}"}
        finally:
            _sse_queues.pop(session_id, None)

    return EventSourceResponse(event_generator())


# ── JSON-RPC 2.0 核心 ──────────────────────────────────────────


def _jsonrpc_response(id, result):
    return {"jsonrpc": "2.0", "id": id, "result": result}


def _jsonrpc_error(id, code, message):
    return {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}


async def _handle_initialize(id, params):
    """处理 initialize 方法"""
    return _jsonrpc_response(id, {
        "protocolVersion": "2025-03-26",
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True},
            "prompts": {"listChanged": True},
            "elicitation": {},
            "sampling": {},
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    })


async def _handle_tools_list(id, params):
    server = get_mcp_server()
    tools = await server.list_tools()
    return _jsonrpc_response(id, {
        "tools": [t.model_dump() for t in tools],
    })


async def _handle_tools_call(id, params):
    name = params.get("name")
    arguments = params.get("arguments", {})
    if not name:
        return _jsonrpc_error(id, -32602, "Missing tool name")

    server = get_mcp_server()
    try:
        result = await server.call_tool(name, arguments)
        content = []
        for item in result:
            if hasattr(item, "model_dump"):
                content.append(item.model_dump())
            else:
                content.append({"type": "text", "text": str(item)})
        return _jsonrpc_response(id, {"content": content, "isError": False})
    except Exception as e:
        logger.warning(f"Tool call failed: {e}")
        return _jsonrpc_error(id, -32000, f"Tool execution error: {e}")


async def _handle_resources_list(id, params):
    server = get_mcp_server()
    resources = await server.list_resources()
    return _jsonrpc_response(id, {
        "resources": [r.model_dump() for r in resources],
    })


async def _handle_resources_read(id, params):
    uri = params.get("uri")
    if not uri:
        return _jsonrpc_error(id, -32602, "Missing resource URI")

    server = get_mcp_server()
    try:
        contents = await server.read_resource(uri)
        result_contents = []
        for c in contents:
            entry = {"uri": uri}
            if c.mime_type:
                entry["mimeType"] = c.mime_type
            if isinstance(c.content, bytes):
                entry["blob"] = base64.b64encode(c.content).decode()
            else:
                entry["text"] = str(c.content)
            result_contents.append(entry)
        return _jsonrpc_response(id, {"contents": result_contents})
    except Exception as e:
        logger.warning(f"Resource read failed: {e}")
        return _jsonrpc_error(id, -32000, f"Resource read error: {e}")


async def _handle_prompts_list(id, params):
    server = get_mcp_server()
    prompts = await server.list_prompts()
    return _jsonrpc_response(id, {
        "prompts": [p.model_dump() for p in prompts],
    })


async def _handle_prompts_get(id, params):
    name = params.get("name")
    arguments = params.get("arguments", {})
    if not name:
        return _jsonrpc_error(id, -32602, "Missing prompt name")

    server = get_mcp_server()
    try:
        result = await server.get_prompt(name, arguments or None)
        return _jsonrpc_response(id, result.model_dump())
    except Exception as e:
        logger.warning(f"Prompt get failed: {e}")
        return _jsonrpc_error(id, -32000, f"Prompt error: {e}")


async def _handle_elicitation_create(id, params):
    """处理 elicitation/create — MCP Server 向用户请求信息"""
    message = params.get("message", "")
    elicitation_type = params.get("type", "confirm")  # confirm / input / selection
    options = params.get("options", [])

    # 广播 elicitation 请求到所有 SSE 连接
    elicitation_data = {
        "id": str(uuid.uuid4()),
        "type": "elicitation",
        "elicitation_type": elicitation_type,
        "message": message,
        "options": options,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await _broadcast_to_sse(elicitation_data)

    return _jsonrpc_response(id, {
        "elicitation_id": elicitation_data["id"],
        "status": "pending",
    })


async def _handle_sampling_create_message(id, params):
    """处理 sampling/createMessage — Host 代 Server 调用 LLM 补全"""
    messages = params.get("messages", [])
    model = params.get("model", "gpt-4o")
    max_tokens = params.get("maxTokens", 1024)
    temperature = params.get("temperature", 0.7)

    # 使用 Fugue 的 LLM provider 执行补全
    try:
        from app.engine.llm_provider import get_llm_provider
        # 尝试使用默认 provider 或从环境变量获取
        provider_key = None
        base_url = None
        for provider_name in ["openai", "anthropic"]:
            key = os.environ.get(f"{provider_name.upper()}_API_KEY")
            if key:
                provider_key = key
                break
        if not provider_key:
            return _jsonrpc_error(id, -32603, "No LLM API key configured")

        llm = get_llm_provider(
            "openai" if provider_key else "anthropic",
            api_key=provider_key,
            base_url=base_url,
        )
        response = await llm.chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return _jsonrpc_response(id, {
            "role": "assistant",
            "content": response.content,
            "model": model,
        })
    except Exception as e:
        logger.error(f"sampling/createMessage failed: {e}")
        return _jsonrpc_error(id, -32603, f"LLM completion failed: {str(e)}")


# 方法路由表
_METHOD_HANDLERS = {
    "initialize": _handle_initialize,
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
    "resources/list": _handle_resources_list,
    "resources/read": _handle_resources_read,
    "prompts/list": _handle_prompts_list,
    "prompts/get": _handle_prompts_get,
    "elicitation/create": _handle_elicitation_create,
    "sampling/createMessage": _handle_sampling_create_message,
}


@router.post("/message")
async def mcp_server_message(request: Request):
    """JSON-RPC 2.0 消息端点。

    客户端通过 POST 发送 JSON-RPC 请求，响应通过同一 HTTP 连接返回。
    同时将结果广播到 SSE 连接（供需要推送通知的客户端使用）。
    """
    try:
        body = await request.json()
    except Exception:
        return _jsonrpc_error(None, -32700, "Parse error")

    # 验证 JSON-RPC 2.0 格式
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or not body.get("method"):
        return _jsonrpc_error(
            body.get("id") if isinstance(body, dict) else None,
            -32600, "Invalid Request",
        )

    req_id = body.get("id")
    method = body["method"]
    params = body.get("params", {})

    # 分发到对应方法处理器
    handler = _METHOD_HANDLERS.get(method)
    if handler is None:
        return _jsonrpc_error(req_id, -32601, f"Method not found: {method}")

    result = await handler(req_id, params)

    # 将响应也广播到 SSE（客户端可选择通过 SSE 接收）
    if _sse_queues:
        await _broadcast_to_sse("jsonrpc_response", result)

    return result


# ── 状态端点 ────────────────────────────────────────────────────


@router.get("/status", response_model=MCPServerStatus)
async def mcp_server_status():
    """返回 MCP 服务器运行状态和能力概览。"""
    server = get_mcp_server()
    tools = await server.list_tools()
    resources = await server.list_resources()
    prompts = await server.list_prompts()
    return {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "status": "running",
        "tools_count": len(tools),
        "resources_count": len(resources),
        "prompts_count": len(prompts),
    }
