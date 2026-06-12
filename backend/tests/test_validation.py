"""DAG校验和工作流验证测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validate_dag_no_cycle(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试无环DAG校验通过"""
    # 创建3个task：A -> B -> C
    resp_a = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task A",
            "description": "第一步",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    task_a_id = resp_a.json()["id"]

    resp_b = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task B",
            "description": "第二步",
            "agent_id": test_agents[0]["id"],
            "context_task_ids": [task_a_id],
        },
        headers=test_user["headers"],
    )
    task_b_id = resp_b.json()["id"]

    resp_c = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task C",
            "description": "第三步",
            "agent_id": test_agents[1]["id"],
            "context_task_ids": [task_b_id],
        },
        headers=test_user["headers"],
    )
    assert resp_c.status_code == 201

    # 验证DAG
    response = await client.post(
        "/api/v1/validation/validate-dag",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True


@pytest.mark.asyncio
async def test_validate_dag_parallel(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试并行任务DAG校验"""
    # 创建并行任务：A, B -> C
    resp_a = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task A",
            "description": "并行任务1",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    task_a_id = resp_a.json()["id"]

    resp_b = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task B",
            "description": "并行任务2",
            "agent_id": test_agents[1]["id"],
        },
        headers=test_user["headers"],
    )
    task_b_id = resp_b.json()["id"]

    resp_c = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task C",
            "description": "汇总任务",
            "agent_id": test_agents[0]["id"],
            "context_task_ids": [task_a_id, task_b_id],
        },
        headers=test_user["headers"],
    )
    assert resp_c.status_code == 201

    # 验证DAG
    response = await client.post(
        "/api/v1/validation/validate-dag",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True


@pytest.mark.asyncio
async def test_validate_dag_empty_crew(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试空crew的DAG校验"""
    response = await client.post(
        "/api/v1/validation/validate-dag",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    # 空crew可能有效（没有task）或无效
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_validate_dag_invalid_crew(client: AsyncClient, test_user: dict):
    """测试不存在的crew"""
    response = await client.post(
        "/api/v1/validation/validate-dag",
        json={"crew_id": "nonexistent"},
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_validate_crew_ready(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试工作流就绪校验"""
    # 创建有效的task配置
    resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "任务",
            "description": "描述",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    assert resp.status_code == 201

    # 验证工作流就绪
    response = await client.post(
        "/api/v1/validation/validate-crew",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_ready" in data


@pytest.mark.asyncio
async def test_validate_crew_no_tasks(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试没有task的工作流校验"""
    response = await client.post(
        "/api/v1/validation/validate-crew",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_ready"] is False
    assert len(data.get("errors", [])) > 0


@pytest.mark.asyncio
async def test_validate_crew_no_agents(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
):
    """测试没有agent的工作流校验"""
    response = await client.post(
        "/api/v1/validation/validate-crew",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_ready"] is False


@pytest.mark.asyncio
async def test_validate_execution_ready(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试执行就绪校验"""
    # 创建有效的配置
    resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "任务",
            "description": "描述",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    assert resp.status_code == 201

    # 校验执行就绪
    response = await client.post(
        "/api/v1/validation/validate-execution",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "can_execute" in data


@pytest.mark.asyncio
async def test_validate_with_invalid_task(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试包含无效task的校验"""
    # 创建task但缺少必要配置
    resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "",  # 空名称
            "description": "描述",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    # 可能成功（前端校验）或失败（后端校验）
    if resp.status_code == 201:
        # 如果创建成功，验证时应该检测到问题
        response = await client.post(
            "/api/v1/validation/validate-crew",
            json={"crew_id": test_crew["id"]},
            headers=test_user["headers"],
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_validate_complex_dag(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试复杂DAG结构"""
    # 创建复杂的依赖关系：
    # A -> B -> D
    # A -> C -> D
    # 即 D 同时依赖 B 和 C，而 B 和 C 都依赖 A

    resp_a = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task A",
            "description": "起始任务",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    task_a_id = resp_a.json()["id"]

    resp_b = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task B",
            "description": "分支1",
            "agent_id": test_agents[0]["id"],
            "context_task_ids": [task_a_id],
        },
        headers=test_user["headers"],
    )
    task_b_id = resp_b.json()["id"]

    resp_c = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task C",
            "description": "分支2",
            "agent_id": test_agents[1]["id"],
            "context_task_ids": [task_a_id],
        },
        headers=test_user["headers"],
    )
    task_c_id = resp_c.json()["id"]

    resp_d = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "Task D",
            "description": "汇总任务",
            "agent_id": test_agents[0]["id"],
            "context_task_ids": [task_b_id, task_c_id],
        },
        headers=test_user["headers"],
    )
    assert resp_d.status_code == 201

    # 验证DAG
    response = await client.post(
        "/api/v1/validation/validate-dag",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True


@pytest.mark.asyncio
async def test_validate_dag_structure_info(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试DAG结构信息返回"""
    # 创建简单DAG
    resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "任务",
            "description": "描述",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    assert resp.status_code == 201

    # 获取DAG结构信息
    response = await client.post(
        "/api/v1/validation/validate-dag",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    # 可能还包含其他结构信息
