"""MCP Server HTTP 端点 Pydantic Schema"""

from typing import Any

from pydantic import BaseModel


class MCPToolInfo(BaseModel):
    """MCP 工具信息"""

    name: str
    description: str
    input_schema: dict[str, Any]


class MCPResourceInfo(BaseModel):
    """MCP 资源信息"""

    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None


class MCPPromptInfo(BaseModel):
    """MCP 提示词信息"""

    name: str
    description: str | None = None
    arguments: list[dict[str, Any]] | None = None


class MCPServerStatus(BaseModel):
    """MCP 服务器状态响应"""

    name: str
    version: str
    status: str
    tools_count: int
    resources_count: int
    prompts_count: int
