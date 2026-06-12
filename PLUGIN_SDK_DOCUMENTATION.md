# Fugue Plugin SDK 文档

## 概述

Fugue Plugin SDK 允许开发者创建自定义工具和插件，扩展Fugue的功能。插件可以：
- 定义新的工具供Agent使用
- 集成外部API和服务
- 封装复杂的业务逻辑
- 与其他开发者分享

## 快速开始

### 1. 创建插件

创建一个Python文件，继承`Plugin`基类：

```python
from app.plugins import Plugin, Tool

class MyPlugin(Plugin):
    name = "my_plugin"
    description = "我的自定义插件"
    version = "1.0.0"
    author = "Your Name"
    tags = ["utility", "custom"]

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询"
                }
            },
            "required": ["query"]
        },
        permissions="safe",
        category="search"
    )
    async def search(self, query: str) -> str:
        """搜索工具"""
        # 实现你的搜索逻辑
        return f"搜索结果: {query}"
```

### 2. 部署插件

将插件文件放到 `backend/app/plugins/plugins/` 目录：

```
backend/
  app/
    plugins/
      plugins/
        my_plugin.py    <- 你的插件
```

### 3. 使用插件

插件系统会自动加载插件。启动后端服务即可使用：

```bash
cd backend
uvicorn app.main:app --reload
```

## Plugin 基类

### 必要属性

```python
class MyPlugin(Plugin):
    name = "my_plugin"           # 插件名称（唯一标识）
    description = "描述"          # 插件描述
    version = "1.0.0"            # 版本号（语义化版本）
```

### 可选属性

```python
    author = "作者"               # 作者名称
    license = "MIT"              # 许可证
    homepage = "https://..."     # 项目主页
    tags = ["tag1", "tag2"]      # 标签
    dependencies = []            # Python依赖列表
    python_requires = ">=3.10"   # Python版本要求
```

### 生命周期钩子

```python
    async def setup(self):
        """插件初始化（加载时调用）"""
        # 初始化资源，如数据库连接、API客户端等
        self.client = httpx.AsyncClient()

    async def cleanup(self):
        """插件清理（卸载时调用）"""
        # 清理资源
        await self.client.aclose()

    async def health_check(self):
        """健康检查"""
        return {
            "healthy": True,
            "message": "Plugin is running"
        }
```

## Tool 装饰器

`@Tool` 装饰器用于标记方法为可调用工具：

```python
@Tool(
    input_schema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "参数描述"
            },
            "param2": {
                "type": "integer",
                "description": "数字参数",
                "default": 10
            }
        },
        "required": ["param1"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        }
    },
    permissions="safe",       # safe | caution | dangerous
    category="general",       # 分类
    version="1.0.0"           # 工具版本
)
async def my_tool(self, param1: str, param2: int = 10) -> str:
    """工具描述（会自动提取为工具说明）"""
    return f"Result: {param1}"
```

### 权限等级

- **safe**: 只读操作，无副作用（推荐）
  - 示例：搜索、读取数据、文本处理
- **caution**: 有副作用但可控
  - 示例：写文件、发送消息、修改数据库
- **dangerous**: 危险操作，需要用户确认
  - 示例：执行代码、删除数据、系统命令

### 分类（category）

常用分类：
- `search`: 搜索相关
- `file`: 文件操作
- `data`: 数据处理
- `code`: 代码相关
- `text`: 文本处理
- `math`: 数学计算
- `ai`: AI/ML相关
- `utility`: 实用工具
- `general`: 通用

## 完整示例

