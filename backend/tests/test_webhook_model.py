"""Webhook模型测试"""

from app.models.webhook import Webhook


def test_webhook_to_dict():
    """测试Webhook序列化"""
    webhook = Webhook(
        url="https://example.com/hook",
        events=["execution.completed"],
        is_active=True,
    )
    data = webhook.to_dict()
    assert data["url"] == "https://example.com/hook"
    assert data["events"] == ["execution.completed"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_webhook_repr():
    """测试Webhook字符串表示"""
    webhook = Webhook(url="https://example.com/hook", is_active=True)
    assert repr(webhook) == "<Webhook https://example.com/hook (active=True)>"


def test_webhook_table_name():
    """测试表名"""
    assert Webhook.__tablename__ == "webhooks"


def test_webhook_columns():
    """测试必要列存在"""
    columns = {c.name for c in Webhook.__table__.columns}
    expected = {"id", "user_id", "url", "events", "secret_hash",
                "is_active", "failure_count", "last_triggered_at",
                "created_at", "updated_at"}
    assert expected.issubset(columns)


def test_webhook_column_types():
    """测试列类型正确"""
    table = Webhook.__table__
    # user_id应为外键，指向users.id
    fk = list(table.c.user_id.foreign_keys)[0]
    assert "users" in str(fk)
    # is_active应为布尔类型
    assert table.c.is_active.default.arg is True
    # failure_count应为整型，默认0
    assert table.c.failure_count.default.arg == 0
