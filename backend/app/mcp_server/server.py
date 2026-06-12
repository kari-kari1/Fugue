"""MCP Server 工厂 — 创建和管理 FastMCP 实例"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

_server_instance: Optional[FastMCP] = None


def create_mcp_server() -> FastMCP:
    """创建并配置 FastMCP 服务器实例。

    注册所有 tools、resources、prompts 后返回实例。
    """
    server = FastMCP(
        name="Fugue",
        instructions="Multi-agent workflow platform - execute workflows, query status, and browse templates.",
    )

    from .tools import register_tools
    from .resources import register_resources
    from .prompts import register_prompts

    register_tools(server)
    register_resources(server)
    register_prompts(server)

    return server


def get_mcp_server() -> FastMCP:
    """获取全局单例 MCP 服务器实例。"""
    global _server_instance
    if _server_instance is None:
        _server_instance = create_mcp_server()
    return _server_instance


def _reset_server() -> None:
    """重置全局单例（仅供测试使用）。"""
    global _server_instance
    _server_instance = None
