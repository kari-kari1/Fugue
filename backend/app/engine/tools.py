"""工具注册表 — 定义内置工具的 schema、权限和执行逻辑"""

import asyncio
import logging
import os
import shutil
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_db_session():
    """获取数据库会话（用于工具内部访问数据库）"""
    from app.core.database import db_session_manager
    return db_session_manager.get_session()


# 文件工具沙箱根目录（桌面应用模式：使用用户主目录，不限制路径）
WORKSPACE_ROOT = Path(os.path.expanduser("~")).resolve()

# 工作空间目录（可通过执行引擎设置，用于限制文件操作范围）
_workspace_dir = os.getenv("FUGUE_WORKSPACE", None)


def set_workspace_dir(path: str):
    """设置工作空间目录（执行开始时调用）"""
    global _workspace_dir
    _workspace_dir = path


def clear_workspace_dir():
    """清除工作空间目录（执行结束时调用）"""
    global _workspace_dir
    _workspace_dir = None


def _validate_file_path(file_path: str) -> tuple[bool, str]:
    """验证文件路径。桌面应用模式：允许所有路径，但优先在工作空间内操作。"""
    try:
        resolved = Path(file_path).resolve()
        return True, str(resolved)
    except Exception as e:
        return False, f"[错误] 路径解析失败: {str(e)}"


# 代码执行沙箱 — 桌面应用模式，放宽导入限制
# 只阻止极端危险的操作（删除系统文件等），允许 os/pathlib/docx 等常用模块
_CODE_IMPORT_BLOCK = ""


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_call_id: str
    tool_name: str
    output: str
    success: bool = True
    duration_ms: int = 0
    error: str | None = None


class BaseTool(ABC):
    """工具基类"""
    name: str
    description: str
    category: str
    permissions: str  # 'safe' | 'caution' | 'dangerous'

    @abstractmethod
    def get_openai_schema(self) -> dict[str, Any]:
        """返回 OpenAI function calling 格式的 schema"""
        ...

    @abstractmethod
    def get_anthropic_schema(self) -> dict[str, Any]:
        """返回 Anthropic tool_use 格式的 schema"""
        ...

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> str:
        """执行工具，返回结果字符串"""
        ...


