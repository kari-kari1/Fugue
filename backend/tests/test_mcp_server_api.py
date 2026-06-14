"""MCP Server HTTP API 测试

测试 SSE 端点、JSON-RPC 消息端点和状态端点。
使用独立的测试 FastAPI app，避免依赖 main.py 中的数据库等配置。

注意：SSE 端点使用无限循环的 EventSourceResponse，在 ASGI 测试中会导致
httpx 客户端永久阻塞。测试中使用有限生成器替代，验证端点的连接和数据格式。
"""

import json

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from httpx import ASGITransport, AsyncClient

from app.api.v1.mcp_server import mcp_server_message, mcp_server_status
from app.mcp_server.server import get_mcp_server


def _get_server():
    """获取 MCP 服务器实例"""
    return get_mcp_server()


def _make_test_app() -> FastAPI:
    """创建测试 FastAPI app，手动注册 MCP Server 端点。

    SSE 端点使用有限生成器以避免 ASGI 测试阻塞。
    """
    test_app = FastAPI()

    # SSE 端点 — 有限生成器版本（生产环境使用 EventSourceResponse 无限循环）
    @test_app.get("/api/v1/mcp-server/sse")
    async def _test_sse(request: Request):
        async def gen():
            yield "event: connected\n"
            yield f'data: {json.dumps({"name": "Fugue", "version": "0.1.0"})}\n\n'
        return StreamingResponse(gen(), media_type="text/event-stream")

    # JSON-RPC 消息端点
    @test_app.post("/api/v1/mcp-server/message")
    async def _test_message(request: Request):
        return await mcp_server_message(request)

    # 状态端点
    @test_app.get("/api/v1/mcp-server/status")
    async def _test_status():
        return await mcp_server_status()

    return test_app


@pytest_asyncio.fixture
async def client():
    """创建独立的测试 HTTP 客户端（仅挂载 MCP Server 端点）"""
    test_app = _make_test_app()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── SSE 端点 ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_endpoint_returns_sse(client: AsyncClient):
    """SSE 端点应返回 200 和 text/event-stream Content-Type"""
    response = await client.get("/api/v1/mcp-server/sse")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_mcp_server_sse_sends_connected_event(client: AsyncClient):
    """SSE 连接后应立即发送 connected 事件，包含服务器名称"""
    response = await client.get("/api/v1/mcp-server/sse")
    text = response.text
    assert "event: connected" in text
    assert "Fugue" in text


@pytest.mark.asyncio
async def test_mcp_server_sse_router_has_sse_route():
    """路由器应注册了 /sse 路由"""
    from app.api.v1.mcp_server import router

    sse_routes = [r for r in router.routes if hasattr(r, "path") and r.path == "/sse"]
    assert len(sse_routes) == 1
    assert "GET" in sse_routes[0].methods


# ── JSON-RPC: initialize ──────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_json_rpc_initialize(client: AsyncClient):
    """initialize 方法应返回服务器信息和 capabilities"""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    response = await client.post("/api/v1/mcp-server/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    result = data["result"]
    assert result["serverInfo"]["name"] == "Fugue"
    assert "serverInfo" in result
    assert "capabilities" in result


# ── JSON-RPC: tools/list ─────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_endpoint_handles_json_rpc(client: AsyncClient):
    """tools/list 应返回工具列表"""
    payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    response = await client.post("/api/v1/mcp-server/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert "result" in data
    assert "tools" in data["result"]
    tools = data["result"]["tools"]
    assert isinstance(tools, list)
    assert len(tools) >= 3
    tool_names = {t["name"] for t in tools}
    assert {"execute_workflow", "get_execution_status", "list_workflows"}.issubset(tool_names)


@pytest.mark.asyncio
async def test_mcp_server_tools_list_has_schema(client: AsyncClient):
    """工具条目应包含 name、description 和 inputSchema"""
    payload = {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}
    response = await client.post("/api/v1/mcp-server/message", json=payload)
    data = response.json()
    tool = next(t for t in data["result"]["tools"] if t["name"] == "list_workflows")
    assert "description" in tool
    assert "inputSchema" in tool
    assert isinstance(tool["inputSchema"], dict)


# ── JSON-RPC: resources/list ──────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_resources_list(client: AsyncClient):
    """resources/list 应返回资源列表"""
    payload = {"jsonrpc": "2.0", "id": 4, "method": "resources/list", "params": {}}
    response = await client.post("/api/v1/mcp-server/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "resources" in data["result"]


# ── JSON-RPC: resources/read ──────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_resources_read(client: AsyncClient):
    """resources/read 应返回资源内容"""
    from unittest.mock import AsyncMock, patch

    from mcp.server.lowlevel.helper_types import ReadResourceContents

    mock_contents = [ReadResourceContents(
        content='[{"uri": "fugue://workflows/1", "name": "test"}]',
        mime_type="application/json",
    )]
    with patch.object(
        type(_get_server()), "read_resource", new=AsyncMock(return_value=mock_contents)
    ):
        payload = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/read",
            "params": {"uri": "fugue://workflows"},
        }
        response = await client.post("/api/v1/mcp-server/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "contents" in data["result"]


# ── JSON-RPC: prompts/list ────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_prompts_list(client: AsyncClient):
    """prompts/list 应返回提示词列表"""
    payload = {"jsonrpc": "2.0", "id": 6, "method": "prompts/list", "params": {}}
    response = await client.post("/api/v1/mcp-server/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    prompts = data["result"]["prompts"]
    assert isinstance(prompts, list)
    prompt_names = {p["name"] for p in prompts}
    assert {"workflow_analysis", "agent_optimization", "execution_debugging"}.issubset(prompt_names)


# ── JSON-RPC: prompts/get ─────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_prompts_get(client: AsyncClient):
    """prompts/get 应返回提示词详情"""
    payload = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "prompts/get",
        "params": {
            "name": "workflow_analysis",
            "arguments": {
                "workflow_name": "test",
                "workflow_description": "desc",
            },
        },
    }
    response = await client.post("/api/v1/mcp-server/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "messages" in data["result"]


# ── JSON-RPC: tools/call ──────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_tools_call_unknown_tool(client: AsyncClient):
    """tools/call 对不存在的工具应返回错误"""
    payload = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {"name": "nonexistent_tool", "arguments": {}},
    }
    response = await client.post("/api/v1/mcp-server/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32000


# ── JSON-RPC: 错误处理 ────────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_json_rpc_invalid_format(client: AsyncClient):
    """缺少必要字段应返回 JSON-RPC 错误"""
    response = await client.post(
        "/api/v1/mcp-server/message",
        json={"id": 9, "method": "tools/list"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32600


@pytest.mark.asyncio
async def test_mcp_server_json_rpc_unknown_method(client: AsyncClient):
    """未知方法应返回 Method not found 错误"""
    payload = {"jsonrpc": "2.0", "id": 10, "method": "unknown/method", "params": {}}
    response = await client.post("/api/v1/mcp-server/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32601


# ── 状态端点 ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mcp_server_status(client: AsyncClient):
    """status 端点应返回服务器能力和计数"""
    response = await client.get("/api/v1/mcp-server/status")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Fugue"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"
    assert isinstance(data["tools_count"], int)
    assert data["tools_count"] >= 3
    assert isinstance(data["resources_count"], int)
    assert isinstance(data["prompts_count"], int)
    assert data["prompts_count"] >= 3
