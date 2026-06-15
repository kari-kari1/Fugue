"""文件上传/下载 API 端点"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.services.file_storage import get_file_storage

logger = logging.getLogger(__name__)

router = APIRouter()

# 允许的最大文件大小：50 MB
MAX_FILE_SIZE = 50 * 1024 * 1024


# ── Schemas ──


class FileUploadOut(BaseModel):
    """文件上传响应"""
    object_name: str
    content_type: str
    size: int


class PresignedUrlOut(BaseModel):
    """预签名 URL 响应"""
    url: str
    expires_in: int


# ── Endpoints ──


@router.post("/upload", response_model=FileUploadOut)
async def upload_file(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    prefix: Optional[str] = Query(None, description="对象路径前缀，如 documents/kb-123"),
):
    """上传文件

    文件以 {prefix}/{user_id}/{uuid}_{filename} 的形式存储在 MinIO 中。
    """
    storage = get_file_storage()
    if storage is None:
        raise HTTPException(
            status_code=503,
            detail="文件存储服务未启用（USE_MINIO=False）",
        )

    # 读取文件内容并检查大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024} MB）",
        )

    # 构建对象名
    unique_id = uuid.uuid4().hex[:12]
    filename = file.filename or "unnamed"
    # B10: 清洗 prefix — 防止路径遍历
    if prefix:
        import posixpath
        # 去除首尾斜杠，规范化路径，拒绝包含 .. 的前缀
        path_prefix = prefix.strip("/")
        path_prefix = posixpath.normpath(path_prefix)
        if ".." in path_prefix:
            raise HTTPException(status_code=400, detail="非法路径前缀")
    else:
        path_prefix = "uploads"
    object_name = f"{path_prefix}/{current_user.id}/{unique_id}_{filename}"

    content_type = file.content_type or "application/octet-stream"

    try:
        await storage.upload_file(file_data=content, object_name=object_name, content_type=content_type)
    except Exception as exc:
        logger.error("Upload failed: %s", exc)
        raise HTTPException(status_code=500, detail="文件上传失败")

    return FileUploadOut(
        object_name=object_name,
        content_type=content_type,
        size=len(content),
    )


@router.get("/{object_name:path}")
async def download_file(
    object_name: str,
    current_user: CurrentUser,
    as_url: bool = Query(False, description="返回预签名 URL 而非文件内容"),
    expires: int = Query(3600, ge=60, le=604800, description="预签名有效期（秒）"),
):
    """下载文件或获取预签名 URL

    - 默认返回文件内容（二进制）
    - 传入 as_url=true 返回临时访问链接
    """
    storage = get_file_storage()
    if storage is None:
        raise HTTPException(
            status_code=503,
            detail="文件存储服务未启用（USE_MINIO=False）",
        )

    if as_url:
        try:
            url = await storage.get_presigned_url(object_name, expires=expires)
            return PresignedUrlOut(url=url, expires_in=expires)
        except Exception as exc:
            logger.error("Failed to get presigned URL for %s: %s", object_name, exc)
            raise HTTPException(status_code=404, detail="文件不存在或无法访问")

    try:
        data = await storage.download_file(object_name)
    except Exception as exc:
        logger.error("Download failed for %s: %s", object_name, exc)
        raise HTTPException(status_code=404, detail="文件不存在")

    # 尝试从对象名推断文件名
    filename = object_name.split("/")[-1] if "/" in object_name else object_name

    # 简单推断 content_type
    content_type = _guess_content_type(filename)

    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{object_name:path}")
async def delete_file(
    object_name: str,
    current_user: CurrentUser,
):
    """删除文件"""
    storage = get_file_storage()
    if storage is None:
        raise HTTPException(
            status_code=503,
            detail="文件存储服务未启用（USE_MINIO=False）",
        )

    try:
        await storage.delete_file(object_name)
    except Exception as exc:
        logger.error("Delete failed for %s: %s", object_name, exc)
        raise HTTPException(status_code=500, detail="文件删除失败")

    return {"message": "文件已删除", "object_name": object_name}


# ── 工具函数 ──

_CONTENT_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".json": "application/json",
    ".csv": "text/csv",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".html": "text/html",
    ".htm": "text/html",
}


def _guess_content_type(filename: str) -> str:
    """根据文件扩展名推断 Content-Type"""
    for ext, ct in _CONTENT_TYPE_MAP.items():
        if filename.lower().endswith(ext):
            return ct
    return "application/octet-stream"