# ─── 具体工具实现 ───


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the internet for real-time information"
    category = "search"
    permissions = "safe"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Maximum results", "default": 5},
                    },
                    "required": ["query"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": "web_search",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum results", "default": 5},
                },
                "required": ["query"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        query = arguments.get("query", "")
        max_results = min(arguments.get("max_results", 5), 5)
        try:
            # I1: DuckDuckGo 异步化 — 包装到 asyncio.to_thread 避免阻塞事件循环
            def _search():
                from duckduckgo_search import DDGS
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append(r)
                return results

            results = await asyncio.to_thread(_search)

            if not results:
                return f'[搜索结果] 关于"{query}"未找到相关结果'

            output = f'[搜索结果] 关于"{query}"找到 {len(results)} 条结果：\n\n'
            for i, r in enumerate(results, 1):
                title = r.get("title", "")[:100]
                href = r.get("href", "")[:200]
                body = r.get("body", "")[:300]
                output += f"{i}. {title}\n   URL: {href}\n   摘要: {body}\n\n"
            return output.strip()[:4000]
        except ImportError:
            return "[错误] 搜索依赖未安装，请安装 duckduckgo-search: pip install duckduckgo-search"
        except Exception as e:
            return f"[错误] 搜索失败: {str(e)}"


class FileReadTool(BaseTool):
    name = "file_read"
    description = "Read the contents of a file"
    category = "file"
    permissions = "safe"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "file_read",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file"},
                        "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                    },
                    "required": ["file_path"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": "file_read",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file"},
                    "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                },
                "required": ["file_path"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        file_path = arguments.get("file_path", "")
        encoding = arguments.get("encoding", "utf-8")
        # B6: 路径沙箱验证
        is_valid, resolved = _validate_file_path(file_path)
        if not is_valid:
            return resolved
        try:
            # I4: 异步文件读取
            def _read():
                with open(resolved, encoding=encoding) as f:
                    return f.read(10000)
            content = await asyncio.to_thread(_read)
            return f"[文件内容] {file_path}:\n{content}"
        except FileNotFoundError:
            return f"[错误] 文件不存在: {file_path}"
        except PermissionError:
            return f"[错误] 无权限读取: {file_path}"
        except Exception as e:
            return f"[错误] 读取失败: {str(e)}"


class FileWriteTool(BaseTool):
    name = "file_write"
    description = "Write content to a file"
    category = "file"
    permissions = "caution"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "file_write",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to write"},
                        "content": {"type": "string", "description": "Content to write"},
                        "mode": {"type": "string", "enum": ["overwrite", "append"], "default": "overwrite"},
                    },
                    "required": ["file_path", "content"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": "file_write",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to write"},
                    "content": {"type": "string", "description": "Content to write"},
                    "mode": {"type": "string", "enum": ["overwrite", "append"], "default": "overwrite"},
                },
                "required": ["file_path", "content"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        file_path = arguments.get("file_path", "")
        content = arguments.get("content", "")
        mode = arguments.get("mode", "overwrite")
        # B6: 路径沙箱验证
        is_valid, resolved = _validate_file_path(file_path)
        if not is_valid:
            return resolved
        try:
            # I4: 异步文件写入
            def _write():
                file_mode = "a" if mode == "append" else "w"
                with open(resolved, file_mode, encoding="utf-8") as f:
                    f.write(content)
            await asyncio.to_thread(_write)
            return f"[成功] 已写入文件: {file_path} ({len(content)} 字符, 模式: {mode})"
        except PermissionError:
            return f"[错误] 无权限写入: {file_path}"
        except Exception as e:
            return f"[错误] 写入失败: {str(e)}"


class CodeExecuteTool(BaseTool):
    name = "code_execute"
    description = "Execute code in a sandboxed environment"
    category = "code"
    permissions = "dangerous"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "code_execute",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "language": {"type": "string", "enum": ["python", "javascript"], "description": "Language (bash removed for security)"},
                        "code": {"type": "string", "description": "Code to execute"},
                    },
                    "required": ["language", "code"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": "code_execute",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "enum": ["python", "javascript"], "description": "Language (bash removed for security)"},
                    "code": {"type": "string", "description": "Code to execute"},
                },
                "required": ["language", "code"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        language = arguments.get("language", "python")
        code = (arguments.get("code", "") or "").strip()

        if not code:
            return "[错误] 未提供代码内容。请使用 code 参数提供可执行的 Python/JavaScript 代码。"

        # B5: 检测运行时可用性
        if language == "python" and not shutil.which("python"):
            return "[错误] Python 运行时未安装或不在 PATH 中"
        if language == "javascript" and not shutil.which("node"):
            return "[错误] Node.js 运行时未安装或不在 PATH 中"
        # bash 已被移除
        if language == "bash":
            return "[错误] 安全限制：bash 执行已禁用，请使用 python 或 javascript"

        # 桌面应用模式：使用用户主目录作为工作目录（允许写入桌面/文档等）
        sandbox_dir = os.path.expanduser("~")

        # ── 构建实际命令 ──────────────────────────────────────
        from app.engine.sandbox import SandboxConfig, SandboxType, get_sandbox_manager
        sandbox_mgr = get_sandbox_manager()
        sandbox_type = sandbox_mgr._auto_select_sandbox()
        config = SandboxConfig(max_execution_time=30)

        if language == "python":
            # 注入沙箱限制（桌面模式已放宽）
            sandboxed_code = _CODE_IMPORT_BLOCK + "\n" + code if _CODE_IMPORT_BLOCK else code
            cmd_str = f"python -c {sandboxed_code!r}"
        elif language == "javascript":
            sandboxed_code = code
            cmd_str = f"node -e {code!r}"
        else:
            return f"[错误] 不支持的语言: {language}"

        # ── 命令安全验证 ──────────────────────────────────────
        validation_error = sandbox_mgr.validate_command(cmd_str, config)
        if validation_error:
            return f"[错误] 命令被安全策略拒绝: {validation_error}"

        # ── 沙箱执行 ──────────────────────────────────────────
        # NONE 模式（Windows）不走 cmd /c 包装，直接 subprocess 执行
        if sandbox_type == SandboxType.NONE:
            try:
                return await self._execute_direct(language, sandboxed_code, sandbox_dir)
            except TimeoutError:
                return "[错误] 代码执行超时 (30秒)"
            except Exception as e:
                return f"[错误] 执行失败: {str(e)}"

        # 真正的沙箱模式（bwrap / docker / seatbelt）
        try:
            result = await sandbox_mgr.execute_in_sandbox(
                command=cmd_str,
                workspace=sandbox_dir,
                config=config,
                sandbox_type=sandbox_type,
            )

            output = result.get("output", "").strip()
            err = result.get("error", "").strip()

            formatted = f"[代码执行] {language} (沙箱: {result.get('sandbox_type', 'unknown')}):\n"
            if output:
                formatted += f"输出:\n{output}\n"
            if err:
                formatted += f"错误:\n{err}\n"
            if not output and not err:
                formatted += "(无输出)"
            return formatted

        except Exception as e:
            # 沙箱不可用 — 不降级到直接执行，确保安全
            logger.error(f"[SANDBOX] 沙箱执行失败: {e}")
            return f"[错误] 沙箱执行失败，已拒绝直接执行以确保安全: {str(e)}"

    async def _execute_direct(self, language: str, code: str, sandbox_dir: str) -> str:
        """直接执行（沙箱降级路径 / NONE 模式）

        注意：此方法不经过 cmd /c 包装，可正确处理代码中的引号和换行符。
        """
        if language == "python":
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-c", code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=sandbox_dir,
            )
        elif language == "javascript":
            proc = await asyncio.create_subprocess_exec(
                "node", "-e", code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=sandbox_dir,
            )
        else:
            return f"[错误] 不支持的语言: {language}"

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()

        result = f"[代码执行] {language} (沙箱: none):\n"
        if output:
            result += f"输出:\n{output}\n"
        if err:
            result += f"错误:\n{err}\n"
        if not output and not err:
            result += "(无输出)"
        return result


