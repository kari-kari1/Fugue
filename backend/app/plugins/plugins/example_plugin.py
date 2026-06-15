"""示例插件 — 演示如何使用Plugin SDK开发自定义工具"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List
from datetime import datetime

from app.plugins.base import Plugin, Tool

logger = logging.getLogger(__name__)


class ExamplePlugin(Plugin):
    """示例插件 — 包含多个实用工具的示例

    这个插件展示了如何使用Fugue Plugin SDK开发自定义工具。
    包含以下工具：
    - text_transform: 文本转换工具
    - json_formatter: JSON格式化工具
    - datetime_util: 日期时间工具
    - calculator: 计算器工具
    """

    name = "example_plugin"
    description = "示例插件，包含多个实用工具"
    version = "1.0.0"
    author = "Fugue Team"
    license = "MIT"
    tags = ["example", "utility", "demo"]

    dependencies = []
    python_requires = ">=3.10"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要转换的文本"
                },
                "operation": {
                    "type": "string",
                    "enum": ["upper", "lower", "title", "reverse", "capitalize"],
                    "description": "转换操作",
                    "default": "upper"
                }
            },
            "required": ["text", "operation"]
        },
        permissions="safe",
        category="text",
        version="1.0.0"
    )
    async def text_transform(self, text: str, operation: str) -> str:
        """文本转换工具

        支持多种文本转换操作：大写、小写、首字母大写、反转等。
        """
        operations = {
            "upper": text.upper(),
            "lower": text.lower(),
            "title": text.title(),
            "reverse": text[::-1],
            "capitalize": text.capitalize(),
        }

        if operation not in operations:
            return f"❌ 不支持的转换操作: {operation}"

        result = operations[operation]
        return f"✅ 转换结果 ({operation}):\n{result}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "json_str": {
                    "type": "string",
                    "description": "JSON字符串"
                },
                "indent": {
                    "type": "integer",
                    "description": "缩进空格数",
                    "default": 2
                }
            },
            "required": ["json_str"]
        },
        permissions="safe",
        category="data",
        version="1.0.0"
    )
    async def json_formatter(self, json_str: str, indent: int = 2) -> str:
        """JSON格式化工具

        格式化和美化JSON字符串。
        """
        try:
            data = json.loads(json_str)
            formatted = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)
            return f"✅ 格式化的JSON:\n```json\n{formatted}\n```"
        except json.JSONDecodeError as e:
            return f"❌ JSON解析失败: {str(e)}"
        except Exception as e:
            return f"❌ 格式化失败: {str(e)}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["now", "today", "timestamp", "format"],
                    "description": "日期时间操作"
                },
                "format": {
                    "type": "string",
                    "description": "日期格式（用于format操作）",
                    "default": "%Y-%m-%d %H:%M:%S"
                }
            },
            "required": ["operation"]
        },
        permissions="safe",
        category="utility",
        version="1.0.0"
    )
    async def datetime_util(self, operation: str, format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """日期时间工具

        提供日期时间相关的实用功能。
        """
        now = datetime.now()

        if operation == "now":
            return f"🕐 当前时间: {now.strftime(format)}"
        elif operation == "today":
            return f"📅 今天日期: {now.strftime('%Y-%m-%d')}"
        elif operation == "timestamp":
            return f"⏱️ Unix时间戳: {int(now.timestamp())}"
        elif operation == "format":
            return f"📆 格式化时间: {now.strftime(format)}"
        else:
            return f"❌ 不支持的操作: {operation}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式（支持 +, -, *, /, **, sqrt, sin, cos, tan, log 等）"
                }
            },
            "required": ["expression"]
        },
        permissions="safe",
        category="math",
        version="1.0.0"
    )
    async def calculator(self, expression: str) -> str:
        """计算器工具

        安全地计算数学表达式。
        """
        import math

        # 安全的数学函数
        safe_functions = {
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "abs": abs,
            "round": round,
            "pow": pow,
            "pi": math.pi,
            "e": math.e,
        }

        try:
            # 安全检查：只允许数字、运算符和安全函数
            safe_pattern = r'^[\d\s\+\-\*/\.\(\)\,*]+$'
            has_functions = any(func in expression for func in safe_functions.keys())

            if not re.match(safe_pattern, expression) and not has_functions:
                return "❌ 表达式包含不允许的字符"

            # 计算表达式
            result = eval(expression, {"__builtins__": {}}, safe_functions)
            return f"🔢 计算结果:\n{expression} = {result}"

        except ZeroDivisionError:
            return "❌ 错误: 除以零"
        except Exception as e:
            return f"❌ 计算失败: {str(e)}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要分析的文本"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["word_count", "char_count", "sentence_count", "reading_time"],
                    "description": "分析类型"
                }
            },
            "required": ["text", "analysis_type"]
        },
        permissions="safe",
        category="text",
        version="1.0.0"
    )
    async def text_analyzer(self, text: str, analysis_type: str) -> str:
        """文本分析工具

        提供文本统计和分析功能。
        """
        if analysis_type == "word_count":
            words = len(text.split())
            return f"📊 词数统计: {words} 个单词"

        elif analysis_type == "char_count":
            chars = len(text)
            chars_no_spaces = len(text.replace(" ", "").replace("\n", ""))
            return f"📊 字符统计:\n- 总字符数: {chars}\n- 不含空格: {chars_no_spaces}"

        elif analysis_type == "sentence_count":
            sentences = len(re.split(r'[.!?]+', text.strip()))
            return f"📊 句子数量: {sentences} 句"

        elif analysis_type == "reading_time":
            words = len(text.split())
            # 平均阅读速度：200词/分钟
            minutes = words / 200
            if minutes < 1:
                return f"⏱️ 预计阅读时间: {int(minutes * 60)} 秒"
            else:
                return f"⏱️ 预计阅读时间: {minutes:.1f} 分钟"

        else:
            return f"❌ 不支持的分析类型: {analysis_type}"

    async def setup(self):
        """插件初始化"""
        logger.info(f"ExamplePlugin v{self.version} initialized")

    async def cleanup(self):
        """插件清理"""
        logger.info(f"ExamplePlugin v{self.version} cleanup")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "healthy": True,
            "message": f"ExamplePlugin v{self.version} is running normally",
            "tools_count": len(self.tools),
        }


# 导出插件类
__all__ = ["ExamplePlugin"]
