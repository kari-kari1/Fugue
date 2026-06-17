"""插件管理器 — 管理插件的生命周期和工具注册"""

import logging
from typing import Any

from .base import Plugin, ToolMeta

logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器

    负责：
    - 插件的注册和卸载
    - 工具的发现和索引
    - 插件的生命周期管理
    - 插件健康检查
    """

    def __init__(self):
        self._plugins: dict[str, Plugin] = {}  # plugin_name -> Plugin instance
        self._tools_index: dict[str, ToolMeta] = {}  # tool_name -> ToolMeta
        self._plugin_classes: dict[str, type[Plugin]] = {}  # plugin_name -> Plugin class

    @property
    def plugins(self) -> dict[str, Plugin]:
        """获取所有已加载的插件"""
        return self._plugins.copy()

    @property
    def tools(self) -> dict[str, ToolMeta]:
        """获取所有已注册的工具"""
        return self._tools_index.copy()

    def register_plugin_class(self, plugin_class: type[Plugin]):
        """注册插件类（不立即实例化）

        Args:
            plugin_class: Plugin子类

        Raises:
            ValueError: 如果插件名称已存在
        """
        if not issubclass(plugin_class, Plugin):
            raise TypeError(f"{plugin_class} is not a Plugin subclass")

        plugin_name = plugin_class.name
        if plugin_name in self._plugin_classes:
            raise ValueError(f"Plugin '{plugin_name}' already registered")

        self._plugin_classes[plugin_name] = plugin_class
        logger.info(f"Registered plugin class: {plugin_name}")

    async def load_plugin(
        self,
        plugin_name: str,
        config: dict[str, Any] | None = None,
    ) -> Plugin:
        """加载并初始化插件

        Args:
            plugin_name: 插件名称
            config: 插件配置

        Returns:
            初始化后的Plugin实例

        Raises:
            ValueError: 插件不存在或加载失败
        """
        if plugin_name in self._plugins:
            logger.warning(f"Plugin '{plugin_name}' already loaded, returning existing instance")
            return self._plugins[plugin_name]

        plugin_class = self._plugin_classes.get(plugin_name)
        if not plugin_class:
            raise ValueError(f"Plugin '{plugin_name}' not registered")

        try:
            # 实例化插件
            plugin_instance = plugin_class(config)

            # 调用setup钩子
            await plugin_instance.setup()

            # 注册工具
            for tool_name, tool_meta in plugin_instance.tools.items():
                if tool_name in self._tools_index:
                    # 安全获取插件名称
                    existing_func = self._tools_index[tool_name].func
                    existing_plugin = getattr(existing_func, '__self__', None)
                    existing_name = existing_plugin.name if existing_plugin else 'unknown'
                    logger.warning(
                        f"Tool '{tool_name}' already registered (from plugin "
                        f"'{existing_name}'), "
                        f"overwriting with plugin '{plugin_name}'"
                    )
                self._tools_index[tool_name] = tool_meta

            # 保存实例
            self._plugins[plugin_name] = plugin_instance
            logger.info(
                f"Loaded plugin '{plugin_name}' v{plugin_instance.version} "
                f"with {len(plugin_instance.tools)} tools"
            )

            return plugin_instance

        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            raise ValueError(f"Failed to load plugin '{plugin_name}': {e}")

    async def unload_plugin(self, plugin_name: str):
        """卸载插件

        Args:
            plugin_name: 插件名称

        Raises:
            ValueError: 插件未加载
        """
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not loaded")

        try:
            # 移除工具索引
            for tool_name in plugin.tools.keys():
                if tool_name in self._tools_index:
                    del self._tools_index[tool_name]

            # 调用cleanup钩子
            await plugin.cleanup()

            # 移除实例
            del self._plugins[plugin_name]
            logger.info(f"Unloaded plugin '{plugin_name}'")

        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_name}': {e}")
            raise

    async def load_all_plugins(self):
        """加载所有已注册的插件类"""
        for plugin_name in list(self._plugin_classes.keys()):
            try:
                await self.load_plugin(plugin_name)
            except Exception as e:
                logger.error(f"Failed to auto-load plugin '{plugin_name}': {e}")

    async def unload_all_plugins(self):
        """卸载所有已加载的插件"""
        for plugin_name in list(self._plugins.keys()):
            try:
                await self.unload_plugin(plugin_name)
            except Exception as e:
                logger.error(f"Failed to unload plugin '{plugin_name}': {e}")

    def get_plugin(self, plugin_name: str) -> Plugin | None:
        """获取已加载的插件实例"""
        return self._plugins.get(plugin_name)

    def get_tool(self, tool_name: str) -> ToolMeta | None:
        """获取已注册的工具"""
        return self._tools_index.get(tool_name)

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str:
        """执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果

        Raises:
            ValueError: 工具不存在
        """
        tool_meta = self._tools_index.get(tool_name)
        if not tool_meta:
            raise ValueError(f"Tool '{tool_name}' not found")

        # 找到对应的插件实例
        plugin = None
        for p in self._plugins.values():
            if tool_name in p.tools:
                plugin = p
                break

        if not plugin:
            raise ValueError(f"Plugin for tool '{tool_name}' not loaded")

        return await plugin.execute_tool(tool_name, arguments)

    async def health_check_all(self) -> dict[str, dict[str, Any]]:
        """对所有插件执行健康检查"""
        results = {}
        for plugin_name, plugin in self._plugins.items():
            try:
                health = await plugin.health_check()
                results[plugin_name] = health
            except Exception as e:
                results[plugin_name] = {
                    "healthy": False,
                    "message": f"Health check failed: {e}",
                }
        return results

    def list_plugins(self) -> list[dict[str, Any]]:
        """列出所有已加载的插件"""
        return [plugin.to_dict() for plugin in self._plugins.values()]

    def list_tools(self) -> list[dict[str, Any]]:
        """列出所有已注册的工具"""
        tools = []
        for tool_name, tool_meta in self._tools_index.items():
            # 找到所属插件
            plugin_name = None
            for p in self._plugins.values():
                if tool_name in p.tools:
                    plugin_name = p.name
                    break

            tools.append({
                "name": tool_meta.name,
                "description": tool_meta.description,
                "permissions": tool_meta.permissions,
                "category": tool_meta.category,
                "plugin": plugin_name,
            })
        return tools

    def get_tools_by_category(self, category: str) -> list[ToolMeta]:
        """按分类获取工具"""
        return [
            tool for tool in self._tools_index.values()
            if tool.category == category
        ]

    def get_tools_by_permission(self, permission: str) -> list[ToolMeta]:
        """按权限等级获取工具"""
        return [
            tool for tool in self._tools_index.values()
            if tool.permissions == permission
        ]

    def get_openai_tools_schema(
        self,
        categories: list[str] | None = None,
        permissions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """获取工具的OpenAI格式Schema（支持过滤）"""
        tools = self._tools_index.values()

        if categories:
            tools = [t for t in tools if t.category in categories]
        if permissions:
            tools = [t for t in tools if t.permissions in permissions]

        return [tool.to_openai_schema() for tool in tools]

    def get_anthropic_tools_schema(
        self,
        categories: list[str] | None = None,
        permissions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """获取工具的Anthropic格式Schema（支持过滤）"""
        tools = self._tools_index.values()

        if categories:
            tools = [t for t in tools if t.category in categories]
        if permissions:
            tools = [t for t in tools if t.permissions in permissions]

        return [tool.to_anthropic_schema() for tool in tools]


# 全局插件管理器实例
_plugin_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


async def initialize_plugins():
    """初始化插件系统"""
    manager = get_plugin_manager()
    await manager.load_all_plugins()
    logger.info(f"Plugin system initialized with {len(manager.plugins)} plugins")


async def shutdown_plugins():
    """关闭插件系统"""
    manager = get_plugin_manager()
    await manager.unload_all_plugins()
    logger.info("Plugin system shutdown")
