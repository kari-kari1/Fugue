"""速率限制器 — C6: Redis 模式 + 内存降级"""

import time
import logging
from typing import Optional, Dict, List
from collections import defaultdict

from app.core.config import settings

logger = logging.getLogger(__name__)


class _MemoryRateLimiter:
    """内存滑动窗口速率限制器（Redis 不可用时的降级方案）"""

    def __init__(self):
        self._data: Dict[str, List[float]] = defaultdict(list)

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds
        # 清理过期条目
        self._data[key] = [t for t in self._data[key] if t > window_start]
        if len(self._data[key]) >= limit:
            logger.warning(f"Rate limit exceeded for key {key}: {len(self._data[key])}/{limit}")
            return False
        self._data[key].append(now)
        return True


class RedisRateLimiter:
    """Redis 滑动窗口速率限制器"""

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            from app.core.redis import get_redis_client
            self._redis = get_redis_client()
        return self._redis

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        redis = await self._get_redis()
        now = time.time()
        window_start = now - window_seconds

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        _, _, count, _ = await pipe.execute()

        if count > limit:
            logger.warning(f"Rate limit exceeded for key {key}: {count}/{limit}")
            return False
        return True


_rate_limiter = None


def get_rate_limiter():
    """获取速率限制器单例（C6: 自动降级到内存模式）"""
    global _rate_limiter
    if _rate_limiter is None:
        if settings.USE_REDIS:
            _rate_limiter = RedisRateLimiter()
            logger.info("Rate limiter: Redis mode")
        else:
            _rate_limiter = _MemoryRateLimiter()
            logger.info("Rate limiter: in-memory fallback (no Redis)")
    return _rate_limiter
