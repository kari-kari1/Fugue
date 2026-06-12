"""执行引擎测试"""
import pytest
import asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_execution(client: AsyncClient, test_user: dict, test_crew: dict, test_tasks: list):
    """测试创建执行"""
    response = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["crew_id"] == test_crew["id"]
    assert data["status"] == "pending"
    assert "id" in data
    assert "started_at" in data


@pytest.mark.asyncio
async def test_create_execution_invalid_crew(client: AsyncClient, test_user: dict):
    """测试对不存在的crew创建执行"""
    response = await client.post(
        "/api/v1/executions/",
        json={"crew_id": "nonexistent-crew"},
        headers=test_user["headers"],
    )
    assert response.status_code in [404, 400]


@pytest.mark.asyncio
async def test_create_execution_no_tasks(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试对没有task的crew创建执行"""
    response = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    # 可能成功（进入pending）或失败（没有task）
    assert response.status_code in [201, 400]


@pytest.mark.asyncio
async def test_list_executions(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试列出执行记录"""
    # 创建一个执行
    await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )

    response = await client.get(
        "/api/v1/executions/",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_executions_by_crew(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试按crew列出执行记录"""
    # 创建执行
    await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )

    response = await client.get(
        f"/api/v1/executions/?crew_id={test_crew['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_execution(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试获取执行详情"""
    # 创建执行
    create_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    execution_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/executions/{execution_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == execution_id
    assert "status" in data
    assert "trace" in data


@pytest.mark.asyncio
async def test_get_execution_not_found(client: AsyncClient, test_user: dict):
    """测试获取不存在的执行"""
    response = await client.get(
        "/api/v1/executions/nonexistent-id",
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execution_lifecycle(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试执行完整生命周期：创建 -> 运行 -> 完成"""
    # 创建执行
    create_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert create_resp.status_code == 201
    execution_id = create_resp.json()["id"]

    # 等待执行完成（最多30秒）
    completed = False
    for _ in range(30):
        await asyncio.sleep(1)
        get_resp = await client.get(
            f"/api/v1/executions/{execution_id}",
            headers=test_user["headers"],
        )
        status = get_resp.json()["status"]
        if status not in ["pending", "running"]:
            completed = True
            break

    assert completed, "执行超时"
    data = get_resp.json()
    assert data["status"] == "completed"
    assert data["total_tokens_used"] > 0


@pytest.mark.asyncio
async def test_execution_task_executions(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试获取执行的Task执行记录"""
    # 创建并等待执行完成
    create_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    execution_id = create_resp.json()["id"]

    # 等待完成
    for _ in range(30):
        await asyncio.sleep(1)
        get_resp = await client.get(
            f"/api/v1/executions/{execution_id}",
            headers=test_user["headers"],
        )
        if get_resp.json()["status"] not in ["pending", "running"]:
            break

    # 获取Task执行记录
    response = await client.get(
        f"/api/v1/executions/{execution_id}/task-executions",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(test_tasks)

    # 验证每个Task执行都有输出
    for te in data:
        assert te["status"] == "completed"
        assert te.get("output") is not None


@pytest.mark.asyncio
async def test_execution_trace(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试执行trace记录"""
    # 创建并等待执行完成
    create_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    execution_id = create_resp.json()["id"]

    # 等待完成
    for _ in range(30):
        await asyncio.sleep(1)
        get_resp = await client.get(
            f"/api/v1/executions/{execution_id}",
            headers=test_user["headers"],
        )
        if get_resp.json()["status"] not in ["pending", "running"]:
            break

    data = get_resp.json()
    assert len(data["trace"]) > 0

    # 验证trace结构
    trace = data["trace"][0]
    assert "timestamp" in trace
    assert "event_type" in trace
    assert "data" in trace


@pytest.mark.asyncio
async def test_cancel_execution(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试取消执行"""
    # 创建执行
    create_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    execution_id = create_resp.json()["id"]

    # 等待一小段时间让执行开始
    await asyncio.sleep(0.5)

    # 取消执行
    cancel_resp = await client.post(
        f"/api/v1/executions/{execution_id}/cancel",
        headers=test_user["headers"],
    )
    assert cancel_resp.status_code == 200

    # 等待取消生效
    await asyncio.sleep(2)

    # 验证状态
    get_resp = await client.get(
        f"/api/v1/executions/{execution_id}",
        headers=test_user["headers"],
    )
    status = get_resp.json()["status"]
    assert status in ["cancelled", "completed"]  # 可能已经完成了


@pytest.mark.asyncio
async def test_cancel_nonexistent_execution(client: AsyncClient, test_user: dict):
    """测试取消不存在的执行"""
    response = await client.post(
        "/api/v1/executions/nonexistent-id/cancel",
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_executions(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试并发执行 — 使用不同工作流同时运行"""
    import random

    # 创建3个独立的工作流，每个带相同的agent/task配置
    execution_ids = []
    crews_to_cleanup = []

    for i in range(3):
        # 为每个并发执行创建独立的工作流
        crew_resp = await client.post(
            "/api/v1/crews/",
            json={
                "name": f"并发测试工作流-{i}-{random.randint(1000, 9999)}",
                "description": f"并发执行测试 #{i}",
                "process": "sequential",
                "agents": [
                    {"name": f"并发Agent-{i}", "role": "研究员",
                     "goal": "测试并发执行", "llm_provider": "openai", "llm_model": "gpt-4o",
                     "tools_config": []},
                ],
                "tasks": [
                    {"name": f"并发任务-{i}", "description": "测试任务",
                     "agent_position": 0, "context_task_positions": []},
                ],
            },
            headers=test_user["headers"],
        )
        assert crew_resp.status_code == 201, f"Failed to create crew {i}: {crew_resp.text}"
        crew = crew_resp.json()
        crews_to_cleanup.append(crew["id"])

        resp = await client.post(
            "/api/v1/executions/",
            json={"crew_id": crew["id"]},
            headers=test_user["headers"],
        )
        assert resp.status_code == 201, f"Failed to create execution {i}: {resp.text}"
        execution_ids.append(resp.json()["id"])

    # 等待所有执行完成
    for eid in execution_ids:
        for _ in range(30):
            await asyncio.sleep(1)
            get_resp = await client.get(
                f"/api/v1/executions/{eid}",
                headers=test_user["headers"],
            )
            if get_resp.json()["status"] not in ["pending", "running"]:
                break

    # 验证所有执行都完成了
    for eid in execution_ids:
        get_resp = await client.get(
            f"/api/v1/executions/{eid}",
            headers=test_user["headers"],
        )
        assert get_resp.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_execution_cost_tracking(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试执行成本追踪"""
    # 创建并等待执行完成
    create_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    execution_id = create_resp.json()["id"]

    # 等待完成
    for _ in range(30):
        await asyncio.sleep(1)
        get_resp = await client.get(
            f"/api/v1/executions/{execution_id}",
            headers=test_user["headers"],
        )
        if get_resp.json()["status"] not in ["pending", "running"]:
            break

    data = get_resp.json()
    assert "total_tokens_used" in data
    assert "total_cost_usd" in data
    assert data["total_tokens_used"] > 0
    assert data["total_cost_usd"] >= 0


@pytest.mark.asyncio
async def test_pause_and_checkpoints(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_tasks: list,
):
    """测试暂停请求和检查点查询"""
    import asyncio as _aio

    # 创建执行
    create_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=test_user["headers"],
    )
    assert create_resp.status_code == 201
    execution_id = create_resp.json()["id"]

    # 等待进入运行状态
    await _aio.sleep(2)

    # 发送暂停请求（可能已快速完成，验证请求不抛异常）
    pause_resp = await client.post(
        f"/api/v1/executions/{execution_id}/pause",
        headers=test_user["headers"],
    )
    assert pause_resp.status_code in (200, 400)  # 200=成功暂停, 400=已完成无法暂停

    # 查询检查点（即使执行已完成，也应返回结果）
    cp_resp = await client.get(
        f"/api/v1/executions/{execution_id}/checkpoints",
        headers=test_user["headers"],
    )
    assert cp_resp.status_code == 200
    assert isinstance(cp_resp.json(), list)
