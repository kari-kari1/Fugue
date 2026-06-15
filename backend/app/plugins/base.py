"""Plugin SDK 基础类和装饰器

提供Plugin基类、Tool装饰器和元数据定义。
"""

import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Type,
    get_type_hints,
)
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class ToolMeta:
    """工具元数据"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    permissions: str = "safe"  # 'safe' | 'caution' | 'dangerous'
    category: str = "general"
    version: str = "1.0.0"
    func: Callable = None

    def to_openai_schema(self) -> Dict[str, Any]:
        """转换为OpenAI function calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            }
        }

    def to_anthropic_schema(self) -> Dict[str, Any]:
        """转换为Anthropic tool_use格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class Tool:
    """工具装饰器

    用于标记Plugin类中的方法为可调用工具。

    Args:
        input_schema: 输入参数的JSON Schema
        output_schema: 输出格式的JSON Schema（可选）
        permissions: 权限等级 ('safe' | 'caution' | 'dangerous')
        category: 工具分类
        version: 工具版本

    Example:
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
            return f"结果: {query}"
    """

    def __init__(
        self,
        input_schema: Dict[str, Any],
        output_schema: Optional[Dict[str, Any]] = None,
        permissions: str = "safe",
        category: str = "general",
        version: str = "1.0.0",
        description: Optional[str] = None,
    ):
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.permissions = permissions
        self.category = category
        self.version = version
        self._description = description

    def __call__(self, func: Callable) -> Callable:
        """装饰器实现"""
        # 从函数文档字符串提取描述
        description = self._description or func.__doc__ or ""
        if description:
            # 清理文档字符串
            description = description.strip().split("\n")[0]

        # 保存工具元数据到函数属性
        func._tool_meta = ToolMeta(
            name=func.__name__,
            description=description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            permissions=self.permissions,
            category=self.category,
            version=self.version,
            func=func,
        )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Tool '{func.__name__}' execution failed: {e}")
                raise

        wrapper._tool_meta = func._tool_meta
        return wrapper


class PluginMeta(ABC):
    """插件元信息抽象基类"""
    name: ClassVar[str]
    description: ClassVar[str]
    version: ClassVar[str]
    author: ClassVar[str] = "Unknown"
    license: ClassVar[str] = "MIT"
    homepage: ClassVar[Optional[str]] = None
    tags: ClassVar[List[str]] = []

    # 依赖声明
    dependencies: ClassVar[List[str]] = []  # pip依赖列表
    python_requires: ClassVar[str] = ">=3.10"


class Plugin(PluginMeta):
    """插件基类

    所有自定义插件必须继承此类，并使用@Tool装饰器标记工具方法。

    Example:
        class MyPlugin(Plugin):
            name = "my_plugin"
            description = "我的自定义插件"
            version = "1.0.0"
            author = "开发者"

            @Tool(
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "输入文本"}
                    },
                    "required": ["text"]
                }
            )
            async def process(self, text: str) -> str:
                return text.upper()
    """

    def __init_subclass__(cls, **kwargs):
        """子类初始化时自动发现工具方法"""
        super().__init_subclass__(**kwargs)

        # 验证必要的类属性
        required_attrs = ["name", "description", "version"]
        for attr in required_attrs:
            if not hasattr(cls, attr):
                raise ValueError(f"Plugin class must define '{attr}' class variable")

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化插件

        Args:
            config: 插件配置（可选）
        """
        self.config = config or {}
        self._tools: Dict[str, ToolMeta] = {}
        self._discover_tools()

    def _discover_tools(self):
        """自动发现所有使用@Tool装饰器的方法"""
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue

            attr = getattr(self, attr_name)
            if hasattr(attr, "_tool_meta"):
                tool_meta: ToolMeta = attr._tool_meta
                # 绑定实例方法
                tool_meta.func = attr
                self._tools[attr_name] = tool_meta

    @property
    def tools(self) -> Dict[str, ToolMeta]:
        """获取所有工具"""
        return self._tools.copy()

    def get_tool(self, name: str) -> Optional[ToolMeta]:
        """获取指定工具"""
        return self._tools.get(name)

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """执行工具

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果字符串

        Raises:
            ValueError: 工具不存在
            Exception: 工具执行失败
        """
        tool_meta = self._tools.get(name)
        if not tool_meta:
            raise ValueError(f"Tool '{name}' not found in plugin '{self.name}'")

        try:
            # 执行工具函数
            result = await tool_meta.func(**arguments)

            # 确保返回字符串
            if result is None:
                return ""
            elif isinstance(result, dict):
                import json
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return str(result)

        except TypeError as e:
            # 参数类型错误
            raise ValueError(f"Invalid arguments for tool '{name}': {e}")
        except Exception as e:
            logger.error(f"Plugin '{self.name}' tool '{name}' execution failed: {e}")
            raise

    def get_openai_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的OpenAI格式Schema"""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def get_anthropic_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的Anthropic格式Schema"""
        return [tool.to_anthropic_schema() for tool in self._tools.values()]

    async def setup(self):
        """插件初始化钩子（可选覆盖）

        在插件加载后、执行工具前调用。
        用于初始化资源（如数据库连接、API客户端等）。
        """
        pass

    async def cleanup(self):
        """插件清理钩子（可选覆盖）

        在插件卸载前调用。
        用于清理资源（如关闭连接、释放内存等）。
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """插件健康检查（可选覆盖）

        Returns:
            包含 'healthy' (bool) 和 'message' (str) 的字典
        """
        return {
            "healthy": True,
            "message": "Plugin is healthy",
        }

    def to_dict(self) -> Dict[str, Any]:
        """导出插件元数据为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "license": self.license,
            "homepage": self.homepage,
            "tags": self.tags,
            "tools_count": len(self._tools),
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "permissions": tool.permissions,
                    "category": tool.category,
                }
                for tool in self._tools.values()
            ],
        }

    def __repr__(self) -> str:
        return f"<Plugin '{self.name}' v{self.version} with {len(self._tools)} tools>"
