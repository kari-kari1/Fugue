"""Plugin市场API"""

import logging
import re
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DatabaseSession, CurrentUser
from app.models.plugin import PluginMarketplace
from app.models.plugin_review import PluginReview
from app.models.plugin import PluginConfig

logger = logging.getLogger(__name__)
router = APIRouter()

# B8: install_command 白名单前缀
_ALLOWED_INSTALL_PREFIXES = ("pip install", "pip3 install", "npm install", "yarn add", "pnpm add")


def _validate_install_command(v: Optional[str]) -> Optional[str]:
    """B8: 验证 install_command 仅允许安全的包管理器命令"""
    if v is None or v.strip() == "":
        return None
    cmd = v.strip().lower()
    if not any(cmd.startswith(prefix) for prefix in _ALLOWED_INSTALL_PREFIXES):
        raise ValueError(
            f"install_command 仅允许以下前缀: {_ALLOWED_INSTALL_PREFIXES}。"
            f"收到: {v[:50]}..."
        )
    # 额外检查：阻止 shell 注入（管道、重定向、后台执行）
    if re.search(r'[|;&$`\\]', v):
        raise ValueError("install_command 不允许包含 shell 特殊字符 (|;&$`\\)")
    return v


# ─── 请求/响应模型 ───


class PluginPublishRequest(BaseModel):
    """发布插件请求"""
    plugin_name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    long_description: Optional[str] = None
    current_version: str = Field(..., min_length=1, max_length=20)
    min_fugue_version: Optional[str] = None
    author: str = Field(..., min_length=1, max_length=100)
    author_email: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    category: str = Field(default="general", max_length=50)
    tags: List[str] = Field(default_factory=list)
    install_command: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    python_requires: str = Field(default=">=3.10")
    tools_list: List[str] = Field(default_factory=list)
    permissions_required: List[str] = Field(default_factory=list)

    @field_validator("install_command")
    @classmethod
    def validate_install_command(cls, v: Optional[str]) -> Optional[str]:
        return _validate_install_command(v)


class PluginUpdateRequest(BaseModel):
    """更新插件请求"""
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    long_description: Optional[str] = None
    current_version: Optional[str] = Field(None, max_length=20)
    min_fugue_version: Optional[str] = None
    author: Optional[str] = Field(None, max_length=100)
    author_email: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    install_command: Optional[str] = None
    dependencies: Optional[List[str]] = None
    python_requires: Optional[str] = None
    tools_list: Optional[List[str]] = None
    permissions_required: Optional[List[str]] = None

    @field_validator("install_command")
    @classmethod
    def validate_install_command(cls, v: Optional[str]) -> Optional[str]:
        return _validate_install_command(v)


class PluginRateRequest(BaseModel):
    """评分插件请求"""
    rating: int = Field(..., ge=1, le=5)