class ApiCallTool(BaseTool):
    name = "api_call"
    description = "Make an HTTP request to an external API"
    category = "data"
    permissions = "caution"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "api_call",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "API endpoint URL"},
                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"], "default": "GET"},
                        "headers": {"type": "object", "description": "Request headers"},
                        "body": {"type": "object", "description": "Request body"},
                    },
                    "required": ["url"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": "api_call",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "API endpoint URL"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"], "default": "GET"},
                    "headers": {"type": "object", "description": "Request headers"},
                    "body": {"type": "object", "description": "Request body"},
                },
                "required": ["url"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        import ipaddress
        import socket
        from urllib.parse import urlparse

        import httpx
        url = arguments.get("url", "")
        method = arguments.get("method", "GET").upper()
        headers = arguments.get("headers") or {}
        body = arguments.get("body")
        # B11: SSRF 保护 — 检查 URL 是否解析到内部/私有 IP
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return f"[错误] 无效的 URL: {url}"
            # 解析域名为 IP
            resolved_ip = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(resolved_ip)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return f"[错误] 安全限制：不允许访问内部/私有网络地址 ({resolved_ip})"
        except Exception as e:
            return f"[错误] URL 解析失败: {str(e)}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.request(method, url, headers=headers, json=body)
                content = resp.text[:5000]
                return f"[API响应] {method} {url} (状态码: {resp.status_code}):\n{content}"
        except Exception as e:
            return f"[错误] API调用失败: {str(e)}"


class DatabaseQueryTool(BaseTool):
    name = "database_query"
    description = "Execute a SQL query against a database"
    category = "data"
    permissions = "dangerous"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "database_query",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query"},
                        "database": {"type": "string", "description": "Database connection string"},
                        "params": {"type": "object", "description": "Query parameters"},
                    },
                    "required": ["query"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": "database_query",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query"},
                    "database": {"type": "string", "description": "Database connection string"},
                    "params": {"type": "object", "description": "Query parameters"},
                },
                "required": ["query"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        query = arguments.get("query", "")
        query_stripped = query.strip()
        query_upper = query_stripped.upper()
        if not query_upper.startswith("SELECT"):
            return "[错误] 安全限制：仅允许 SELECT 查询。写操作需通过管理界面执行。"

        # B7: 阻止多语句注入（分号后有非空白字符即视为多语句）
        # 允许末尾分号，但中间不允许
        body = query_stripped.rstrip(";").rstrip()
        if ";" in body:
            return "[错误] 安全限制：不允许执行多条 SQL 语句。"

        # 禁止危险关键字
        dangerous = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "CREATE", "GRANT"]
        for kw in dangerous:
            if kw in query_upper:
                return f"[错误] 安全限制：检测到危险操作 {kw}，仅允许 SELECT 查询。"

        try:

            from app.core.database import get_engine

            async with get_engine().connect() as conn:
                # 设置语句超时
                result = await conn.execute(
                    __import__('sqlalchemy').text(query)
                )
                rows = result.fetchall()
                columns = list(result.keys()) if result.keys() else []

                if not rows:
                    return f"[数据库查询] SQL: {query}\n结果: 无数据"

                # 格式化输出
                output = f"[数据库查询] SQL: {query}\n"
                output += f"返回 {len(rows)} 行, 列: {', '.join(columns)}\n\n"

                # 转为表格格式（限制最多 50 行）
                display_rows = rows[:50]
                if columns:
                    output += " | ".join(str(c) for c in columns) + "\n"
                    output += "-" * 60 + "\n"
                    for row in display_rows:
                        output += " | ".join(str(v) if v is not None else "NULL" for v in row) + "\n"
                if len(rows) > 50:
                    output += f"\n... 共 {len(rows)} 行，仅显示前 50 行"

                return output.strip()
        except Exception as e:
            return f"[错误] 数据库查询失败: {str(e)}"


