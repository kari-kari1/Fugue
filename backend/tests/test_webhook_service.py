"""Webhook服务单元测试（数据库持久化版本）"""

import hmac
import hashlib
import json
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models.base import Base
from app.models.webhook import Webhook


# ── 测试数据库引擎（文件型SQLite，避免 :memory: 连接隔离问题） ──────────

_TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "_test_webhook.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """每个测试前建表，测试后清表"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def service():
    """创建 WebhookService 实例（patch 数据库会话）"""
    from app.services.webhook_service import WebhookService

    svc = WebhookService()
    svc._session_factory = TestSessionLocal
    yield svc
    await svc.close()


# ── 辅助工具 ────────────────────────────────────────────────────────────


def _mock_response(status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    return resp


def _mock_response_error(status_code=500):
    resp = MagicMock()
    resp.status_code = status_code
    return resp


# ── register_webhook 测试 ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_webhook(service):
    """注册webhook应成功创建数据库记录"""
    result = await service.register_webhook(
        user_id="user1",
        url="https://example.com/hook",
        events=["execution.completed"],
        secret="test-secret",
    )

    assert result["url"] == "https://example.com/hook"
    assert result["events"] == ["execution.completed"]
    assert result["is_active"] is True
    assert result["failure_count"] == 0
    assert result["last_triggered_at"] is None
    assert "id" in result
    assert "created_at" in result

    # 验证记录确实写入了数据库
    async with TestSessionLocal() as db:
        from sqlalchemy import select
        db_result = await db.execute(select(Webhook))
        rows = db_result.scalars().all()
        assert len(rows) == 1
        assert rows[0].user_id == "user1"
        assert rows[0].secret_hash == "test-secret"


@pytest.mark.asyncio
async def test_register_webhook_no_secret(service):
    """注册无密钥webhook应成功"""
    result = await service.register_webhook(
        user_id="user1",
        url="https://example.com/hook",
        events=["execution.completed"],
    )
    assert result["is_active"] is True
    assert "id" in result


@pytest.mark.asyncio
async def test_register_webhook_multiple(service):
    """同一用户注册多个webhook应各自有独立ID"""
    r1 = await service.register_webhook("user1", "https://a.com", ["execution.completed"])
    r2 = await service.register_webhook("user1", "https://b.com", ["execution.failed"])

    assert r1["id"] != r2["id"]

    webhooks = await service.get_user_webhooks("user1")
    assert len(webhooks) == 2


# ── unregister_webhook 测试 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unregister_webhook(service):
    """删除存在的webhook应返回True"""
    reg = await service.register_webhook("user1", "https://example.com", ["execution.completed"])

    result = await service.unregister_webhook("user1", reg["id"])
    assert result is True

    # 数据库中应无记录
    webhooks = await service.get_user_webhooks("user1")
    assert len(webhooks) == 0


@pytest.mark.asyncio
async def test_unregister_webhook_nonexistent(service):
    """删除不存在的webhook应返回False"""
    result = await service.unregister_webhook("user1", "wh_nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_unregister_webhook_wrong_user(service):
    """删除不属于用户的webhook应返回False"""
    reg = await service.register_webhook("user1", "https://example.com", ["execution.completed"])

    result = await service.unregister_webhook("user2", reg["id"])
    assert result is False


# ── get_user_webhooks 测试 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_webhooks(service):
    """获取用户webhook列表应返回该用户的所有记录"""
    await service.register_webhook("user1", "https://a.com", ["execution.completed"])
    await service.register_webhook("user1", "https://b.com", ["execution.failed"])
    await service.register_webhook("user2", "https://c.com", ["task.completed"])

    webhooks = await service.get_user_webhooks("user1")
    assert len(webhooks) == 2

    webhooks2 = await service.get_user_webhooks("user2")
    assert len(webhooks2) == 1


@pytest.mark.asyncio
async def test_get_user_webhooks_empty(service):
    """无webhook的用户应返回空列表"""
    webhooks = await service.get_user_webhooks("nonexistent")
    assert webhooks == []


# ── trigger_event 测试 ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trigger_event(service):
    """触发事件应向匹配的活跃webhook发送通知"""
    await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_response(200)

        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["event"] == "execution.completed"
        assert call_args[1]["json"]["data"] == {"run_id": "123"}


@pytest.mark.asyncio
async def test_trigger_event_skips_mismatched(service):
    """不应通知未订阅该事件的webhook"""
    await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.failed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})
        mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_trigger_event_skips_inactive(service):
    """不应通知已禁用的webhook"""
    reg = await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    # 直接将webhook设为不活跃
    async with TestSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Webhook).where(Webhook.id == reg["id"]))
        wh = result.scalar_one()
        wh.is_active = False
        await db.commit()

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})
        mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_trigger_event_parallel(service):
    """应并行通知多个webhook"""
    await service.register_webhook("user1", "https://a.com", ["execution.completed"])
    await service.register_webhook("user1", "https://b.com", ["execution.completed"])

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_response(200)

        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

        assert mock_post.call_count == 2


