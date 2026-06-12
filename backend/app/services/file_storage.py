"""MinIO 文件存储服务"""

import io
import logging
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)

# 单例
_file_storage: Optional["FileStorageService"] = None


def get_file_storage() -> Optional["FileStorageService"]:
    """获取 FileStorageService 单例

    当 USE_MINIO=False 时返回 None，调用方需自行判断。
    """
    global _file_storage
    if not settings.USE_MINIO:
        return None
    if _file_storage is None:
        _file_storage = FileStorageService()
    return _file_storage


class FileStorageService:
    """基于 MinIO 的文件存储服务"""

    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保 Bucket 存在（同步，仅在初始化时调用）"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info("Created MinIO bucket: %s", self.bucket)
        except S3Error as exc:
            logger.error("Failed to ensure bucket %s: %s", self.bucket, exc)
            raise

    # ── 异步公共方法（使用 asyncio.to_thread 包装同步 I/O） ──

    async def ensure_bucket(self):
        """确保 Bucket 存在"""
        import asyncio
        try:
            exists = await asyncio.to_thread(self.client.bucket_exists, self.bucket)
            if not exists:
                await asyncio.to_thread(self.client.make_bucket, self.bucket)
                logger.info("Created MinIO bucket: %s", self.bucket)
        except S3Error as exc:
            logger.error("Failed to ensure bucket %s: %s", self.bucket, exc)
            raise

    async def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """上传文件到 MinIO

        Args:
            file_data: 文件内容
            object_name: 对象名（含路径，如 documents/user123/report.pdf）
            content_type: MIME 类型

        Returns:
            对象名
        """
        import asyncio
        data_stream = io.BytesIO(file_data)
        try:
            await asyncio.to_thread(
                self.client.put_object,
                self.bucket,
                object_name,
                data_stream,
                length=len(file_data),
                content_type=content_type,
            )
            logger.info("Uploaded %s to bucket %s", object_name, self.bucket)
            return object_name
        except S3Error as exc:
            logger.error("Upload failed for %s: %s", object_name, exc)
            raise

    async def download_file(self, object_name: str) -> bytes:
        """从 MinIO 下载文件

        Args:
            object_name: 对象名

        Returns:
            文件内容
        """
        import asyncio
        try:
            response = await asyncio.to_thread(
                self.client.get_object,
                self.bucket,
                object_name,
            )
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as exc:
            logger.error("Download failed for %s: %s", object_name, exc)
            raise

    async def delete_file(self, object_name: str) -> None:
        """从 MinIO 删除文件

        Args:
            object_name: 对象名
        """
        import asyncio
        try:
            await asyncio.to_thread(
                self.client.remove_object,
                self.bucket,
                object_name,
            )
            logger.info("Deleted %s from bucket %s", object_name, self.bucket)
        except S3Error as exc:
            logger.error("Delete failed for %s: %s", object_name, exc)
            raise

    async def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """生成预签名临时 URL

        Args:
            object_name: 对象名
            expires: 有效期（秒），默认 3600

        Returns:
            预签名 URL
        """
        import asyncio
        try:
            url = await asyncio.to_thread(
                self.client.presigned_get_object,
                self.bucket,
                object_name,
                expires=expires,
            )
            return url
        except S3Error as exc:
            logger.error("Presigned URL failed for %s: %s", object_name, exc)
            raise