class ImageGenerationTool(BaseTool):
    name = "image_generation"
    description = "Generate an image from a text description"
    category = "media"
    permissions = "safe"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "image_generation",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Image description"},
                        "size": {"type": "string", "enum": ["256x256", "512x512", "1024x1024"], "default": "1024x1024"},
                        "style": {"type": "string", "enum": ["vivid", "natural"], "default": "vivid"},
                    },
                    "required": ["prompt"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": "image_generation",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image description"},
                    "size": {"type": "string", "enum": ["256x256", "512x512", "1024x1024"], "default": "1024x1024"},
                    "style": {"type": "string", "enum": ["vivid", "natural"], "default": "vivid"},
                },
                "required": ["prompt"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        prompt = arguments.get("prompt", "")
        size = arguments.get("size", "1024x1024")
        style = arguments.get("style", "vivid")

        # J3: 使用 Settings 读取 API Key（不再直接读 os.environ）
        from app.core.config import settings
        api_key = settings.OPENAI_API_KEY or ""
        if not api_key:
            return (
                f'[图像生成] 提示词: "{prompt}"\n'
                f"[提示] 需要配置 OPENAI_API_KEY 才能调用 DALL-E API。"
                f"请在环境变量中设置 OPENAI_API_KEY。"
            )

        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": size,
                        "style": style,
                        "response_format": "url",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            images = data.get("data", [])
            if not images:
                return "[图像生成] 未返回图像数据"

            image_url = images[0].get("url", "")
            revised_prompt = images[0].get("revised_prompt", "")

            output = f'[图像生成] 提示词: "{prompt}"\n'
            if revised_prompt and revised_prompt != prompt:
                output += f"优化后提示词: {revised_prompt}\n"
            output += f"图像URL: {image_url}\n"
            output += f"尺寸: {size}, 风格: {style}"
            return output
        except httpx.HTTPStatusError as e:
            return f"[错误] DALL-E API 请求失败 (HTTP {e.response.status_code}): {e.response.text[:500]}"
        except Exception as e:
            return f"[错误] 图像生成失败: {str(e)}"


class TextAnalysisTool(BaseTool):
    name = "text_analysis"
    description = "Perform structured analysis on text content"
    category = "analysis"
    permissions = "safe"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "text_analysis",
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to analyze"},
                        "analysis_type": {
                            "type": "string",
                            "enum": ["summarize", "sentiment", "keywords", "classify", "translate"],
                        },
                        "target_language": {"type": "string", "description": "Target language for translation"},
                    },
                    "required": ["text", "analysis_type"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": "text_analysis",
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["summarize", "sentiment", "keywords", "classify", "translate"],
                    },
                    "target_language": {"type": "string", "description": "Target language for translation"},
                },
                "required": ["text", "analysis_type"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        text = arguments.get("text", "")
        analysis_type = arguments.get("analysis_type", "summarize")
        target_language = arguments.get("target_language", "en")
        char_count = len(text)
        word_count = len(text.split())

        # 构建分析提示词
        PROMPTS = {
            "summarize": f"请对以下文本进行简洁的摘要，保留关键信息，控制在原文的 1/3 以内：\n\n{text}",
            "sentiment": f"请分析以下文本的情感倾向，返回：积极/中性/消极，以及置信度(0-1)和简要理由：\n\n{text}",
            "keywords": f"请从以下文本中提取 5-10 个最重要的关键词/短语，用逗号分隔：\n\n{text}",
            "classify": f"请对以下文本进行主题分类，返回最合适的分类标签(1-3个)和简要说明：\n\n{text}",
            "translate": f"请将以下文本翻译为{target_language}，保持原文的语气和格式：\n\n{text}",
        }

        prompt = PROMPTS.get(analysis_type, PROMPTS["summarize"])

        try:

            # J3: 使用 Settings 读取 API Key
            from app.core.config import settings as cfg
            from app.engine.llm_provider import get_llm_provider
            api_key = cfg.OPENAI_API_KEY or cfg.ANTHROPIC_API_KEY or ""
            if not api_key:
                return self._local_analysis(text, analysis_type, target_language, char_count, word_count)

            provider_name = "openai" if cfg.OPENAI_API_KEY else "anthropic"
            llm = get_llm_provider(provider_name, api_key=api_key)

            messages = [
                {"role": "system", "content": "你是一个专业的文本分析助手。请用简洁的中文回答。"},
                {"role": "user", "content": prompt},
            ]

            response = await llm.chat(messages=messages, temperature=0.3, max_tokens=1000)

            output = f"[文本分析] 类型: {analysis_type}, 原文 {char_count} 字符 / {word_count} 词\n\n"
            output += response.content
            if response.tokens_used:
                output += f"\n\n(消耗 {response.tokens_used} tokens)"
            return output

        except Exception:
            # LLM 调用失败时回退到本地分析
            return self._local_analysis(text, analysis_type, target_language, char_count, word_count)

    def _local_analysis(self, text: str, analysis_type: str, target_language: str,
                        char_count: int, word_count: int) -> str:
        """无 LLM 时的本地基础分析"""
        import re
        from collections import Counter

        if analysis_type == "summarize":
            sentences = re.split(r'[。！？.!?\n]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            summary = "。".join(sentences[:3]) + "。" if sentences else text[:200]
            return f"[文本摘要] 原文 {char_count} 字符 / {word_count} 词\n摘要: {summary}"

        elif analysis_type == "sentiment":
            positive = len(re.findall(r'[好优良佳棒赞喜乐成功赢]', text))
            negative = len(re.findall(r'[坏差糟悲失败输痛恨怒]', text))
            total = positive + negative
            if total == 0:
                return f"[情感分析] 原文 {char_count} 字符\n情感倾向: 中性 (置信度: 0.5)"
            ratio = positive / total
            label = "积极" if ratio > 0.6 else "消极" if ratio < 0.4 else "中性"
            return f"[情感分析] 原文 {char_count} 字符\n情感倾向: {label} (置信度: {ratio:.2f})"

        elif analysis_type == "keywords":
            # 中文按字符分词（简易），英文按空格
            if re.search(r'[一-鿿]', text):
                words = re.findall(r'[一-鿿]{2,6}', text)
            else:
                words = re.findall(r'[a-zA-Z]{3,}', text.lower())
            stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
            filtered = [w for w in words if w not in stop_words]
            common = Counter(filtered).most_common(10)
            keywords = [w for w, _ in common]
            return f"[关键词提取] 原文 {char_count} 字符\n关键词: {', '.join(keywords) if keywords else '无明显关键词'}"

        elif analysis_type == "translate":
            return f"[翻译] 原文 {char_count} 字符 → 目标语言: {target_language}\n[提示] 翻译功能需要配置 LLM API Key 才能使用"

        else:
            return f"[文本分析] 类型: {analysis_type}, 原文 {char_count} 字符 / {word_count} 词\n[提示] 高级分析需要配置 LLM API Key"


# ─── PDF 生成工具 ───

class PdfCreateTool(BaseTool):
    """创建 PDF 文档"""
    name = "pdf_create"
    description = "创建 PDF 文档。使用此工具将文本、表格或计算结果保存为 PDF 格式文件。支持中文。"
    category = "document"
    permissions = "safe"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "保存路径（绝对路径），如 C:/Users/HP/Desktop/output.pdf"},
                        "title": {"type": "string", "description": "PDF 文档标题"},
                        "content": {"type": "string", "description": "要写入 PDF 的文本内容（支持多行）"},
                    },
                    "required": ["path", "content"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "保存路径（绝对路径）"},
                    "title": {"type": "string", "description": "PDF 文档标题"},
                    "content": {"type": "string", "description": "要写入 PDF 的文本内容"},
                },
                "required": ["path", "content"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        path = arguments.get("path", "")
        title = arguments.get("title", "Document")
        content = arguments.get("content", "")

        if not path:
            return "[错误] 未提供保存路径。请提供 path 参数。"
        if not content:
            return "[错误] 未提供 PDF 内容。请提供 content 参数。"

        try:
            import os

            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfgen import canvas

            # Try to register Chinese font
            font_used = "Helvetica"
            chinese_fonts = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            ]
            for font_path in chinese_fonts:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont("CNFont", font_path))
                        font_used = "CNFont"
                        break
                    except Exception as font_err:
                        logger.debug(f"Font registration failed for {font_path}: {font_err}")
                        continue

            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            c = canvas.Canvas(path, pagesize=A4)
            width, height = A4

            # Title
            c.setFont(font_used, 18)
            c.drawString(50, height - 50, title[:80])

            # Content
            c.setFont(font_used, 11)
            y = height - 90
            for line in content.split("\n"):
                if y < 50:
                    c.showPage()
                    c.setFont(font_used, 11)
                    y = height - 50
                c.drawString(50, y, line[:120])
                y -= 18

            c.save()
            return f"[PDF 创建成功] {path}（标题: {title}，内容 {len(content)} 字符）"
        except Exception as e:
            return f"[PDF 创建失败] {str(e)}"


