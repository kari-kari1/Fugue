"""工作流（Crew）CRUD测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_crew(client: AsyncClient, test_user: dict):
    """测试创建工作流"""
    response = await client.post(
        "/api/v1/crews/",
        json={
            "name": "测试工作流",
            "description": "这是一个测试工作流",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试工作流"
    assert data["description"] == "这是一个测试工作流"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_crew_minimal(client: AsyncClient, test_user: dict):
    """测试创建最小化工作流（只提供name）"""
    response = await client.post(
        "/api/v1/crews/",
        json={"name": "最小工作流"},
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "最小工作流"


@pytest.mark.asyncio
async def test_create_crew_empty_name(client: AsyncClient, test_user: dict):
    """测试空名称被拒绝"""
    response = await client.post(
        "/api/v1/crews/",
        json={"name": ""},
        headers=test_user["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_crew_no_auth(client: AsyncClient):
    """测试未认证创建工作流被拒绝"""
    response = await client.post(
        "/api/v1/crews/",
        json={"name": "未认证"},
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_crews(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试列出工作流"""
    response = await client.get(
        "/api/v1/crews/",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # 检查包含我们创建的工作流
    crew_ids = [c["id"] for c in data]
    assert test_crew["id"] in crew_ids


@pytest.mark.asyncio
async def test_list_crews_empty(client: AsyncClient, test_user: dict):
    """测试空列表"""
    response = await client.get(
        "/api/v1/crews/",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_crew(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试获取工作流详情"""
    response = await client.get(
        f"/api/v1/crews/{test_crew['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_crew["id"]
    assert data["name"] == test_crew["name"]
    assert "agents" in data
    assert "tasks" in data


@pytest.mark.asyncio
async def test_get_crew_not_found(client: AsyncClient, test_user: dict):
    """测试获取不存在的工作流"""
    response = await client.get(
        "/api/v1/crews/nonexistent-id",
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_crew(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试更新工作流"""
    response = await client.put(
        f"/api/v1/crews/{test_crew['id']}",
        json={
            "name": "更新后的工作流",
            "description": "更新后的描述",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后的工作流"
    assert data["description"] == "更新后的描述"


@pytest.mark.asyncio
async def test_update_crew_partial(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试部分更新工作流"""
    response = await client.put(
        f"/api/v1/crews/{test_crew['id']}",
        json={"name": "只更新名称"},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "只更新名称"


@pytest.mark.asyncio
async def test_update_crew_not_found(client: AsyncClient, test_user: dict):
    """测试更新不存在的工作流"""
    response = await client.put(
        "/api/v1/crews/nonexistent-id",
        json={"name": "更新"},
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_crew(client: AsyncClient, test_user: dict):
    """测试删除工作流"""
    # 先创建一个
    create_resp = await client.post(
        "/api/v1/crews/",
        json={"name": "待删除"},
        headers=test_user["headers"],
    )
    crew_id = create_resp.json()["id"]

    # 删除
    response = await client.delete(
        f"/api/v1/crews/{crew_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200

    # 验证已删除
    get_resp = await client.get(
        f"/api/v1/crews/{crew_id}",
        headers=test_user["headers"],
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_crew_not_found(client: AsyncClient, test_user: dict):
    """测试删除不存在的工作流"""
    response = await client.delete(
        "/api/v1/crews/nonexistent-id",
        headers=test_user["headers"],
    )
    assert response.status_code in [404, 200]  # 幂等删除


@pytest.mark.asyncio
async def test_crew_cascade_delete(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
    test_tasks: list,
):
    """测试级联删除（删除crew时删除关联的agents和tasks）"""
    crew_id = test_crew["id"]

    # 删除工作流
    response = await client.delete(
        f"/api/v1/crews/{crew_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200

    # 验证agents被删除
    response = await client.get(
        f"/api/v1/agents/crew/{crew_id}",
        headers=test_user["headers"],
    )
    assert response.status_code in [404, 200]
    if response.status_code == 200:
        assert len(response.json()) == 0

    # 验证tasks被删除
    response = await client.get(
        f"/api/v1/tasks/crew/{crew_id}",
        headers=test_user["headers"],
    )
    assert response.status_code in [404, 200]
    if response.status_code == 200:
        assert len(response.json()) == 0
