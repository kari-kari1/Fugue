"""API Key管理API — 用于REST API发布功能"""

import logging
import secrets
import hashlib
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DatabaseSession, CurrentUser
from app.models.api_key import APIKey
from app.models.published_workflow import PublishedWorkflow

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── 请求/响应模型 ───


class APIKeyCreate(BaseModel):
    """创建API Key请求"""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=lambda: ["execute"])
    rate_limit: int = Field(default=1000, ge=10, le=10000)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API Key响应"""
    id: str
    name: str
    key_prefix: str
    is_active: bool
    permissions: List[str]
    rate_limit: int
    last_used_at: Optional[str]
    expires_at: Optional[str]
    created_at: str


class WorkflowPublishRequest(BaseModel):
    """发布工作流请求"""
    slug: str = Field(..., min_length=3, max_length=100, pattern="^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = False
    version: str = "1.0.0"
    rate_limit: int = Field(default=100, ge=10, le=1000)


class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    inputs: dict = Field(default_factory=dict)
    callback_url: Optional[str] = None
    timeout: Optional[int] = Field(None, ge=30, le=3600)


# ─── 辅助函数 ───


def generate_api_key() -> tuple[str, str, str]:
    """生成API Key

    Returns:
        (raw_key, key_hash, key_prefix)
    """
    raw_key = f"af_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:10]

    return raw_key, key_hash, key_prefix


async def get_api_key_from_header(
    db: AsyncSession,
    authorization: Optional[str],
) -> Optional[APIKey]:
    """从Authorization header获取API Key"""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    raw_key = authorization[7:]  # Remove "Bearer " prefix
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        )
    )
    return result.scalar_one_or_none()


# ─── API端点 ───


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取当前用户的API Key列表"""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        APIKeyResponse(
            id=str(key.id),
            name=key.name,
            key_prefix=key.key_prefix,
            is_active=key.is_active,
            permissions=key.permissions or [],
            rate_limit=key.rate_limit,
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            created_at=key.created_at.isoformat() if key.created_at else "",
        )
        for key in keys
    ]


@router.post("/")
async def create_api_key(
    data: APIKeyCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """创建新的API Key"""
    raw_key, key_hash, key_prefix = generate_api_key()

    expires_at = None
    if data.expires_in_days:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)

    api_key = APIKey(
        user_id=current_user.id,
        name=data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        permissions=data.permissions,
        rate_limit=data.rate_limit,
        expires_at=expires_at,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "key": raw_key,  # 仅在创建时返回完整key
        "key_prefix": key_prefix,
        "message": "请妥善保管API Key，此密钥仅显示一次",
    }


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除API Key"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")

    await db.delete(key)
    await db.commit()

    return {"success": True, "message": "API Key deleted"}


@router.patch("/{key_id}/toggle")
async def toggle_api_key(
    key_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """启用/禁用API Key"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")

    key.is_active = not key.is_active
    await db.commit()

    return {
        "success": True,
        "is_active": key.is_active,
    }
