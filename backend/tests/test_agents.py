"""Agent CRUD测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试创建Agent"""
    response = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": test_crew["id"],
            "name": "研究员",
            "role": "研究",
            "goal": "收集数据",
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "研究员"
    assert data["role"] == "研究"
    assert data["crew_id"] == test_crew["id"]


@pytest.mark.asyncio
async def test_create_agent_minimal(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试创建最小化Agent"""
    response = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": test_crew["id"],
            "name": "最小Agent",
            "role": "助手",
            "goal": "帮助用户",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_agent_invalid_crew(client: AsyncClient, test_user: dict):
    """测试在不存在的crew下创建Agent"""
    response = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": "nonexistent-crew-id",
            "name": "测试Agent",
            "role": "测试",
            "goal": "测试目标",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_agent_missing_fields(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试缺少必填字段"""
    response = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": test_crew["id"],
            # 缺少name, role, goal
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_agents_by_crew(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
):
    """测试按crew列出Agent"""
    response = await client.get(
        f"/api/v1/agents/crew/{test_crew['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(test_agents)


@pytest.mark.asyncio
async def test_list_agents_empty_crew(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试空crew的Agent列表"""
    response = await client.get(
        f"/api/v1/agents/crew/{test_crew['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient, test_user: dict, test_agents: list):
    """测试获取Agent详情"""
    agent = test_agents[0]
    response = await client.get(
        f"/api/v1/agents/{agent['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent["id"]
    assert data["name"] == agent["name"]


@pytest.mark.asyncio
async def test_get_agent_not_found(client: AsyncClient, test_user: dict):
    """测试获取不存在的Agent"""
    response = await client.get(
        "/api/v1/agents/nonexistent-id",
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient, test_user: dict, test_agents: list):
    """测试更新Agent"""
    agent = test_agents[0]
    response = await client.put(
        f"/api/v1/agents/{agent['id']}",
        json={
            "name": "高级研究员",
            "goal": "深度研究",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "高级研究员"
    assert data["goal"] == "深度研究"


@pytest.mark.asyncio
async def test_update_agent_not_found(client: AsyncClient, test_user: dict):
    """测试更新不存在的Agent"""
    response = await client.put(
        "/api/v1/agents/nonexistent-id",
        json={"name": "更新"},
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient, test_user: dict, test_agents: list):
    """测试删除Agent"""
    agent = test_agents[0]
    response = await client.delete(
        f"/api/v1/agents/{agent['id']}",
        headers=test_user["headers"],
    )
    assert response.status_code in [200, 204]  # 200 or 204 No Content

    # 验证已删除
    get_resp = await client.get(
        f"/api/v1/agents/{agent['id']}",
        headers=test_user["headers"],
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent_not_found(client: AsyncClient, test_user: dict):
    """测试删除不存在的Agent"""
    response = await client.delete(
        "/api/v1/agents/nonexistent-id",
        headers=test_user["headers"],
    )
    assert response.status_code in [404, 200]


@pytest.mark.asyncio
async def test_agent_with_tools(client: AsyncClient, test_user: dict, test_crew: dict):
    """测试创建带工具的Agent"""
    response = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": test_crew["id"],
            "name": "工具Agent",
            "role": "执行者",
            "goal": "使用工具完成任务",
            "tools_config": ["web_search", "file_read"],
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert "tools_config" in data
    assert len(data["tools_config"]) == 2
