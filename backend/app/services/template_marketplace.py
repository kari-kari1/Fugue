"""模板市场服务 — 增强模板的分享、收藏、评分功能"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template
from app.models.user import User

logger = logging.getLogger(__name__)


class TemplateMarketplaceService:
    """模板市场服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_popular_templates(
        self,
        limit: int = 10,
        days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """获取热门模板

        Args:
            limit: 返回数量
            days: 时间范围（天），None表示所有时间

        Returns:
            热门模板列表
        """
        query = (
            select(
                Template,
                User.username.label("author_name"),
            )
            .join(User, Template.user_id == User.id)
            .where(Template.is_public == True)
        )

        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.where(Template.created_at >= cutoff)

        query = query.order_by(
            Template.use_count.desc(),
            Template.rating.desc(),
        ).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(row.Template.id),
                "name": row.Template.name,
                "description": row.Template.description,
                "category": row.Template.category,
                "author": row.author_name,
                "use_count": row.Template.use_count,
                "rating": row.Template.rating,
                "star_count": row.Template.star_count or 0,
                "created_at": row.Template.created_at.isoformat() if row.Template.created_at else None,
            }
            for row in rows
        ]

    async def get_trending_templates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取趋势模板（最近7天使用量增长最快的）

        这里简化实现：返回最近创建且使用量较高的模板
        """
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        query = (
            select(
                Template,
                User.username.label("author_name"),
            )
            .join(User, Template.user_id == User.id)
            .where(
                Template.is_public == True,
                Template.created_at >= seven_days_ago,
            )
            .order_by(Template.use_count.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(row.Template.id),
                "name": row.Template.name,
                "description": row.Template.description,
                "author": row.author_name,
                "use_count": row.Template.use_count,
                "trend": "hot" if row.Template.use_count > 10 else "rising",
            }
            for row in rows
        ]

    async def get_recommended_templates(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取推荐模板（基于用户历史使用）

        简化实现：返回用户常用分类的高评分模板
        """
        # 获取用户最常用的分类
        user_categories = await self._get_user_top_categories(user_id)

        if not user_categories:
            # 如果没有历史，返回热门模板
            return await self.get_popular_templates(limit=limit)

        # 获取这些分类的高评分模板
        query = (
            select(
                Template,
                User.username.label("author_name"),
            )
            .join(User, Template.user_id == User.id)
            .where(
                Template.is_public == True,
                Template.category.in_(user_categories),
                Template.user_id != user_id,  # 排除自己的
            )
            .order_by(Template.rating.desc(), Template.use_count.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(row.Template.id),
                "name": row.Template.name,
                "description": row.Template.description,
                "category": row.Template.category,
                "author": row.author_name,
                "use_count": row.Template.use_count,
                "rating": row.Template.rating,
            }
            for row in rows
        ]

    async def star_template(self, template_id: str, user_id: str) -> Dict[str, Any]:
        """收藏模板"""
        template = await self._get_template(template_id)
        if not template:
            return {"success": False, "error": "Template not found"}

        # 这里简化实现：增加star_count
        # 实际应该有独立的star记录表
        template.star_count = (template.star_count or 0) + 1
        await self.db.commit()

        return {
            "success": True,
            "star_count": template.star_count,
        }

    async def fork_template(
        self,
        template_id: str,
        user_id: str,
        new_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fork模板（复制为自己的模板）"""
        original = await self._get_template(template_id)
        if not original:
            return {"success": False, "error": "Template not found"}

        # 创建副本
        forked = Template(
            name=new_name or f"{original.name} (Fork)",
            description=original.description,
            category=original.category,
            icon=original.icon,
            difficulty=original.difficulty,
            agents_config=original.agents_config,
            tasks_config=original.tasks_config,
            connections_config=original.connections_config,
            process_type=original.process_type,
            tags=original.tags,
            is_builtin=False,
            is_public=False,
            user_id=user_id,
            forked_from_id=template_id,
        )

        self.db.add(forked)
        await self.db.flush()
        await self.db.refresh(forked)

        # 增加原模板的fork_count
        original.fork_count = (original.fork_count or 0) + 1
        await self.db.commit()

        return {
            "success": True,
            "forked_id": str(forked.id),
            "forked_name": forked.name,
        }

    async def rate_template(
        self,
        template_id: str,
        user_id: str,
        rating: int,
    ) -> Dict[str, Any]:
        """评分模板（1-5分）"""
        if rating < 1 or rating > 5:
            return {"success": False, "error": "Rating must be between 1 and 5"}

        template = await self._get_template(template_id)
        if not template:
            return {"success": False, "error": "Template not found"}

        # 简化实现：更新平均评分
        # 实际应该有独立的rating记录表
        if template.rating_count:
            new_total = template.rating * template.rating_count + rating
            template.rating_count += 1
            template.rating = new_total / template.rating_count
        else:
            template.rating = rating
            template.rating_count = 1

        await self.db.commit()

        return {
            "success": True,
            "rating": round(template.rating, 2),
            "rating_count": template.rating_count,
        }

    async def record_usage(self, template_id: str) -> None:
        """记录模板使用"""
        template = await self._get_template(template_id)
        if template:
            template.use_count = (template.use_count or 0) + 1
            await self.db.commit()

    async def get_user_templates(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """获取用户的模板列表"""
        query = (
            select(Template)
            .where(Template.user_id == user_id)
            .order_by(Template.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await self.db.execute(query)
        templates = result.scalars().all()

        # 统计总数
        count_query = select(func.count()).where(Template.user_id == user_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        return {
            "templates": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "use_count": t.use_count,
                    "rating": t.rating,
                    "star_count": t.star_count,
                    "is_public": t.is_public,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in templates
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def toggle_public(self, template_id: str, user_id: str) -> Dict[str, Any]:
        """切换模板的公开/私有状态"""
        template = await self._get_template(template_id)
        if not template:
            return {"success": False, "error": "Template not found"}

        if template.user_id != user_id:
            return {"success": False, "error": "Permission denied"}

        template.is_public = not template.is_public
        await self.db.commit()

        return {
            "success": True,
            "is_public": template.is_public,
        }

    async def _get_template(self, template_id: str) -> Optional[Template]:
        """获取模板"""
        result = await self.db.execute(
            select(Template).where(Template.id == template_id)
        )
        return result.scalar_one_or_none()

    async def _get_user_top_categories(self, user_id: str, limit: int = 3) -> List[str]:
        """获取用户最常用的模板分类"""
        # 这里简化实现：返回预设分类
        return ["AI开发", "数据分析", "内容创作"]
