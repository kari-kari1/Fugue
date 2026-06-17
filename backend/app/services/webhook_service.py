"""Webhook服务 — 处理执行完成、失败等事件的回调通知（数据库持久化版本）"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.webhook import Webhook

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook事件类型"""
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_STARTED = "execution.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    REVIEW_REQUIRED = "review.required"


class WebhookService:
    """Webhook服务（数据库持久化）"""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=10)
        self._session_factory = AsyncSessionLocal

    async def register_webhook(
        self,
        user_id: str,
        url: str,
        events: list[str],
        secret: str | None = None,
    ) -> dict[str, Any]:
        """注册Webhook

        Args:
            user_id: 用户ID
            url: 回调URL
            events: 订阅的事件列表
            secret: 签名密钥（可选）

        Returns:
            Webhook配置
        """
        webhook = Webhook(
            user_id=user_id,
            url=url,
            events=events,
            is_active=True,
            failure_count=0,
            secret_hash=secret,  # 存储原始密钥用于HMAC签名
        )

        async with self._session_factory() as db:
            db.add(webhook)
            await db.commit()
            await db.refresh(webhook)

        result = webhook.to_dict()
        logger.info(f"Registered webhook {result['id']} for user {user_id}")
        return result

    async def unregister_webhook(self, user_id: str, webhook_id: str) -> bool:
        """取消注册Webhook"""
        async with self._session_factory() as db:
            result = await db.execute(
                delete(Webhook).where(
                    Webhook.id == webhook_id,
                    Webhook.user_id == user_id,
                )
            )
            await db.commit()
            return result.rowcount > 0

    async def trigger_event(
        self,
        user_id: str,
        event_type: str,
        payload: dict[str, Any],
    ):
        """触发事件并通知所有订阅者

        Args:
            user_id: 用户ID
            event_type: 事件类型
            payload: 事件数据
        """
        async with self._session_factory() as db:
            result = await db.execute(
                select(Webhook).where(
                    Webhook.user_id == user_id,
                    Webhook.is_active == True,  # noqa: E712
                )
            )
            webhooks = result.scalars().all()

        active_webhooks = [
            wh for wh in webhooks
            if event_type in (wh.events or [])
        ]

        if not active_webhooks:
            return

        logger.info(f"Triggering event {event_type} for user {user_id}, {len(active_webhooks)} webhooks")

        # 并行发送通知
        tasks = [
            self._send_webhook(wh, event_type, payload)
            for wh in active_webhooks
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: dict[str, Any],
    ):
        """发送Webhook通知"""
        webhook_id = webhook.id
        url = webhook.url

        try:
            body = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload,
            }

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Fugue-Webhook/1.0",
            }

            # 如果有secret，添加签名
            if webhook.secret_hash:
                message = json.dumps(body, sort_keys=True)
                signature = hmac.new(
                    webhook.secret_hash.encode(),
                    message.encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Fugue-Signature"] = f"sha256={signature}"

            response = await self._client.post(url, json=body, headers=headers)

            # 更新数据库状态
            async with self._session_factory() as db:
                webhook = await db.merge(webhook)
                webhook.last_triggered_at = datetime.utcnow()

                if response.status_code >= 400:
                    logger.warning(f"Webhook {webhook_id} returned {response.status_code}")
                    webhook.failure_count += 1
                else:
                    # 重置失败计数
                    webhook.failure_count = 0

                await db.commit()

        except Exception as e:
            logger.error(f"Failed to send webhook {webhook_id}: {e}")

            # 更新数据库：增加失败计数
            async with self._session_factory() as db:
                webhook = await db.merge(webhook)
                webhook.last_triggered_at = datetime.utcnow()
                webhook.failure_count += 1

                # 如果连续失败超过5次，禁用webhook
                if webhook.failure_count >= 5:
                    webhook.is_active = False
                    logger.warning(f"Webhook {webhook_id} disabled after 5 consecutive failures")

                await db.commit()

    async def get_user_webhooks(self, user_id: str) -> list[dict[str, Any]]:
        """获取用户的所有Webhook"""
        async with self._session_factory() as db:
            result = await db.execute(
                select(Webhook).where(Webhook.user_id == user_id)
            )
            webhooks = result.scalars().all()

        return [wh.to_dict() for wh in webhooks]

    async def test_webhook(self, webhook_id: str, user_id: str) -> dict[str, Any]:
        """测试Webhook"""
        async with self._session_factory() as db:
            result = await db.execute(
                select(Webhook).where(
                    Webhook.id == webhook_id,
                    Webhook.user_id == user_id,
                )
            )
            webhook = result.scalar_one_or_none()

        if not webhook:
            return {"success": False, "error": "Webhook not found"}

        try:
            await self._send_webhook(
                webhook,
                "test",
                {"message": "This is a test webhook", "timestamp": datetime.utcnow().isoformat()}
            )
            return {"success": True, "message": "Test webhook sent successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """关闭HTTP客户端"""
        await self._client.aclose()


# 全局单例
_webhook_service: WebhookService | None = None


def get_webhook_service() -> WebhookService:
    """获取Webhook服务单例"""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
