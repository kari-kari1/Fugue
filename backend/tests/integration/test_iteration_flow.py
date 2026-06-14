"""迭代流程集成测试

测试完整的迭代流程，包括：
1. 创建完成的execution
2. 调用POST /refine创建迭代
3. 验证迭代被创建
4. 验证迭代状态更新
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution import Execution, ExecutionStatus
from app.models.iteration import Iteration, IterationStatus
from app.models.user import User


@pytest_asyncio.fixture
async def completed_execution_with_tasks(
    db_session: AsyncSession,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
) -> dict:
    """创建一个带有任务的已完成execution"""
    # 获取用户ID
    result = await db_session.execute(
        select(User).where(User.email == test_user["email"])
    )
    user = result.scalar_one()

    execution = Execution(
        crew_id=test_crew["id"],
        user_id=user.id,
        status=ExecutionStatus.COMPLETED,
        results={"output": "原始执行结果", "tokens_used": 100, "cost_usd": 0.02},
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)

    return {
        "execution": execution,
        "execution_id": str(execution.id),
        "crew_id": test_crew["id"],
        "user": user,
    }


@pytest.mark.asyncio
async def test_full_iteration_lifecycle(
    client: AsyncClient,
    test_user: dict,
    completed_execution_with_tasks: dict,
):
    """测试完整的迭代生命周期

    步骤：
    1. 验证初始执行状态
    2. 创建第一个迭代（reexecute模式）
    3. 验证迭代被创建
    4. 创建第二个迭代（incremental模式）
    5. 验证迭代状态和计数
    """
    execution_id = completed_execution_with_tasks["execution_id"]

    # Step 1: 验证execution状态
    response = await client.get(
        f"/api/v1/executions/{execution_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    execution_data = response.json()
    assert execution_data["status"] == ExecutionStatus.COMPLETED.value

    # Step 2: 创建第一个迭代（reexecute模式）
    create_iter1_resp = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={
            "feedback": "需要更详细的研究结果",
            "mode": "reexecute",
        },
        headers=test_user["headers"],
    )
    assert create_iter1_resp.status_code == 201
    iter1_data = create_iter1_resp.json()

    # Step 3: 验证迭代被正确创建
    assert iter1_data["execution_id"] == execution_id
    assert iter1_data["iteration_number"] == 1
    assert iter1_data["feedback"] == "需要更详细的研究结果"
    assert iter1_data["mode"] == "reexecute"
    assert iter1_data["status"] == IterationStatus.PENDING.value
    assert iter1_data["tokens_used"] == 0
    assert iter1_data["cost_usd"] == 0.0
    assert "id" in iter1_data
    assert "created_at" in iter1_data

    iter1_id = iter1_data["id"]

    # Step 4: 验证迭代列表包含这个迭代
    list_resp = await client.get(
        f"/api/v1/executions/{execution_id}/iterations",
        headers=test_user["headers"],
    )
    assert list_resp.status_code == 200
    iterations = list_resp.json()
    assert len(iterations) == 1
    assert iterations[0]["id"] == iter1_id

    # Step 6: 创建第二个迭代（incremental模式）
    create_iter2_resp = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={
            "feedback": "继续改进写作质量",
            "mode": "incremental",
        },
        headers=test_user["headers"],
    )
    assert create_iter2_resp.status_code == 201
    iter2_data = create_iter2_resp.json()

    # Step 7: 验证iteration_number自增
    assert iter2_data["iteration_number"] == 2
    assert iter2_data["mode"] == "incremental"
    assert iter2_data["status"] == IterationStatus.PENDING.value

    # Step 8: 验证迭代列表包含两个迭代
    list_resp2 = await client.get(
        f"/api/v1/executions/{execution_id}/iterations",
        headers=test_user["headers"],
    )
    assert list_resp2.status_code == 200
    iterations2 = list_resp2.json()
    assert len(iterations2) == 2

    # 按iteration_number排序验证
    iter_numbers = [it["iteration_number"] for it in iterations2]
    assert iter_numbers == [1, 2]


@pytest.mark.asyncio
async def test_iteration_status_update_after_processing(
    client: AsyncClient,
    test_user: dict,
    completed_execution_with_tasks: dict,
    db_session: AsyncSession,
):
    """测试迭代处理后状态更新"""
    execution_id = completed_execution_with_tasks["execution_id"]

    # 创建迭代
    create_resp = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={
            "feedback": "更新状态测试",
            "mode": "reexecute",
        },
        headers=test_user["headers"],
    )
    assert create_resp.status_code == 201
    iter_data = create_resp.json()
    iter_id = iter_data["id"]

    # 初始状态应为pending
    assert iter_data["status"] == IterationStatus.PENDING.value

    # 通过直接操作数据库更新迭代状态（模拟处理）
    result = await db_session.execute(
        select(Iteration).where(Iteration.id == iter_id)
    )
    iteration = result.scalar_one()
    iteration.status = IterationStatus.RUNNING
    await db_session.commit()
    await db_session.refresh(iteration)

    # 验证状态更新
    assert iteration.status == IterationStatus.RUNNING

    # 模拟完成处理
    iteration.status = IterationStatus.COMPLETED
    iteration.refined_output = "迭代完成的结果"
    iteration.tokens_used = 150
    iteration.cost_usd = 0.03
    await db_session.commit()
    await db_session.refresh(iteration)

    # 通过迭代列表验证最终状态
    list_resp = await client.get(
        f"/api/v1/executions/{execution_id}/iterations",
        headers=test_user["headers"],
    )
    assert list_resp.status_code == 200
    iterations = list_resp.json()
    assert len(iterations) == 1
    final_data = iterations[0]
    assert final_data["status"] == IterationStatus.COMPLETED.value
    assert final_data["refined_output"] == "迭代完成的结果"
    assert final_data["tokens_used"] == 150
    assert final_data["cost_usd"] == 0.03


@pytest.mark.asyncio
async def test_iteration_modes_support(
    client: AsyncClient,
    test_user: dict,
    completed_execution_with_tasks: dict,
):
    """测试不同的迭代模式"""
    execution_id = completed_execution_with_tasks["execution_id"]

    # 测试reexecute模式
    reexecute_resp = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={"feedback": "完全重新执行", "mode": "reexecute"},
        headers=test_user["headers"],
    )
    assert reexecute_resp.status_code == 201
    assert reexecute_resp.json()["mode"] == "reexecute"

    # 测试incremental模式
    incremental_resp = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={"feedback": "增量优化", "mode": "incremental"},
        headers=test_user["headers"],
    )
    assert incremental_resp.status_code == 201
    assert incremental_resp.json()["mode"] == "incremental"

    # 验证两种模式都被创建
    list_resp = await client.get(
        f"/api/v1/executions/{execution_id}/iterations",
        headers=test_user["headers"],
    )
    assert list_resp.status_code == 200
    iterations = list_resp.json()
    assert len(iterations) == 2
    modes = [it["mode"] for it in iterations]
    assert "reexecute" in modes
    assert "incremental" in modes


@pytest.mark.asyncio
async def test_iteration_with_failed_execution(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    db_session: AsyncSession,
):
    """测试对失败状态的execution创建迭代"""
    # 创建失败的execution
    result = await db_session.execute(
        select(User).where(User.email == test_user["email"])
    )
    user = result.scalar_one()

    execution = Execution(
        crew_id=test_crew["id"],
        user_id=user.id,
        status=ExecutionStatus.FAILED,
        error_log="执行失败",
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)

    execution_id = str(execution.id)

    # 对失败的execution创建迭代应该成功
    response = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={
            "feedback": "失败后重试",
            "mode": "reexecute",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["execution_id"] == execution_id
    assert data["iteration_number"] == 1


@pytest.mark.asyncio
async def test_iteration_cost_tracking(
    client: AsyncClient,
    test_user: dict,
    completed_execution_with_tasks: dict,
    db_session: AsyncSession,
):
    """测试迭代的成本跟踪"""
    execution_id = completed_execution_with_tasks["execution_id"]

    # 创建迭代
    create_resp = await client.post(
        f"/api/v1/executions/{execution_id}/refine",
        json={"feedback": "成本跟踪测试", "mode": "reexecute"},
        headers=test_user["headers"],
    )
    assert create_resp.status_code == 201
    iter_data = create_resp.json()
    iter_id = iter_data["id"]

    # 初始成本应为0
    assert iter_data["tokens_used"] == 0
    assert iter_data["cost_usd"] == 0.0

    # 模拟处理并更新成本
    result = await db_session.execute(
        select(Iteration).where(Iteration.id == iter_id)
    )
    iteration = result.scalar_one()
    iteration.tokens_used = 500
    iteration.cost_usd = 0.10
    await db_session.commit()
    await db_session.refresh(iteration)

    # 通过迭代列表验证成本被正确跟踪
    list_resp = await client.get(
        f"/api/v1/executions/{execution_id}/iterations",
        headers=test_user["headers"],
    )
    assert list_resp.status_code == 200
    iterations = list_resp.json()
    assert len(iterations) == 1
    data = iterations[0]
    assert data["tokens_used"] == 500
    assert data["cost_usd"] == 0.10
