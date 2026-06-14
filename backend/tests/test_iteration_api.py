"""迭代API端点测试"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution import Execution, ExecutionStatus
from app.models.user import User


@pytest_asyncio.fixture
async def completed_execution(db_session: AsyncSession, test_user: dict, test_crew: dict) -> Execution:
    """创建一个已标记为completed的execution（直接操作数据库，避免等待引擎）"""
    # 从DB获取用户ID（test_user["id"]可能为None）
    result = await db_session.execute(
        select(User).where(User.email == test_user["email"])
    )
    user = result.scalar_one()

    execution = Execution(
        crew_id=test_crew["id"],
        user_id=user.id,
        status=ExecutionStatus.COMPLETED,
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)
    return execution


@pytest.mark.asyncio
async def test_list_iterations_endpoint(
    client: AsyncClient,
    test_user: dict,
    completed_execution: Execution,
):
    """测试获取迭代列表端点"""
    execution_id = completed_execution.id

    # 初始时迭代列表应为空
    response = await client.get(
        f"/api/v1/executions/{execution_id}/iterations",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

    # 创建一个迭代后再查询
    create_resp = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={"feedback": "第一轮反馈", "mode": "reexecute"},
        headers=test_user["headers"],
    )
    assert create_resp.status_code == 201

    response = await client.get(
        f"/api/v1/executions/{execution_id}/iterations",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["iteration_number"] == 1
    assert data[0]["feedback"] == "第一轮反馈"
    assert data[0]["mode"] == "reexecute"
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_create_iteration_endpoint(
    client: AsyncClient,
    test_user: dict,
    completed_execution: Execution,
):
    """测试创建迭代端点"""
    execution_id = completed_execution.id

    # 创建第一个迭代
    response = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={"feedback": "需要更详细", "mode": "reexecute"},
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["execution_id"] == execution_id
    assert data["iteration_number"] == 1
    assert data["feedback"] == "需要更详细"
    assert data["mode"] == "reexecute"
    assert data["status"] == "pending"
    assert data["tokens_used"] == 0
    assert data["cost_usd"] == 0.0
    assert "id" in data
    assert "created_at" in data

    # 创建第二个迭代，验证iteration_number自增
    response2 = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={"feedback": "继续优化", "mode": "incremental"},
        headers=test_user["headers"],
    )
    assert response2.status_code == 201
    data2 = response2.json()
    assert data2["iteration_number"] == 2
    assert data2["mode"] == "incremental"


@pytest.mark.asyncio
async def test_refine_rejected_when_execution_running(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
):
    """测试running状态的执行不能迭代"""
    # 用直接DB操作创建running状态的execution
    # 这需要通过db_session fixture注入
    # 简化方式：创建一个execution后立即尝试refine
    create_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    execution_id = create_resp.json()["id"]

    # execution处于pending/running状态，应该被拒绝
    response = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={"feedback": "尝试迭代", "mode": "reexecute"},
        headers=test_user["headers"],
    )
    assert response.status_code == 400
    assert "已完成或失败" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_iterations_not_found(client: AsyncClient, test_user: dict):
    """测试对不存在的execution获取迭代列表"""
    response = await client.get(
        "/api/v1/executions/nonexistent-id/iterations",
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_refine_not_found(client: AsyncClient, test_user: dict):
    """测试对不存在的execution创建迭代"""
    response = await client.post(
        "/api/v1/executions/nonexistent-id/refine",
        json={"feedback": "测试", "mode": "reexecute"},
        headers=test_user["headers"],
    )
    assert response.status_code == 404
