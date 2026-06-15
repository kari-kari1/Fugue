"""MCP (Model Context Protocol) 工具适配器

支持连接 MCP Server，自动发现和调用其暴露的工具。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)


class MCPToolAdapter:
    """MCP 工具适配器 — 管理与 MCP Server 的连接和工具调用"""

    def __init__(self):
        self._connections: Dict[str, Any] = {}  # server_id -> session
        self._tools_cache: Dict[str, List[Dict[str, Any]]] = {}  # server_id -> tools
        self._exit_stack = AsyncExitStack()

    async def connect_server(
        self,
        server_id: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
    ) -> List[Dict[str, Any]]:
        """连接到 MCP Server 并发现其工具。

        Args:
            server_id: 服务器唯一标识
            command: 启动命令（如 "npx", "python"）
            args: 命令参数
            env: 环境变量

        Returns:
            该服务器暴露的工具列表
        """
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=command,
                args=args or [],
                env=env,
            )

            # 启动 MCP Server 进程并建立连接
            read_stream, write_stream = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            # 初始化会话
            await session.initialize()

            # 发现工具
            tools_result = await session.list_tools()
            tools = []
            for tool in tools_result.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                })

            self._connections[server_id] = session
            self._tools_cache[server_id] = tools

            logger.info(f"MCP Server '{server_id}' connected, discovered {len(tools)} tools")
            return tools

        except Exception as e:
            logger.error(f"Failed to connect MCP Server '{server_id}': {e}")
            raise

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """调用 MCP Server 上的工具。

        Args:
            server_id: 服务器标识
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        session = self._connections.get(server_id)
        if not session:
            return {"success": False, "error": f"MCP Server '{server_id}' not connected"}

        try:
            result = await session.call_tool(tool_name, arguments)

            # 提取文本内容
            output_parts = []
            for content in result.content:
                if hasattr(content, 'text'):
                    output_parts.append(content.text)
                elif hasattr(content, 'type'):
                    output_parts.append(f"[{content.type}]")

            return {
                "success": not result.isError if hasattr(result, 'isError') else True,
                "output": "\n".join(output_parts),
            }

        except Exception as e:
            logger.error(f"MCP tool call failed: {server_id}/{tool_name}: {e}")
            return {"success": False, "error": str(e)}

    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有已连接服务器的工具列表"""
        return dict(self._tools_cache)

    def get_tool_schemas(self, server_id: str = None) -> List[Dict[str, Any]]:
        """获取工具的 OpenAI function calling 格式 schema。

        Args:
            server_id: 指定服务器，None 表示全部

        Returns:
            OpenAI 格式的 tools 列表
        """
        schemas = []
        servers = {server_id: self._tools_cache[server_id]} if server_id else self._tools_cache

        for sid, tools in servers.items():
            for tool in tools:
                schemas.append({
                    "type": "function",
                    "function": {
                        "name": f"mcp_{sid}_{tool['name']}",
                        "description": f"[MCP:{sid}] {tool['description']}",
                        "parameters": tool.get("input_schema", {}),
                    }
                })
        return schemas

    def is_mcp_tool(self, tool_name: str) -> bool:
        """判断工具名是否为 MCP 工具（格式: mcp_{server_id}_{tool_name}）"""
        return tool_name.startswith("mcp_")

    def parse_mcp_tool_name(self, tool_name: str) -> tuple:
        """解析 MCP 工具名，返回 (server_id, original_tool_name)"""
        # mcp_{server_id}_{tool_name} → 需要处理 server_id 中可能的下划线
        parts = tool_name[4:].split("_", 1)  # 去掉 "mcp_" 前缀后按第一个 "_" 分割
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], parts[0]

    async def disconnect_all(self):
        """断开所有 MCP Server 连接"""
        try:
            await self._exit_stack.aclose()
        except Exception as e:
            logger.warning(f"Error closing MCP connections: {e}")
        self._connections.clear()
        self._tools_cache.clear()


# 全局单例
_mcp_adapter: Optional[MCPToolAdapter] = None


def get_mcp_adapter() -> MCPToolAdapter:
    """获取全局 MCP 适配器实例"""
    global _mcp_adapter
    if _mcp_adapter is None:
        _mcp_adapter = MCPToolAdapter()
    return _mcp_adapter
