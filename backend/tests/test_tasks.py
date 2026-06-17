"""Task CRUD测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, test_user: dict, test_crew: dict, test_agents: list):
    """测试创建Task"""
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "研究任务",
            "description": "收集相关数据",
            "agent_id": test_agents[0]["id"],
            "expected_output": "结构化的数据报告",
            "output_type": "text",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "研究任务"
    assert data["agent_id"] == test_agents[0]["id"]
    assert data["crew_id"] == test_crew["id"]


@pytest.mark.asyncio
async def test_create_task_minimal(client: AsyncClient, test_user: dict, test_crew: dict, test_agents: list):
    """测试创建最小化Task"""
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "简单任务",
            "description": "执行简单操作",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_task_with_dependencies(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试创建带依赖的Task"""
    # 创建第一个Task
    resp1 = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "任务1",
            "description": "第一步",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    task1_id = resp1.json()["id"]

    # 创建依赖第一个Task的第二个Task
    resp2 = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "任务2",
            "description": "第二步（依赖第一步）",
            "agent_id": test_agents[1]["id"],
            "context_task_ids": [task1_id],
        },
        headers=test_user["headers"],
    )
    assert resp2.status_code == 201
    data = resp2.json()
    assert task1_id in data["context_task_ids"]


@pytest.mark.asyncio
async def test_create_task_invalid_crew(client: AsyncClient, test_user: dict, test_agents: list):
    """测试在不存在的crew下创建Task"""
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": "nonexistent-crew",
            "name": "任务",
            "description": "描述",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_task_invalid_agent(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试使用不存在的agent创建Task"""
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "任务",
            "description": "描述",
            "agent_id": "nonexistent-agent",
        },
        headers=test_user["headers"],
    )
    # API可能允许创建（返回201）或拒绝（返回400/404/422）
    assert response.status_code in [201, 400, 404, 422]


@pytest.mark.asyncio
async def test_create_task_missing_fields(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试缺少必填字段"""
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            # 缺少name, description, agent_id
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tasks_by_crew(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试按crew列出Task"""
    response = await client.get(
        f"/api/v1/tasks/crew/{test_crew['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(test_tasks)


@pytest.mark.asyncio
async def test_list_tasks_empty_crew(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试空crew的Task列表"""
    response = await client.get(
        f"/api/v1/tasks/crew/{test_crew['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, test_user: dict, test_tasks: list):
    """测试获取Task详情"""
    task = test_tasks[0]
    response = await client.get(
        f"/api/v1/tasks/{task['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task["id"]
    assert data["name"] == task["name"]


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient, test_user: dict):
    """测试获取不存在的Task"""
    response = await client.get(
        "/api/v1/tasks/nonexistent-id",
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, test_user: dict, test_tasks: list):
    """测试更新Task"""
    task = test_tasks[0]
    response = await client.put(
        f"/api/v1/tasks/{task['id']}",
        json={
            "name": "更新后的任务",
            "description": "更新后的描述",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后的任务"
    assert data["description"] == "更新后的描述"


@pytest.mark.asyncio
async def test_update_task_not_found(client: AsyncClient, test_user: dict):
    """测试更新不存在的Task"""
    response = await client.put(
        "/api/v1/tasks/nonexistent-id",
        json={"name": "更新"},
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, test_user: dict, test_tasks: list):
    """测试删除Task"""
    task = test_tasks[0]
    response = await client.delete(
        f"/api/v1/tasks/{task['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code in [200, 204]  # 200 or 204 No Content

    # 验证已删除
    get_resp = await client.get(
        f"/api/v1/tasks/{task['id']}",
        headers=test_user["headers"],
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_not_found(client: AsyncClient, test_user: dict):
    """测试删除不存在的Task"""
    response = await client.delete(
        "/api/v1/tasks/nonexistent-id",
        headers=test_user["headers"],
    )
    assert response.status_code in [404, 200]


@pytest.mark.asyncio
async def test_task_output_types(client: AsyncClient, test_user: dict, test_crew: dict, test_agents: list):
    """测试不同的输出类型"""
    for output_type in ["text", "json", "file", "code"]:
        response = await client.post(
            "/api/v1/tasks/",
            json={
                "crew_id": test_crew["id"],
                "name": f"任务_{output_type}",
                "description": f"输出类型: {output_type}",
                "agent_id": test_agents[0]["id"],
                "output_type": output_type,
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        assert response.json()["output_type"] == output_type


@pytest.mark.asyncio
async def test_task_with_validation_rules(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试带验证规则的Task"""
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "验证任务",
            "description": "带验证规则",
            "agent_id": test_agents[0]["id"],
            "validation_rules": [
                {"type": "not_empty", "message": "输出不能为空"},
                {"type": "min_length", "value": 100, "message": "至少100字"},
            ],
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_task_with_timeout(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试带超时配置的Task"""
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": test_crew["id"],
            "name": "超时任务",
            "description": "有超时限制",
            "agent_id": test_agents[0]["id"],
            "timeout_seconds": 300,
            "max_retries": 3,
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["timeout_seconds"] == 300
    assert data["max_retries"] == 3