# ─── Agent 可访问的记忆工具（报告第1.3节） ───

class RememberTool(BaseTool):
    """Agent 主动记录关键信息到长期记忆"""
    name = "remember"
    description = "记录一条重要信息到长期记忆。当你学到关键信息、得出结论或发现模式时使用此工具。"
    category = "memory"
    permissions = "safe"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "要记录的内容"},
                        "memory_type": {"type": "string", "enum": ["conclusion", "feedback", "pattern"],
                                        "description": "记忆类型：conclusion(结论), feedback(反馈), pattern(模式发现)"},
                        "importance": {"type": "integer", "minimum": 0, "maximum": 5,
                                       "description": "重要程度 0-5, 5=极其重要"},
                    },
                    "required": ["content"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "要记录的内容"},
                    "memory_type": {"type": "string", "enum": ["conclusion", "feedback", "pattern"],
                                    "description": "记忆类型：conclusion(结论), feedback(反馈), pattern(模式发现)"},
                    "importance": {"type": "integer", "minimum": 0, "maximum": 5,
                                   "description": "重要程度 0-5"},
                },
                "required": ["content"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        content = arguments.get("content", "")
        memory_type = arguments.get("memory_type", "conclusion")
        importance = arguments.get("importance", 3)
        try:
            from app.services.memory_service import MemoryService
            async with get_db_session() as db:
                svc = MemoryService(db)
                result = await svc.save_memory(
                    agent_id="tool-remember", content=content,
                    memory_type=memory_type, importance=importance,
                )
                return f"[记忆已记录] id={getattr(result, 'id', '?')} type={memory_type} importance={importance}"
        except Exception as e:
            return f"[记忆记录失败] {str(e)}"


class RecallTool(BaseTool):
    """Agent 主动检索长期记忆"""
    name = "recall"
    description = "搜索你的长期记忆库，检索相关历史信息。当你需要回忆之前学到的内容时使用。"
    category = "memory"
    permissions = "safe"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "自然语言搜索查询"},
                        "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"},
                    },
                    "required": ["query"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "自然语言搜索查询"},
                    "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"},
                },
                "required": ["query"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        try:
            from app.services.memory_service import MemoryService
            async with get_db_session() as db:
                svc = MemoryService(db)
                results = await svc.recall_memories_scored(
                    agent_id="tool-recall", query=query, top_k=top_k,
                )
                if not results:
                    return "[记忆检索] 未找到相关记忆"
                lines = ["[记忆检索结果]"]
                for i, r in enumerate(results[:top_k], 1):
                    lines.append(f"{i}. [{r.get('memory_type', '?')}] {r.get('content', '')[:300]}")
                return "\n".join(lines)
        except Exception as e:
            return f"[记忆检索失败] {str(e)}"


class SearchKnowledgeTool(BaseTool):
    """Agent 搜索知识库"""
    name = "search_knowledge"
    description = "搜索已配置的知识库，查找相关文档资料。当你需要专业领域知识或参考文档时使用。"
    category = "memory"
    permissions = "safe"

    def get_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索查询"},
                        "kb_name": {"type": "string", "description": "指定知识库名称（可选，留空则搜索所有）"},
                        "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"},
                    },
                    "required": ["query"],
                },
            },
        }

    def get_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "kb_name": {"type": "string", "description": "指定知识库名称（可选）"},
                    "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"},
                },
                "required": ["query"],
            },
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        try:
            from app.services.memory_service import MemoryService
            async with get_db_session() as db:
                svc = MemoryService(db)
                results = await svc.retrieve_from_knowledge_base(
                    agent_id="tool-search", query=query, top_k=top_k,
                )
                if not results:
                    return "[知识库搜索] 未找到相关内容"
                lines = ["[知识库搜索结果]"]
                for i, r in enumerate(results[:top_k], 1):
                    lines.append(f"{i}. {r.get('content', r.get('text', ''))[:300]}")
                return "\n".join(lines)
        except Exception as e:
            return f"[知识库搜索失败] {str(e)}"


