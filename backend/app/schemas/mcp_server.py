"""MCP Server HTTP 端点 Pydantic Schema"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MCPToolInfo(BaseModel):
    """MCP 工具信息"""

    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPResourceInfo(BaseModel):
    """MCP 资源信息"""

    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class MCPPromptInfo(BaseModel):
    """MCP 提示词信息"""

    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None


class MCPServerStatus(BaseModel):
    """MCP 服务器状态响应"""

    name: str
    version: str
    status: str
    tools_count: int
    resources_count: int
    prompts_count: int
