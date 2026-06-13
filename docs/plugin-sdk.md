# AgentForge Plugin SDK 规范文档

> 报告第5章要求：设计 Plugin SDK 规档，提供标准化的插件开发接口。

## 概述

AgentForge 插件系统允许第三方开发者扩展平台能力。插件可以提供：

- **工具 (Tools)**: 可被智能体调用的外部能力
- **技能 (Skills)**: 可复用的任务模板和工作流
- **MCP 服务器**: 通过 Model Context Protocol 接入的外部工具

## 快速开始

### 1. 创建插件目录结构

```
my-plugin/
├── plugin.json          # 插件元数据
├── __init__.py          # 插件入口
├── tools/               # 工具定义
│   └── my_tool.py
├── skills/              # 技能定义
│   └── my_skill.json
└── requirements.txt     # 依赖
```

### 2. 定义 plugin.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "我的自定义插件",
  "author": "Your Name",
  "min_agentforge_version": "0.1.0",
  "tools": ["tools/my_tool.py"],
  "skills": ["skills/my_skill.json"],
  "dependencies": ["requests>=2.28"]
}
```

### 3. 实现工具

```python
# tools/my_tool.py
from app.plugins.base import Tool

@Tool(
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"}
        },
        "required": ["query"]
    },
    permissions="safe",
    category="search",
    version="1.0.0"
)
async def my_search(query: str) -> str:
    """自定义搜索工具"""
    # 实现逻辑
    return f"搜索结果: {query}"
```

### 4. 定义技能

```json
// skills/my_skill.json
{
  "name": "my-analysis",
  "description": "自定义分析技能",
  "version": "1.0.0",
  "category": "analysis",
  "tags": ["custom", "analysis"],
  "required_tools": ["my_search"],
  "prompt_template": "请分析以下内容：\n\n{input}",
  "parameters": {
    "input": {"type": "string", "required": true}
  }
}
```

## 工具接口规范

### Tool 装饰器参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `input_schema` | dict | 是 | JSON Schema 格式的输入参数定义 |
| `permissions` | str | 否 | 权限级别: `safe` / `caution` / `dangerous` |
| `category` | str | 否 | 工具分类: `data` / `search` / `media` / `code` 等 |
| `version` | str | 否 | 语义化版本号 |

### 权限级别

- `safe`: 只读操作，无需审批
- `caution`: 可能有副作用，半自动模式下需审批
- `dangerous`: 系统级操作（文件写入、代码执行等），默认需审批

### 输入验证

工具函数的类型注解会自动用于输入验证。支持的类型：

- `str`, `int`, `float`, `bool`
- `dict`, `list`
- `Optional[T]` — 可选参数

## 技能接口规范

### SkillDefinition 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 唯一标识符 (kebab-case) |
| `description` | string | 是 | 一句话描述 |
| `version` | string | 是 | 语义化版本号 |
| `category` | string | 否 | 分类标签 |
| `tags` | string[] | 否 | 搜索标签 |
| `parameters` | object | 否 | 参数定义 (JSON Schema) |
| `required_tools` | string[] | 否 | 依赖的工具列表 |
| `prompt_template` | string | 否 | Agent 提示词模板 |
| `task_template` | object | 否 | 预定义任务结构 |

### prompt_template 变量

使用 `{variable_name}` 格式引用 parameters 中定义的参数。

## 发布流程

1. 开发并测试插件
2. 填写 `plugin.json` 元数据
3. 提交到 AgentForge Marketplace
4. 审核通过后发布

## 示例项目

参考 `backend/app/plugins/plugins/enanced_tools_plugin.py` 了解完整插件实现。

## 常见问题

**Q: 插件如何访问数据库？**
A: 通过 `from app.core.database import db_session_manager` 获取会话。

**Q: 插件如何发布事件？**
A: 通过 `from app.services.event_publisher import event_publisher` 发布 WebSocket 事件。

**Q: 插件如何注册 MCP 工具？**
A: 实现 MCP 协议接口，在 plugin.json 中声明 MCP 配置。