# ── _send_webhook 测试 ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_webhook_success(service):
    """发送成功应重置failure_count并更新last_triggered_at"""
    reg = await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_response(200)

        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

    # 验证数据库状态已更新
    async with TestSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Webhook).where(Webhook.id == reg["id"]))
        wh = result.scalar_one()
        assert wh.failure_count == 0
        assert wh.last_triggered_at is not None


@pytest.mark.asyncio
async def test_send_webhook_http_error_increments_failure(service):
    """HTTP错误应增加failure_count"""
    reg = await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_response_error(500)

        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

    async with TestSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Webhook).where(Webhook.id == reg["id"]))
        wh = result.scalar_one()
        assert wh.failure_count == 1
        assert wh.is_active is True


@pytest.mark.asyncio
async def test_send_webhook_exception_increments_failure(service):
    """网络异常应增加failure_count"""
    reg = await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection timeout")

        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

    async with TestSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Webhook).where(Webhook.id == reg["id"]))
        wh = result.scalar_one()
        assert wh.failure_count == 1


@pytest.mark.asyncio
async def test_send_webhook_disables_after_5_failures(service):
    """连续5次失败后应自动禁用webhook"""
    reg = await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection timeout")

        for _ in range(5):
            await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

    async with TestSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Webhook).where(Webhook.id == reg["id"]))
        wh = result.scalar_one()
        assert wh.failure_count == 5
        assert wh.is_active is False


@pytest.mark.asyncio
async def test_send_webhook_success_resets_failure_count(service):
    """发送成功应重置之前的failure_count"""
    reg = await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        # 先失败2次
        mock_post.side_effect = Exception("timeout")
        for _ in range(2):
            await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

        # 再成功1次
        mock_post.side_effect = None
        mock_post.return_value = _mock_response(200)
        await service.trigger_event("user1", "execution.completed", {"run_id": "456"})

    async with TestSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Webhook).where(Webhook.id == reg["id"]))
        wh = result.scalar_one()
        assert wh.failure_count == 0


# ── HMAC签名测试 ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_webhook_signs_with_secret(service):
    """应使用secret_hash进行HMAC签名"""
    await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
        secret="my-secret-key",
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_response(200)

        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert "X-Fugue-Signature" in headers
        assert headers["X-Fugue-Signature"].startswith("sha256=")

        # 验证签名正确
        body = call_args[1]["json"]
        message = json.dumps(body, sort_keys=True)
        expected_sig = hmac.new(
            b"my-secret-key",
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        assert headers["X-Fugue-Signature"] == f"sha256={expected_sig}"


@pytest.mark.asyncio
async def test_send_webhook_no_signature_without_secret(service):
    """无密钥的webhook不应包含签名头"""
    await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_response(200)

        await service.trigger_event("user1", "execution.completed", {"run_id": "123"})

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert "X-Fugue-Signature" not in headers


# ── test_webhook 测试 ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_test_webhook(service):
    """测试webhook应发送test事件"""
    reg = await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_response(200)

        result = await service.test_webhook(reg["id"], "user1")

    assert result["success"] is True
    assert result["message"] == "Test webhook sent successfully"


@pytest.mark.asyncio
async def test_test_webhook_not_found(service):
    """测试不存在的webhook应返回失败"""
    result = await service.test_webhook("wh_nonexistent", "user1")
    assert result["success"] is False
    assert result["error"] == "Webhook not found"


@pytest.mark.asyncio
async def test_test_webhook_failure(service):
    """发送失败时webhook的failure_count应递增（异常在_send_webhook内部捕获）"""
    reg = await service.register_webhook(
        "user1", "https://example.com/hook",
        ["execution.completed"],
    )

    with patch.object(service._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection refused")

        result = await service.test_webhook(reg["id"], "user1")

    # _send_webhook 在内部捕获异常并更新 failure_count，不会向上抛出
    assert result["success"] is True

    # 验证failure_count已递增
    async with TestSessionLocal() as db:
        from sqlalchemy import select
        db_result = await db.execute(select(Webhook).where(Webhook.id == reg["id"]))
        wh = db_result.scalar_one()
        assert wh.failure_count == 1


# ── 单例模式测试 ────────────────────────────────────────────────────────


def test_get_webhook_service_singleton():
    """get_webhook_service应返回同一实例"""
    from app.services.webhook_service import get_webhook_service, _webhook_service

    # 重置全局实例
    import app.services.webhook_service as ws_module
    ws_module._webhook_service = None

    s1 = get_webhook_service()
    s2 = get_webhook_service()
    assert s1 is s2


# ── WebhookEventType 测试 ──────────────────────────────────────────────


def test_webhook_event_types():
    """WebhookEventType枚举值应与API保持一致"""
    from app.services.webhook_service import WebhookEventType

    assert WebhookEventType.EXECUTION_COMPLETED.value == "execution.completed"
    assert WebhookEventType.EXECUTION_FAILED.value == "execution.failed"
    assert WebhookEventType.EXECUTION_STARTED.value == "execution.started"
    assert WebhookEventType.TASK_COMPLETED.value == "task.completed"
    assert WebhookEventType.TASK_FAILED.value == "task.failed"
    assert WebhookEventType.REVIEW_REQUIRED.value == "review.required"