# ─── 工具注册表 ───

_TOOL_REGISTRY: dict[str, BaseTool] = {}


def _register_defaults():
    """注册所有内置工具"""
    tools = [
        WebSearchTool(), FileReadTool(), FileWriteTool(), CodeExecuteTool(),
        ApiCallTool(), DatabaseQueryTool(), ImageGenerationTool(), TextAnalysisTool(),
        PdfCreateTool(), RememberTool(), RecallTool(), SearchKnowledgeTool(),
    ]
    for t in tools:
        _TOOL_REGISTRY[t.name] = t


_register_defaults()


def get_tool(name: str) -> BaseTool | None:
    """按名称获取工具"""
    return _TOOL_REGISTRY.get(name)


def get_tools_by_names(names: list[str]) -> list[BaseTool]:
    """按名称列表获取工具"""
    return [_TOOL_REGISTRY[n] for n in names if n in _TOOL_REGISTRY]


def get_openai_tools(tool_names: list[str]) -> list[dict[str, Any]]:
    """将工具名列表转为 OpenAI function calling 格式"""
    return [_TOOL_REGISTRY[n].get_openai_schema() for n in tool_names if n in _TOOL_REGISTRY]


def get_anthropic_tools(tool_names: list[str]) -> list[dict[str, Any]]:
    """将工具名列表转为 Anthropic tool_use 格式"""
    return [_TOOL_REGISTRY[n].get_anthropic_schema() for n in tool_names if n in _TOOL_REGISTRY]


