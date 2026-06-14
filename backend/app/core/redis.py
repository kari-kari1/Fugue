"""Redis客户端连接模块"""

import logging

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """获取Redis异步客户端（单例）"""
    global _redis_client
    if _redis_client is None:
        logger.info(f"Connecting to Redis: {settings.REDIS_URL}")
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client():
    """关闭Redis连接"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")
