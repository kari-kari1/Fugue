"""ScheduledTask模型测试"""

import pytest
from app.models.scheduled_task import ScheduledTask


def test_scheduled_task_to_dict():
    """测试ScheduledTask序列化"""
    task = ScheduledTask(
        crew_id="test-crew-id",
        cron_expression="0 9 * * *",
        timezone="Asia/Shanghai",
        inputs={"key": "value"},
        is_active=True,
    )
    data = task.to_dict()
    assert data["crew_id"] == "test-crew-id"
    assert data["cron_expression"] == "0 9 * * *"
    assert data["timezone"] == "Asia/Shanghai"
    assert data["inputs"] == {"key": "value"}
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_scheduled_task_to_dict_null_dates():
    """测试ScheduledTask序列化（日期字段为None）"""
    task = ScheduledTask(
        crew_id="test-crew-id",
        cron_expression="0 9 * * *",
    )
    data = task.to_dict()
    assert data["last_run_at"] is None
    assert data["next_run_at"] is None


def test_scheduled_task_repr():
    """测试ScheduledTask字符串表示"""
    task = ScheduledTask(cron_expression="0 9 * * *", is_active=True)
    assert repr(task) == "<ScheduledTask 0 9 * * * (active=True)>"


def test_scheduled_task_table_name():
    """测试表名"""
    assert ScheduledTask.__tablename__ == "scheduled_tasks"


def test_scheduled_task_columns():
    """测试必要列存在"""
    columns = {c.name for c in ScheduledTask.__table__.columns}
    expected = {
        "id", "user_id", "crew_id", "cron_expression", "timezone",
        "inputs", "is_active", "last_run_at", "next_run_at",
        "run_count", "failure_count", "created_at", "updated_at",
    }
    assert expected.issubset(columns)


def test_scheduled_task_column_types():
    """测试列类型正确"""
    table = ScheduledTask.__table__
    # user_id应为外键，指向users.id
    fk_user = list(table.c.user_id.foreign_keys)[0]
    assert "users" in str(fk_user)
    # crew_id应为外键，指向crews.id
    fk_crew = list(table.c.crew_id.foreign_keys)[0]
    assert "crews" in str(fk_crew)
    # is_active应为布尔类型，默认True
    assert table.c.is_active.default.arg is True
    # run_count应为整型，默认0
    assert table.c.run_count.default.arg == 0
    # failure_count应为整型，默认0
    assert table.c.failure_count.default.arg == 0
    # timezone默认UTC
    assert table.c.timezone.default.arg == "UTC"
