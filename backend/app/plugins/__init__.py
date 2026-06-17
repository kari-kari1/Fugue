"""Fugue Plugin SDK

提供插件开发框架，让开发者能够轻松创建和分享自定义工具。

使用示例：
    from fugue.plugin import Plugin, Tool

    class MyCustomTool(Plugin):
        name = "my_custom_tool"
        description = "自定义工具描述"
        version = "1.0.0"
        author = "开发者名称"

        @Tool(
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"}
                },
                "required": ["query"]
            },
            permissions="safe"
        )
        async def search(self, query: str) -> str:
            # 工具实现
            return f"搜索结果: {query}"
"""

from .base import Plugin, PluginMeta, Tool
from .loader import PluginLoader
from .manager import PluginManager, get_plugin_manager

__version__ = "1.0.0"
__all__ = [
    "Plugin",
    "Tool",
    "PluginMeta",
    "PluginManager",
    "get_plugin_manager",
    "PluginLoader",
]
