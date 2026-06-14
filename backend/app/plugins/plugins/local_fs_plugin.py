"""本地文件系统操作插件 — 提供AI文件读写、目录浏览工具"""

import logging
from typing import Any

from app.engine.local_fs_client import LOCAL_FS_PORT, list_directory, read_file, write_file
from app.plugins.base import Plugin, Tool

logger = logging.getLogger(__name__)


class LocalFSPlugin(Plugin):
    """本地文件系统操作工具（读写文件、浏览目录）"""

    name = "local_fs"
    description = "本地文件系统操作工具（读写文件、浏览目录）"
    version = "1.0.0"
    author = "Fugue Team"
    tags = ["filesystem", "local", "native"]

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                },
                "offset": {
                    "type": "integer",
                    "description": "起始行号（从1开始）"
                },
                "limit": {
                    "type": "integer",
                    "description": "读取行数"
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码（如 utf-8, gbk）"
                }
            },
            "required": ["path"]
        },
        permissions="safe",
        category="filesystem",
        version="1.0.0"
    )
    async def fs_read(
        self,
        path: str,
        offset: int = None,
        limit: int = None,
        encoding: str = None,
    ) -> str:
        """读取本地文件内容"""
        try:
            content = await read_file(path, encoding=encoding)

            if offset is not None or limit is not None:
                lines = content.splitlines(keepends=True)
                total = len(lines)
                start = (offset or 1) - 1
                if start < 0:
                    start = 0
                end = (start + limit) if limit else total
                if end > total:
                    end = total
                selected = lines[start:end]
                header = f"[行 {start + 1}-{end}/{total}]"
                return header + "\n" + "".join(selected)

            if len(content) > 500 * 1024:
                return (
                    content[: 500 * 1024]
                    + f"\n\n... 文件过大（{len(content)} 字符），已截断。"
                    + "请使用 offset 和 limit 参数分段读取。"
                )

            return content

        except FileNotFoundError:
            return f"❌ 文件不存在: {path}"
        except PermissionError:
            return f"❌ 没有权限访问: {path}"
        except RuntimeError as e:
            return f"❌ 读取失败: {e}"
        except Exception as e:
            return f"❌ 读取文件时发生未知错误: {e}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容"
                },
                "append": {
                    "type": "boolean",
                    "description": "是否追加模式",
                    "default": False
                }
            },
            "required": ["path", "content"]
        },
        permissions="restricted",
        category="filesystem",
        version="1.0.0"
    )
    async def fs_write(self, path: str, content: str, append: bool = False) -> str:
        """写入本地文件"""
        # 工作空间限制：如果设置了工作空间，只能写入工作空间内
        from app.engine.tools import _workspace_dir
        if _workspace_dir:
            from pathlib import Path
            resolved = Path(path).resolve()
            ws = Path(_workspace_dir).resolve()
            if not str(resolved).startswith(str(ws)):
                logger.warning(f"[LocalFS] fs_write blocked: {path} outside workspace {_workspace_dir}")
                return f"❌ 工作空间限制：路径 {path} 不在工作空间 {_workspace_dir} 内。\n请将文件保存到工作空间内，例如：{_workspace_dir}/output.docx"
        try:
            await write_file(path, content, append=append)
            mode = "追加" if append else "覆盖"
            return f"✅ 文件写入成功（{mode}模式）: {path}（{len(content)} 字符）"
        except PermissionError:
            return f"❌ 没有写入权限: {path}"
        except RuntimeError as e:
            return f"❌ 写入失败: {e}"
        except Exception as e:
            return f"❌ 写入文件时发生未知错误: {e}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目录路径"
                }
            },
            "required": ["path"]
        },
        permissions="safe",
        category="filesystem",
        version="1.0.0"
    )
    async def fs_list(self, path: str) -> str:
        """列出本地目录内容"""
        try:
            entries: list[dict[str, Any]] = await list_directory(path)

            dirs: list[dict[str, Any]] = []
            files: list[dict[str, Any]] = []
            for entry in entries:
                if entry.get("is_dir"):
                    dirs.append(entry)
                else:
                    files.append(entry)

            dirs.sort(key=lambda e: e.get("name", ""))
            files.sort(key=lambda e: e.get("name", ""))

            lines: list[str] = []
            lines.append(f"📁 {path}（共 {len(entries)} 项，{len(dirs)} 个目录，{len(files)} 个文件）")

            for d in dirs:
                lines.append(f"  [DIR] {d.get('name', '?')}")

            for f in files:
                size = f.get("size", 0)
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                lines.append(f"  {f.get('name', '?')} ({size_str})")

            return "\n".join(lines)

        except FileNotFoundError:
            return f"❌ 目录不存在: {path}"
        except PermissionError:
            return f"❌ 没有权限访问: {path}"
        except RuntimeError as e:
            return f"❌ 列出目录失败: {e}"
        except Exception as e:
            return f"❌ 列出目录时发生未知错误: {e}"

    async def setup(self):
        """插件初始化"""
        logger.info("LocalFSPlugin v%s initialized (LOCAL_FS_PORT=%s)", self.version, LOCAL_FS_PORT)

    async def cleanup(self):
        """插件清理"""
        logger.info("LocalFSPlugin v%s cleanup", self.version)

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return {
            "healthy": True,
            "message": f"LocalFSPlugin v{self.version} is running normally",
            "local_fs_port": LOCAL_FS_PORT,
        }


__all__ = ["LocalFSPlugin"]