async def execute_tool(tool_name: str, arguments: dict[str, Any], call_id: str = "") -> ToolResult:
    """执行单个工具并返回结果（支持内置工具 + 插件工具）"""
    tool = _TOOL_REGISTRY.get(tool_name)
    if not tool:
        # 尝试从插件管理器查找
        plugin_result = await _try_execute_plugin_tool(tool_name, arguments)
        if plugin_result is not None:
            return ToolResult(
                tool_call_id=call_id, tool_name=tool_name,
                output=plugin_result, success=True,
            )
        return ToolResult(
            tool_call_id=call_id, tool_name=tool_name,
            output=f"[错误] 未知工具: {tool_name}", success=False,
        )
    start = time.monotonic()
    try:
        output = await tool.execute(arguments)
        duration = int((time.monotonic() - start) * 1000)
        return ToolResult(
            tool_call_id=call_id, tool_name=tool_name,
            output=output, success=True, duration_ms=duration,
        )
    except Exception as e:
        duration = int((time.monotonic() - start) * 1000)
        logger.error(f"Tool {tool_name} execution failed: {e}")
        return ToolResult(
            tool_call_id=call_id, tool_name=tool_name,
            output=f"[错误] 工具执行失败: {str(e)}", success=False,
            duration_ms=duration, error=str(e),
        )


async def _try_execute_plugin_tool(tool_name: str, arguments: dict[str, Any]) -> str | None:
    """尝试通过插件管理器执行工具，返回 None 表示工具不存在"""
    try:
        from app.plugins.manager import get_plugin_manager
        manager = get_plugin_manager()
        tool_meta = manager.tools.get(tool_name)
        if not tool_meta or not tool_meta.func:
            return None
        result = await tool_meta.func(**arguments)
        return str(result)
    except Exception as e:
        logger.error(f"Plugin tool {tool_name} execution failed: {e}")
        return f"[错误] 插件工具执行失败: {e}"


def get_plugin_tool_schemas(provider: str = "openai") -> list[dict[str, Any]]:
    """获取所有已加载插件的工具 schema"""
    try:
        from app.plugins.manager import get_plugin_manager
        manager = get_plugin_manager()
        schemas = []
        for tool_name, tool_meta in manager.tools.items():
            if provider == "anthropic":
                schemas.append(tool_meta.to_anthropic_schema())
            else:
                schemas.append(tool_meta.to_openai_schema())
        return schemas
    except Exception as e:
        logger.warning(f"Failed to get plugin tool schemas: {e}")
        return []
