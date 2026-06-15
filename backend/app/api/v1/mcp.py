"""MCP Server 管理 API"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.engine.mcp_adapter import get_mcp_adapter
from app.services.mcp_marketplace import get_mcp_marketplace

logger = logging.getLogger(__name__)
router = APIRouter()


class MCPServerConnect(BaseModel):
    """连接 MCP Server 请求"""
    server_id: str = Field(..., min_length=1, max_length=50)
    command: str = Field(..., min_length=1)
    args: List[str] = Field(default_factory=list)
    env: Optional[dict] = None


class MCPCallTool(BaseModel):
    """调用 MCP 工具请求"""
    server_id: str
    tool_name: str
    arguments: dict = Field(default_factory=dict)


@router.post("/connect")
async def connect_mcp_server(data: MCPServerConnect, current_user: CurrentUser):
    """连接到 MCP Server 并发现工具（需认证）"""
    adapter = get_mcp_adapter()
    try:
        tools = await adapter.connect_server(
            server_id=data.server_id,
            command=data.command,
            args=data.args,
            env=data.env,
        )
        return {
            "server_id": data.server_id,
            "tools_count": len(tools),
            "tools": tools,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接 MCP Server 失败: {str(e)}")


@router.get("/tools")
async def list_mcp_tools(current_user: CurrentUser, server_id: Optional[str] = None):
    """列出已连接 MCP Server 的工具（需认证）"""
    adapter = get_mcp_adapter()
    all_tools = adapter.get_all_tools()

    if server_id:
        tools = all_tools.get(server_id, [])
        if not tools:
            raise HTTPException(status_code=404, detail=f"MCP Server '{server_id}' 未连接或无工具")
        return {"server_id": server_id, "tools": tools}

    return {
        "servers": {
            sid: {"tools_count": len(tools), "tools": tools}
            for sid, tools in all_tools.items()
        }
    }


@router.post("/call")
async def call_mcp_tool(data: MCPCallTool, current_user: CurrentUser):
    """调用 MCP Server 上的工具（需认证）"""
    adapter = get_mcp_adapter()
    result = await adapter.call_tool(
        server_id=data.server_id,
        tool_name=data.tool_name,
        arguments=data.arguments,
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "工具调用失败"))
    return result


@router.get("/schemas")
async def get_mcp_tool_schemas(current_user: CurrentUser, server_id: Optional[str] = None):
    """获取 MCP 工具的 OpenAI function calling 格式 schema（需认证）"""
    adapter = get_mcp_adapter()
    schemas = adapter.get_tool_schemas(server_id)
    return {"schemas": schemas, "count": len(schemas)}


# ─── MCP工具市场 ───


@router.get("/marketplace/presets")
async def list_mcp_presets(
    category: Optional[str] = Query(None, description="按分类过滤"),
    search: Optional[str] = Query(None, description="关键词搜索"),
):
    """列出预置的MCP Server配置"""
    marketplace = get_mcp_marketplace()
    presets = marketplace.list_presets(category=category, search=search)

    return {
        "presets": presets,
        "total": len(presets),
    }


@router.get("/marketplace/categories")
async def list_mcp_categories():
    """获取MCP Server分类列表"""
    marketplace = get_mcp_marketplace()
    categories = marketplace.get_categories()

    return {
        "categories": categories,
        "total": len(categories),
    }


@router.get("/marketplace/presets/{preset_id}")
async def get_mcp_preset(preset_id: str):
    """获取预置配置详情"""
    marketplace = get_mcp_marketplace()
    preset = marketplace.get_preset(preset_id)

    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

    return preset


@router.get("/marketplace/presets/{preset_id}/install")
async def get_install_command(preset_id: str):
    """获取安装命令"""
    marketplace = get_mcp_marketplace()
    install_info = marketplace.generate_install_command(preset_id)

    if not install_info:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

    return install_info
