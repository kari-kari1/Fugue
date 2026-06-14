"""本地文件系统客户端 — 优先通过 Tauri local-fs HTTP 服务，回退到原生 Python 操作"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_fs_config() -> tuple:
    """动态读取 local-fs 服务配置，确保每次请求使用最新的环境变量。"""
    port = int(os.environ.get("LOCAL_FS_PORT", "0"))
    base = f"http://127.0.0.1:{port}/api/local-fs" if port else None
    token = os.environ.get("LOCAL_FS_TOKEN", "")
    return base, token


def get_local_fs_port() -> int:
    """获取当前 local-fs 端口（供插件健康检查等使用）"""
    return int(os.environ.get("LOCAL_FS_PORT", "0"))


# 向后兼容：动态代理对象（供 local_fs_plugin.py 导入使用）
class _FsPortProxy:
    """动态端口代理，支持 int() 转换和字符串表示"""
    def __repr__(self): return str(get_local_fs_port())
    def __int__(self): return get_local_fs_port()
    def __eq__(self, other): return get_local_fs_port() == other
    def __bool__(self): return get_local_fs_port() != 0


LOCAL_FS_PORT = _FsPortProxy()


def _is_tauri_available() -> bool:
    """检测 Tauri local-fs 服务是否可用"""
    port = int(os.environ.get("LOCAL_FS_PORT", "0"))
    return port > 0


async def _request(endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
    """向 Tauri local-fs 服务发送 POST 请求，自带重试逻辑。"""
    base_url, token = _get_fs_config()
    if base_url is None:
        raise RuntimeError("Tauri local-fs 服务不可用")

    url = f"{base_url}/{endpoint}"
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=data, headers=headers)
                resp.raise_for_status()
                result = resp.json()
                if isinstance(result, dict) and "error" in result:
                    raise RuntimeError(f"local-fs 错误: {result['error']}")
                return result
        except httpx.ConnectError:
            logger.debug("local-fs 连接失败 (第 %d/3 次)，1 秒后重试...", attempt + 1)
            await asyncio.sleep(1)

    raise RuntimeError(f"无法连接 local-fs 服务 ({url})")


# ── 原生 Python 文件操作回退 ──────────────────────────


def _resolve_path(path: str) -> Path:
    """解析路径：相对路径基于工作空间，绝对路径保持不变"""
    p = Path(path)
    if not p.is_absolute():
        port = int(os.environ.get("LOCAL_FS_PORT", "0"))
        if port > 0:
            # Tauri 模式下使用工作空间（从 LOCAL_FS_PORT 推断）
            from app.engine.tools import _workspace_dir
            base = _workspace_dir or Path.home() / "Desktop"
        else:
            base = Path.home() / "Desktop"
        p = base / p
    return p.expanduser().resolve()


async def read_file(path: str, encoding: str | None = None) -> str:
    """读取本地文件内容，返回文本。优先 Tauri，回退原生 Python。"""
    if _is_tauri_available():
        payload: dict[str, Any] = {"path": path}
        if encoding is not None:
            payload["encoding"] = encoding
        result = await _request("read", payload)
        return result["content"]

    # 原生回退
    p = _resolve_path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    enc = encoding or "utf-8"
    return p.read_text(encoding=enc)


async def write_file(path: str, content: str, append: bool = False) -> None:
    """写入本地文件。优先 Tauri，回退原生 Python。"""
    if _is_tauri_available():
        await _request("write", {"path": path, "content": content, "append": append})
        return

    # 原生回退
    p = _resolve_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with open(p, mode, encoding="utf-8") as f:
        f.write(content)


async def list_directory(path: str) -> list[Any]:
    """列出本地目录内容。优先 Tauri，回退原生 Python。"""
    if _is_tauri_available():
        result = await _request("list", {"path": path})
        return result["entries"]

    # 原生回退
    p = _resolve_path(path)
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(f"目录不存在: {path}")
    entries = []
    for item in sorted(p.iterdir()):
        stat = item.stat()
        entries.append({
            "name": item.name,
            "path": str(item),
            "is_dir": item.is_dir(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
        })
    return entries


async def get_metadata(path: str) -> dict[str, Any]:
    """获取本地文件/目录元数据。优先 Tauri，回退原生 Python。"""
    if _is_tauri_available():
        result = await _request("metadata", {"path": path})
        return result

    # 原生回退
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"路径不存在: {path}")
    stat = p.stat()
    return {
        "name": p.name,
        "path": str(p),
        "is_dir": p.is_dir(),
        "is_file": p.is_file(),
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
    }
