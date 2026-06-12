"""MCP工具市场服务 — 提供预置MCP Server配置和一键安装功能"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# 预置MCP Server配置
PRESET_MCP_SERVERS = [
    {
        "id": "filesystem",
        "name": "文件系统",
        "description": "文件系统操作工具，支持读写文件、目录遍历、文件搜索等",
        "category": "file",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "<your-directory-path>"],
        "env": {},
        "tools_count": 10,
        "star_count": 1500,
        "verified": True,
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
        "setup_instructions": "1. 安装 Node.js 18+\n2. 修改 args 中的路径为你要访问的目录\n3. 点击连接即可使用",
    },
    {
        "id": "github",
        "name": "GitHub",
        "description": "GitHub API工具，支持仓库管理、Issue、PR、代码搜索等",
        "category": "development",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-token>"
        },
        "tools_count": 15,
        "star_count": 2000,
        "verified": True,
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/github",
        "setup_instructions": "1. 创建 GitHub Personal Access Token\n2. 设置环境变量 GITHUB_PERSONAL_ACCESS_TOKEN\n3. 点击连接",
    },
    {
        "id": "brave-search",
        "name": "Brave搜索",
        "description": "使用Brave Search API进行网络搜索",
        "category": "search",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
            "BRAVE_API_KEY": "<your-api-key>"
        },
        "tools_count": 2,
        "star_count": 800,
        "verified": True,
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search",
        "setup_instructions": "1. 注册 Brave Search API（免费额度）\n2. 获取 API Key\n3. 设置环境变量 BRAVE_API_KEY",
    },
    {
        "id": "postgres",
        "name": "PostgreSQL",
        "description": "PostgreSQL数据库查询和管理工具",
        "category": "database",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "env": {
            "POSTGRES_CONNECTION_STRING": "postgresql://user:pass@localhost:5432/dbname"
        },
        "tools_count": 3,
        "star_count": 600,
        "verified": True,
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres",
        "setup_instructions": "1. 确保PostgreSQL可访问\n2. 设置连接字符串\n3. 点击连接",
    },
    {
        "id": "slack",
        "name": "Slack",
        "description": "Slack消息和频道管理工具",
        "category": "communication",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env": {
            "SLACK_BOT_TOKEN": "<your-bot-token>",
            "SLACK_TEAM_ID": "<your-team-id>"
        },
        "tools_count": 8,
        "star_count": 500,
        "verified": True,
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/slack",
        "setup_instructions": "1. 创建Slack App并获取Bot Token\n2. 获取Team ID\n3. 设置环境变量",
    },
    {
        "id": "puppeteer",
        "name": "Puppeteer",
        "description": "浏览器自动化工具，支持网页截图、PDF生成、网页交互",
        "category": "automation",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "env": {},
        "tools_count": 5,
        "star_count": 700,
        "verified": True,
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer",
        "setup_instructions": "确保系统已安装Chrome或Chromium浏览器",
    },
    {
        "id": "sqlite",
        "name": "SQLite",
        "description": "SQLite数据库查询和管理工具",
        "category": "database",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "<your-database-path>"],
        "env": {},
        "tools_count": 4,
        "star_count": 400,
        "verified": True,
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite",
        "setup_instructions": "1. 修改 db-path 为你的SQLite数据库路径\n2. 点击连接",
    },
    {
        "id": "memory",
        "name": "记忆存储",
        "description": "知识图谱记忆工具，支持实体和关系的存储、检索",
        "category": "ai",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {},
        "tools_count": 6,
        "star_count": 300,
        "verified": True,
        "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/memory",
        "setup_instructions": "无需额外配置，直接连接即可使用",
    },
]


class MCPMarketplaceService:
    """MCP工具市场服务"""

    def __init__(self):
        self._presets = {server["id"]: server for server in PRESET_MCP_SERVERS}

    def list_presets(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """列出预置的MCP Server配置

        Args:
            category: 按分类过滤
            search: 按关键词搜索

        Returns:
            预置配置列表
        """
        results = list(PRESET_MCP_SERVERS)

        if category:
            results = [s for s in results if s["category"] == category]

        if search:
            search_lower = search.lower()
            results = [
                s for s in results
                if search_lower in s["name"].lower()
                or search_lower in s["description"].lower()
            ]

        return results

    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """获取预置配置"""
        return self._presets.get(preset_id)

    def get_categories(self) -> List[Dict[str, Any]]:
        """获取所有分类"""
        categories = {}
        for server in PRESET_MCP_SERVERS:
            cat = server["category"]
            if cat not in categories:
                categories[cat] = {
                    "id": cat,
                    "name": self._get_category_name(cat),
                    "count": 0,
                }
            categories[cat]["count"] += 1

        return list(categories.values())

    def _get_category_name(self, category: str) -> str:
        """获取分类的中文名称"""
        names = {
            "file": "文件系统",
            "development": "开发工具",
            "search": "搜索引擎",
            "database": "数据库",
            "communication": "通讯协作",
            "automation": "自动化",
            "ai": "AI/ML",
            "general": "通用",
        }
        return names.get(category, category)

    def generate_install_command(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """生成安装命令

        Args:
            preset_id: 预置配置ID

        Returns:
            包含命令和说明的字典
        """
        preset = self.get_preset(preset_id)
        if not preset:
            return None

        return {
            "server_id": preset["id"],
            "command": preset["command"],
            "args": preset["args"],
            "env": preset["env"],
            "name": preset["name"],
            "description": preset["description"],
            "setup_instructions": preset["setup_instructions"],
        }

    def validate_config(
        self,
        command: str,
        args: List[str],
        env: Dict[str, str],
    ) -> Dict[str, Any]:
        """验证MCP Server配置

        Returns:
            验证结果，包含 success 和 errors
        """
        errors = []

        if not command:
            errors.append("命令不能为空")

        # 检查环境变量占位符
        for key, value in (env or {}).items():
            if value.startswith("<") and value.endswith(">"):
                errors.append(f"环境变量 {key} 需要配置实际值")

        return {
            "success": len(errors) == 0,
            "errors": errors,
        }


# 全局单例
_mcp_marketplace: Optional[MCPMarketplaceService] = None


def get_mcp_marketplace() -> MCPMarketplaceService:
    """获取MCP市场服务单例"""
    global _mcp_marketplace
    if _mcp_marketplace is None:
        _mcp_marketplace = MCPMarketplaceService()
    return _mcp_marketplace