```python
"""天气查询插件示例"""

import httpx
from typing import Dict, Any
from app.plugins import Plugin, Tool


class WeatherPlugin(Plugin):
    """天气查询插件"""
    name = "weather"
    description = "查询天气信息"
    version = "1.0.0"
    author = "Fugue Team"
    tags = ["weather", "utility"]

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key", "")

    async def setup(self):
        """初始化HTTP客户端"""
        self.client = httpx.AsyncClient(timeout=10)

    async def cleanup(self):
        """清理HTTP客户端"""
        await self.client.aclose()

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称（英文）"
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "description": "温度单位",
                    "default": "metric"
                }
            },
            "required": ["city"]
        },
        permissions="safe",
        category="utility"
    )
    async def get_weather(self, city: str, units: str = "metric") -> str:
        """获取天气信息"""
        try:
            # 使用OpenWeatherMap API
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "units": units,
                "appid": self.api_key,
            }

            response = await self.client.get(url, params=params)
            data = response.json()

            if response.status_code != 200:
                return f"Error: {data.get('message', 'Unknown error')}"

            # 解析天气数据
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            unit_symbol = "°C" if units == "metric" else "°F"

            return (
                f"Weather in {city}:\n"
                f"- Temperature: {temp}{unit_symbol}\n"
                f"- Humidity: {humidity}%\n"
                f"- Conditions: {description}"
            )

        except Exception as e:
            return f"Error fetching weather: {str(e)}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                },
                "days": {
                    "type": "integer",
                    "description": "预报天数（1-5）",
                    "default": 3
                }
            },
            "required": ["city"]
        },
        permissions="safe",
        category="utility"
    )
    async def get_forecast(self, city: str, days: int = 3) -> str:
        """获取天气预报"""
        # 实现预报逻辑...
        return f"Forecast for {city} ({days} days): ..."

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not self.api_key:
            return {
                "healthy": False,
                "message": "API key not configured"
            }
        return {
            "healthy": True,
            "message": "Weather plugin ready"
        }
```

## API接口

插件系统提供以下REST API：

### 列出所有插件
```
GET /api/v1/plugins/
```

### 列出所有工具
```
GET /api/v1/plugins/tools?category=search&permission=safe
```

### 执行工具
```
POST /api/v1/plugins/execute/{tool_name}
Content-Type: application/json

{
    "tool_name": "web_search",
    "arguments": {
        "query": "AI agent frameworks"
    }
}
```

### 获取Schema
```
GET /api/v1/plugins/schemas/openai
GET /api/v1/plugins/schemas/anthropic
```

### 健康检查
```
POST /api/v1/plugins/health-check
```

## 最佳实践

### 1. 错误处理
```python
@Tool(...)
async def my_tool(self, input: str) -> str:
    try:
        result = await some_operation(input)
        return f"Success: {result}"
    except ValueError as e:
        return f"Invalid input: {e}"
    except Exception as e:
        return f"Error: {e}"
```

### 2. 输入验证
```python
@Tool(
    input_schema={
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "format": "email",
                "description": "Email address"
            }
        },
        "required": ["email"]
    }
)
async def validate_email(self, email: str) -> str:
    # Pydantic或其他验证库会自动验证
    ...
```

### 3. 资源管理
```python
async def setup(self):
    self.pool = await create_db_pool()

async def cleanup(self):
    await self.pool.close()
```

### 4. 配置管理
```python
def __init__(self, config: Dict[str, Any] = None):
    super().__init__(config)
    self.api_key = self.config.get("api_key")
    self.timeout = self.config.get("timeout", 30)
```

### 5. 日志记录
```python
import logging

logger = logging.getLogger(__name__)

@Tool(...)
async def my_tool(self, ...):
    logger.info(f"Executing my_tool with args: {...}")
    try:
        result = ...
        logger.info(f"Tool executed successfully")
        return result
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise
```

## 配置插件

在 `plugin_configs` 表中配置插件：

```sql
INSERT INTO plugin_configs (
    id, user_id, plugin_name, plugin_version,
    enabled, config, source
) VALUES (
    uuid(), 'user-id', 'weather', '1.0.0',
    true, '{"api_key": "your-api-key"}', 'local'
);
```

或通过API：
```json
POST /api/v1/plugins/config
{
    "plugin_name": "weather",
    "config": {
        "api_key": "your-api-key"
    }
}
```

## 发布插件

### 1. 本地分享
直接将插件文件分享给其他用户，放到他们的 `plugins/` 目录。

### 2. 插件市场（计划中）
未来可以通过插件市场发布和分享插件。

## 故障排查

### 插件未加载
1. 检查文件是否在正确目录
2. 检查类是否继承 `Plugin`
3. 检查必要的类属性是否定义
4. 查看后端日志

### 工具执行失败
1. 检查输入参数是否符合schema
2. 检查权限设置
3. 查看错误日志
4. 测试健康检查

### 性能问题
1. 使用 `async` 异步操作
2. 设置合理的超时时间
3. 避免阻塞操作
4. 使用连接池

## 示例插件

查看 `backend/app/plugins/plugins/example_plugin.py` 获取完整示例。

## 支持

- 文档: https://docs.fugue.dev/plugins
- 示例: https://github.com/fugue/plugin-examples
- 社区: https://discord.gg/fugue
