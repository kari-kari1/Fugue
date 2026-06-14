"""应用配置模块"""

import logging
import os
import secrets
import sys
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _default_db_url() -> str:
    """计算默认数据库路径 — PyInstaller 打包时使用 APPDATA，开发时用当前目录"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包模式 — 数据库放在用户数据目录（可写）
        data_dir = Path(os.environ.get("APPDATA", Path.home())) / "Fugue"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "fugue.db"
        return f"sqlite+aiosqlite:///{db_path.as_posix()}"
    # 开发模式 — 当前目录
    return "sqlite+aiosqlite:///./fugue.db"


def _default_db_url_sync() -> str:
    url = _default_db_url()
    return url.replace("sqlite+aiosqlite:///", "sqlite:///")


class Settings(BaseSettings):
    """应用配置"""

    # Application
    APP_NAME: str = "Fugue"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database — SQLite 桌面模式（PyInstaller 时自动使用 APPDATA 路径）
    DATABASE_URL: str = Field(default_factory=_default_db_url)
    DATABASE_URL_SYNC: str = Field(default_factory=_default_db_url_sync)

    # Redis（开发环境可选）
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False

    # JWT — 默认为空，首次运行自动生成安全密钥
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080

    # LLM Providers
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    # MinIO（开发环境可选）
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "fugue"
    MINIO_SECURE: bool = False
    USE_MINIO: bool = False

    # CORS — 含桌面应用协议
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "tauri://localhost",
        "https://tauri.localhost",
    ]

    # Celery（开发环境可选）
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    USE_CELERY: bool = False

    # ChromaDB（向量数据库，端口改为 8100 避免与后端 8000 冲突）
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8100
    USE_VECTOR_STORE: bool = True  # P1: 默认开启向量存储，支持知识库和 Agent 记忆

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _validate_settings(self) -> "Settings":
        """配置校验：自动补充密钥 + 安全性检查"""
        # DATABASE_URL 不能为空
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL 不能为空")

        # SECRET_KEY 未配置时自动生成
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(48)
            if self.DEBUG:
                logger.warning(
                    "SECRET_KEY 未配置，已自动生成临时密钥。"
                    "生产环境请在 .env 中设置 SECRET_KEY。"
                )

        # 非 DEBUG 模式下，禁止使用已知占位符
        _placeholder_patterns = (
            "change-me", "your-secret-key", "secret",
            "your-secret-key-change-in-production",
            "fugue-dev-secret",
        )
        if not self.DEBUG:
            key_lower = self.SECRET_KEY.lower()
            if any(p in key_lower for p in _placeholder_patterns) or len(self.SECRET_KEY) < 16:
                raise ValueError(
                    "生产模式(DEBUG=False)下 SECRET_KEY 不能使用占位符或过短密钥，"
                    "请在 .env 中设置至少 16 字符的随机密钥"
                )

        return self


settings = Settings()