class PluginReviewRequest(BaseModel):
    """添加评论请求"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# ─── 工具函数 ───


async def _get_plugin_or_404(db: AsyncSession, plugin_id: str) -> PluginMarketplace:
    """获取插件，不存在则抛出404"""
    result = await db.execute(
        select(PluginMarketplace).where(PluginMarketplace.id == plugin_id)
    )
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


def _check_author(plugin: PluginMarketplace, user_id: str):
    """检查当前用户是否为插件作者"""
    if plugin.publisher_id != user_id:
        raise HTTPException(status_code=403, detail="Only the author can perform this action")


# ─── API端点 ───


@router.post("/publish")
async def publish_plugin(
    request: PluginPublishRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """发布插件到市场"""
    # 检查插件名称是否已存在
    existing = await db.execute(
        select(PluginMarketplace).where(PluginMarketplace.plugin_name == request.plugin_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Plugin name already exists")

    plugin = PluginMarketplace(
        plugin_name=request.plugin_name,
        display_name=request.display_name,
        description=request.description,
        long_description=request.long_description,
        current_version=request.current_version,
        min_fugue_version=request.min_fugue_version,
        author=request.author,
        author_email=request.author_email,
        homepage=request.homepage,
        repository=request.repository,
        category=request.category,
        tags=request.tags,
        install_command=request.install_command,
        dependencies=request.dependencies,
        python_requires=request.python_requires,
        tools_list=request.tools_list,
        permissions_required=request.permissions_required,
        publisher_id=current_user.id,
    )

    db.add(plugin)
    await db.commit()
    await db.refresh(plugin)

    return {"success": True, "plugin": plugin.to_dict()}


@router.get("/list")
async def list_plugins(
    db: DatabaseSession,
    category: Optional[str] = Query(None, description="分类过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取市场插件列表"""
    query = select(PluginMarketplace).where(PluginMarketplace.status == "active")

    if category:
        query = query.where(PluginMarketplace.category == category)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                PluginMarketplace.plugin_name.ilike(pattern),
                PluginMarketplace.display_name.ilike(pattern),
                PluginMarketplace.description.ilike(pattern),
            )
        )

    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页查询
    offset = (page - 1) * page_size
    query = query.order_by(PluginMarketplace.download_count.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    plugins = result.scalars().all()

    return {
        "plugins": [p.to_dict() for p in plugins],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/installed")
async def get_installed_plugins(
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取当前用户已安装的插件"""
    result = await db.execute(
        select(PluginConfig)
        .where(PluginConfig.user_id == current_user.id)
        .where(PluginConfig.source == "marketplace")
    )
    installed = result.scalars().all()

    plugins = []
    for cfg in installed:
        # 查询市场插件信息
        pm_result = await db.execute(
            select(PluginMarketplace).where(PluginMarketplace.plugin_name == cfg.plugin_name)
        )
        pm = pm_result.scalar_one_or_none()
        plugins.append({
            "plugin_name": cfg.plugin_name,
            "plugin_version": cfg.plugin_version,
            "enabled": cfg.enabled,
            "config": cfg.config,
            "installed_at": cfg.created_at.isoformat() if cfg.created_at else None,
            "marketplace_info": pm.to_dict() if pm else None,
        })

    return {"plugins": plugins, "total": len(plugins)}


@router.get("/{plugin_id}")
async def get_plugin_detail(
    plugin_id: str,
    db: DatabaseSession,
):
    """获取插件详情（含评论统计）"""
    plugin = await _get_plugin_or_404(db, plugin_id)

    # 评论统计
    stats_result = await db.execute(
        select(
            func.count(PluginReview.id).label("review_count"),
            func.avg(PluginReview.rating).label("avg_rating"),
        ).where(PluginReview.plugin_id == plugin_id)
    )
    stats = stats_result.one()

    plugin_dict = plugin.to_dict()
    plugin_dict["review_count"] = stats.review_count or 0
    plugin_dict["avg_rating"] = round(float(stats.avg_rating), 2) if stats.avg_rating else None
    plugin_dict["long_description"] = plugin.long_description
    plugin_dict["min_fugue_version"] = plugin.min_fugue_version
    plugin_dict["author_email"] = plugin.author_email
    plugin_dict["homepage"] = plugin.homepage
    plugin_dict["repository"] = plugin.repository
    plugin_dict["install_command"] = plugin.install_command
    plugin_dict["dependencies"] = plugin.dependencies
    plugin_dict["python_requires"] = plugin.python_requires
    plugin_dict["tools_list"] = plugin.tools_list
    plugin_dict["permissions_required"] = plugin.permissions_required
    plugin_dict["status"] = plugin.status
    plugin_dict["publisher_id"] = plugin.publisher_id

    return plugin_dict


@router.put("/{plugin_id}")
async def update_plugin(
    plugin_id: str,
    request: PluginUpdateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """更新插件信息（仅作者）"""
    plugin = await _get_plugin_or_404(db, plugin_id)
    _check_author(plugin, current_user.id)

    update_fields = request.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(plugin, field, value)

    await db.commit()
    await db.refresh(plugin)

    return {"success": True, "plugin": plugin.to_dict()}


@router.delete("/{plugin_id}")
async def delete_plugin(
    plugin_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """删除插件（仅作者）"""
    plugin = await _get_plugin_or_404(db, plugin_id)
    _check_author(plugin, current_user.id)

    await db.delete(plugin)
    await db.commit()

    return {"success": True, "message": "Plugin deleted"}


@router.post("/{plugin_id}/install")
async def install_plugin(
    plugin_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """安装插件（更新下载量）"""
    plugin = await _get_plugin_or_404(db, plugin_id)

    if plugin.status != "active":
        raise HTTPException(status_code=400, detail="Plugin is not active")

    # 检查是否已安装
    existing = await db.execute(
        select(PluginConfig).where(
            PluginConfig.user_id == current_user.id,
            PluginConfig.plugin_name == plugin.plugin_name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Plugin already installed")

    # 创建安装记录
    config = PluginConfig(
        user_id=current_user.id,
        plugin_name=plugin.plugin_name,
        plugin_version=plugin.current_version,
        source="marketplace",
    )
    db.add(config)

    # 更新下载量
    plugin.download_count = (plugin.download_count or 0) + 1

    await db.commit()

    return {"success": True, "message": f"Plugin '{plugin.plugin_name}' installed", "plugin_name": plugin.plugin_name}


@router.post("/{plugin_id}/uninstall")
async def uninstall_plugin(
    plugin_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """卸载插件"""
    plugin = await _get_plugin_or_404(db, plugin_id)

    result = await db.execute(
        select(PluginConfig).where(
            PluginConfig.user_id == current_user.id,
            PluginConfig.plugin_name == plugin.plugin_name,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Plugin not installed")

    await db.delete(config)
    await db.commit()

    return {"success": True, "message": f"Plugin '{plugin.plugin_name}' uninstalled"}


@router.post("/{plugin_id}/rate")
async def rate_plugin(
    plugin_id: str,
    request: PluginRateRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """评分插件（1-5星）"""
    plugin = await _get_plugin_or_404(db, plugin_id)

    # 查找已有评分
    existing = await db.execute(
        select(PluginReview).where(
            PluginReview.plugin_id == plugin_id,
            PluginReview.user_id == current_user.id,
        )
    )
    review = existing.scalar_one_or_none()

    if review:
        review.rating = request.rating
    else:
        review = PluginReview(
            plugin_id=plugin_id,
            user_id=current_user.id,
            rating=request.rating,
        )
        db.add(review)

    await db.commit()

    # 重新计算平均分
    avg_result = await db.execute(
        select(func.avg(PluginReview.rating)).where(PluginReview.plugin_id == plugin_id)
    )
    avg_rating = avg_result.scalar()
    plugin.rating = int(round(float(avg_rating) * 100)) if avg_rating else 0

    count_result = await db.execute(
        select(func.count(PluginReview.id)).where(PluginReview.plugin_id == plugin_id)
    )
    plugin.star_count = count_result.scalar() or 0

    await db.commit()

    return {"success": True, "rating": request.rating, "avg_rating": round(float(avg_rating), 2) if avg_rating else None}


@router.get("/{plugin_id}/reviews")
async def get_reviews(
    plugin_id: str,
    db: DatabaseSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """获取插件评论列表"""
    await _get_plugin_or_404(db, plugin_id)

    count_result = await db.execute(
        select(func.count(PluginReview.id)).where(PluginReview.plugin_id == plugin_id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(PluginReview)
        .where(PluginReview.plugin_id == plugin_id)
        .order_by(PluginReview.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    reviews = result.scalars().all()

    return {
        "reviews": [r.to_dict() for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{plugin_id}/reviews")
async def add_review(
    plugin_id: str,
    request: PluginReviewRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """添加评论"""
    plugin = await _get_plugin_or_404(db, plugin_id)

    # 检查是否已有评论
    existing = await db.execute(
        select(PluginReview).where(
            PluginReview.plugin_id == plugin_id,
            PluginReview.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already reviewed this plugin. Use PUT to update.")

    review = PluginReview(
        plugin_id=plugin_id,
        user_id=current_user.id,
        rating=request.rating,
        comment=request.comment,
    )
    db.add(review)

    await db.commit()
    await db.refresh(review)

    # 更新插件平均分
    avg_result = await db.execute(
        select(func.avg(PluginReview.rating)).where(PluginReview.plugin_id == plugin_id)
    )
    avg_rating = avg_result.scalar()
    plugin.rating = int(round(float(avg_rating) * 100)) if avg_rating else 0

    count_result = await db.execute(
        select(func.count(PluginReview.id)).where(PluginReview.plugin_id == plugin_id)
    )
    plugin.star_count = count_result.scalar() or 0

    await db.commit()

    return {"success": True, "review": review.to_dict()}
