"""速率限制器单元测试 - 使用mock"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.rate_limiter import RedisRateLimiter, get_rate_limiter


@pytest.fixture
def mock_redis():
    """创建mock Redis客户端

    redis.asyncio 中:
    - redis.pipeline() 是同步方法，返回 Pipeline 对象
    - pipe.execute() 是异步方法
    - pipe.zremrangebyscore/zadd/zcard/expire 是同步方法（入队命令，返回self）
    """
    redis = MagicMock()
    pipe = MagicMock()
    redis.pipeline.return_value = pipe
    pipe.execute = AsyncMock()
    pipe.zremrangebyscore.return_value = pipe
    pipe.zadd.return_value = pipe
    pipe.zcard.return_value = pipe
    pipe.expire.return_value = pipe
    return redis, pipe


@pytest.fixture
def limiter(mock_redis):
    """创建带mock Redis的RateLimiter实例"""
    redis, _ = mock_redis
    instance = RedisRateLimiter()
    instance._redis = redis
    return instance


class TestRateLimiter:
    """速率限制器测试套件"""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_within_limit(self, limiter, mock_redis):
        """请求次数在限制内时应返回True"""
        _, pipe = mock_redis
        pipe.execute.return_value = [None, None, 3, None]  # 3次请求，限制10

        result = await limiter.check_rate_limit("test_key", limit=10, window_seconds=60)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_blocks_over_limit(self, limiter, mock_redis):
        """请求次数超过限制时应返回False"""
        _, pipe = mock_redis
        pipe.execute.return_value = [None, None, 11, None]  # 11次请求，限制10

        result = await limiter.check_rate_limit("test_key", limit=10, window_seconds=60)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_exactly_at_limit(self, limiter, mock_redis):
        """请求次数恰好等于限制时应返回True（未超出）"""
        _, pipe = mock_redis
        pipe.execute.return_value = [None, None, 10, None]  # 10次请求，限制10

        result = await limiter.check_rate_limit("test_key", limit=10, window_seconds=60)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_uses_pipeline(self, limiter, mock_redis):
        """应使用pipeline执行多个Redis命令"""
        redis, pipe = mock_redis
        pipe.execute.return_value = [None, None, 1, None]

        await limiter.check_rate_limit("my_key", limit=5, window_seconds=30)

        redis.pipeline.assert_called_once()
        pipe.zremrangebyscore.assert_called_once()
        pipe.zadd.assert_called_once()
        pipe.zcard.assert_called_once()
        pipe.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_default_window(self, limiter, mock_redis):
        """默认窗口应为60秒"""
        redis, pipe = mock_redis
        pipe.execute.return_value = [None, None, 1, None]

        before = time.time()
        await limiter.check_rate_limit("key", limit=5)
        after = time.time()

        # 检查 zremrangebyscore 调用参数中的 window_start
        # pipe.zremrangebyscore(key, 0, window_start) -> args = (key, 0, window_start)
        call_args = pipe.zremrangebyscore.call_args
        window_start = call_args[0][2]
        expected_start_min = before - 60
        expected_start_max = after - 60
        assert expected_start_min <= window_start <= expected_start_max

    @pytest.mark.asyncio
    async def test_check_rate_limit_custom_window(self, limiter, mock_redis):
        """自定义窗口时间应正确传递"""
        redis, pipe = mock_redis
        pipe.execute.return_value = [None, None, 1, None]

        before = time.time()
        await limiter.check_rate_limit("key", limit=5, window_seconds=120)
        after = time.time()

        call_args = pipe.zremrangebyscore.call_args
        window_start = call_args[0][2]
        expected_start_min = before - 120
        expected_start_max = after - 120
        assert expected_start_min <= window_start <= expected_start_max

    @pytest.mark.asyncio
    async def test_check_rate_limit_sets_expire(self, limiter, mock_redis):
        """应为key设置过期时间"""
        _, pipe = mock_redis
        pipe.execute.return_value = [None, None, 1, None]

        await limiter.check_rate_limit("ttl_key", limit=5, window_seconds=45)

        pipe.expire.assert_called_once_with("ttl_key", 45)

    @pytest.mark.asyncio
    async def test_check_rate_limit_lazy_redis_init(self):
        """Redis客户端应延迟初始化"""
        instance = RedisRateLimiter()
        assert instance._redis is None

        with patch("app.core.redis.get_redis_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client

            # 配置 pipeline mock
            pipe = MagicMock()
            mock_client.pipeline.return_value = pipe
            pipe.execute = AsyncMock(return_value=[None, None, 1, None])
            pipe.zremrangebyscore.return_value = pipe
            pipe.zadd.return_value = pipe
            pipe.zcard.return_value = pipe
            pipe.expire.return_value = pipe

            await instance.check_rate_limit("key", limit=5)

            assert instance._redis is mock_client
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_reuses_redis(self, limiter, mock_redis):
        """后续调用应复用已有的Redis连接"""
        _, pipe = mock_redis
        pipe.execute.return_value = [None, None, 1, None]

        await limiter.check_rate_limit("key1", limit=5)
        await limiter.check_rate_limit("key2", limit=5)

        # Redis客户端不应被重新创建
        assert limiter._redis is not None


class TestGetRateLimiter:
    """单例工厂测试"""

    def test_get_rate_limiter_returns_singleton(self):
        """get_rate_limiter应返回同一实例"""
        with patch("app.core.rate_limiter._rate_limiter", None):
            instance1 = get_rate_limiter()
            instance2 = get_rate_limiter()
            assert instance1 is instance2
            from app.core.rate_limiter import _MemoryRateLimiter
            assert isinstance(instance1, (RedisRateLimiter, _MemoryRateLimiter))

    def test_get_rate_limiter_creates_instance(self):
        """get_rate_limiter应创建实例"""
        with patch("app.core.rate_limiter._rate_limiter", None):
            instance = get_rate_limiter()
            from app.core.rate_limiter import _MemoryRateLimiter
            assert isinstance(instance, (RedisRateLimiter, _MemoryRateLimiter))
