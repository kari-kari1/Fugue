"""Iteration模型测试"""

import pytest
from app.models.iteration import Iteration, IterationMode, IterationStatus


def test_iteration_creation():
    """测试迭代记录创建"""
    iteration = Iteration(
        execution_id="test-execution-id",
        iteration_number=1,
        feedback="Need to improve the output quality",
        mode=IterationMode.REEXECUTE,
        original_task_snapshot={"task_id": "123", "prompt": "test"},
        previous_output="Initial output",
        refined_output=None,
        tokens_used=100,
        cost_usd=0.001,
    )

    assert iteration.execution_id == "test-execution-id"
    assert iteration.iteration_number == 1
    assert iteration.feedback == "Need to improve the output quality"
    assert iteration.mode == IterationMode.REEXECUTE
    # Note: status defaults are now applied at Python object level via __init__
    # When creating directly without specifying status, it will default to PENDING
    assert iteration.status == IterationStatus.PENDING
    assert iteration.original_task_snapshot == {"task_id": "123", "prompt": "test"}
    assert iteration.previous_output == "Initial output"
    assert iteration.refined_output is None
    assert iteration.tokens_used == 100
    assert iteration.cost_usd == 0.001
    assert iteration.error_message is None
    assert iteration.completed_at is None


def test_iteration_modes():
    """验证迭代模式枚举"""
    assert IterationMode.REEXECUTE.value == "reexecute"
    assert IterationMode.INCREMENTAL.value == "incremental"
    assert IterationMode.REEXECUTE.name == "REEXECUTE"
    assert IterationMode.INCREMENTAL.name == "INCREMENTAL"


def test_iteration_statuses():
    """验证迭代状态枚举"""
    assert IterationStatus.PENDING.value == "pending"
    assert IterationStatus.RUNNING.value == "running"
    assert IterationStatus.COMPLETED.value == "completed"
    assert IterationStatus.FAILED.value == "failed"
    assert IterationStatus.PENDING.name == "PENDING"
    assert IterationStatus.RUNNING.name == "RUNNING"
    assert IterationStatus.COMPLETED.name == "COMPLETED"
    assert IterationStatus.FAILED.name == "FAILED"


def test_iteration_table_name():
    """测试表名"""
    assert Iteration.__tablename__ == "iterations"


def test_iteration_columns():
    """测试必要列存在"""
    columns = {c.name for c in Iteration.__table__.columns}
    expected = {
        "id", "execution_id", "iteration_number", "feedback", "mode", "status",
        "original_task_snapshot", "previous_output", "refined_output",
        "tokens_used", "cost_usd", "error_message", "completed_at",
        "created_at", "updated_at",
    }
    assert expected.issubset(columns)


def test_iteration_column_types():
    """测试列类型正确"""
    table = Iteration.__table__
    # execution_id应为外键，指向executions.id
    fk = list(table.c.execution_id.foreign_keys)[0]
    assert "executions" in str(fk)
    # tokens_used应为整型，默认0
    assert table.c.tokens_used.default.arg == 0
    # cost_usd应为浮点类型，默认0.0
    assert table.c.cost_usd.default.arg == 0.0
    # status默认PENDING
    assert table.c.status.default.arg == IterationStatus.PENDING


def test_iteration_repr():
    """测试Iteration字符串表示"""
    iteration = Iteration(
        execution_id="test-id",
        iteration_number=1,
        feedback="test",
        mode=IterationMode.REEXECUTE,
        status=IterationStatus.COMPLETED,
    )
    assert repr(iteration) == "<Iteration #1 (completed)>"


def test_iteration_to_dict():
    """测试Iteration序列化"""
    iteration = Iteration(
        execution_id="test-execution-id",
        iteration_number=1,
        feedback="Need to improve output",
        mode=IterationMode.REEXECUTE,
        original_task_snapshot={"key": "value"},
        tokens_used=100,
        cost_usd=0.001,
    )
    data = iteration.to_dict()
    assert data["execution_id"] == "test-execution-id"
    assert data["iteration_number"] == 1
    assert data["feedback"] == "Need to improve output"
    assert data["mode"] == "reexecute"
    assert data["original_task_snapshot"] == {"key": "value"}
    assert data["tokens_used"] == 100
    assert data["cost_usd"] == 0.001
    assert "id" in data
    assert "created_at" in data
