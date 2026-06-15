"""Iteration Schema单元测试"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.iteration import IterationCreate, IterationResponse


def test_iteration_create_schema():
    """验证迭代创建Schema的正常创建"""
    iteration_data = {
        "feedback": "需要提高输出质量，请提供更详细的分析",
        "mode": "reexecute"
    }

    iteration = IterationCreate(**iteration_data)

    assert iteration.feedback == "需要提高输出质量，请提供更详细的分析"
    assert iteration.mode == "reexecute"


def test_iteration_create_reexecute_mode():
    """验证重新执行模式的Schema"""
    # 测试 reexecute 模式
    reexecute_data = {
        "feedback": "输出需要完全重新生成",
        "mode": "reexecute"
    }
    iteration_reexecute = IterationCreate(**reexecute_data)
    assert iteration_reexecute.mode == "reexecute"

    # 测试 incremental 模式
    incremental_data = {
        "feedback": "请在此基础上继续改进",
        "mode": "incremental"
    }
    iteration_incremental = IterationCreate(**incremental_data)
    assert iteration_incremental.mode == "incremental"


def test_iteration_response_schema():
    """验证迭代响应Schema"""
    response_data = {
        "id": "iteration-123",
        "execution_id": "execution-456",
        "iteration_number": 2,
        "feedback": "请改进分析的深度",
        "mode": "incremental",
        "status": "completed",
        "refined_output": "改进后的分析结果",
        "tokens_used": 1500,
        "cost_usd": 0.02,
        "error_message": None,
        "created_at": datetime(2026, 6, 8, 10, 30, 0),
        "updated_at": datetime(2026, 6, 8, 10, 32, 0),
        "completed_at": datetime(2026, 6, 8, 10, 32, 0)
    }

    response = IterationResponse(**response_data)

    assert response.id == "iteration-123"
    assert response.execution_id == "execution-456"
    assert response.iteration_number == 2
    assert response.feedback == "请改进分析的深度"
    assert response.mode == "incremental"
    assert response.status == "completed"
    assert response.refined_output == "改进后的分析结果"
    assert response.tokens_used == 1500
    assert response.cost_usd == 0.02
    assert response.error_message is None
    assert response.created_at == datetime(2026, 6, 8, 10, 30, 0)
    assert response.updated_at == datetime(2026, 6, 8, 10, 32, 0)
    assert response.completed_at == datetime(2026, 6, 8, 10, 32, 0)


def test_iteration_create_validation_errors():
    """验证Schema验证错误"""
    # 空反馈验证失败
    with pytest.raises(ValidationError) as exc_info:
        IterationCreate(feedback="", mode="reexecute")
    assert "feedback" in str(exc_info.value)

    # 无效模式验证失败
    with pytest.raises(ValidationError) as exc_info:
        IterationCreate(feedback="有效反馈", mode="invalid_mode")
    assert "mode" in str(exc_info.value)

    # 缺少必填字段验证失败
    with pytest.raises(ValidationError) as exc_info:
        IterationCreate(feedback="有效反馈")
    assert "mode" in str(exc_info.value)


def test_iteration_response_optional_fields():
    """验证可选字段处理"""
    minimal_response = {
        "id": "iteration-789",
        "execution_id": "execution-101",
        "iteration_number": 1,
        "feedback": "初始反馈",
        "mode": "reexecute",
        "status": "pending",
        "created_at": datetime(2026, 6, 8, 9, 0, 0),
        "updated_at": datetime(2026, 6, 8, 9, 0, 0)
    }

    response = IterationResponse(**minimal_response)

    assert response.refined_output is None
    assert response.tokens_used == 0
    assert response.cost_usd == 0.0
    assert response.error_message is None
    assert response.completed_at is None
