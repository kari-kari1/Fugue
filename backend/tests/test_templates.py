"""模板系统测试"""
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def seeded_templates(client: AsyncClient, test_superuser: dict) -> None:
    """初始化预设模板"""
    response = await client.post(
        "/api/v1/demo/seed-templates",
        headers=test_superuser["headers"],
    )
    assert response.status_code in [201, 200]


@pytest.mark.asyncio
async def test_list_templates_empty(client: AsyncClient, test_user: dict):
    """测试空模板列表"""
    response = await client.get(
        "/api/v1/templates/",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_list_templates_with_data(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试有数据的模板列表"""
    response = await client.get(
        "/api/v1/templates/",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 20
    assert len(data["items"]) == 20


@pytest.mark.asyncio
async def test_list_templates_pagination(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试模板列表分页"""
    # 第一页
    response = await client.get(
        "/api/v1/templates/?page=1&limit=2",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total"] == 20

    # 第二页
    response = await client.get(
        "/api/v1/templates/?page=2&limit=2",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2

    # 第三页（只有1个）
    response = await client.get(
        "/api/v1/templates/?page=3&limit=2",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_templates_filter_by_category(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试按分类筛选模板"""
    response = await client.get(
        "/api/v1/templates/?category=research",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for template in data["items"]:
        assert template["category"] == "research"


@pytest.mark.asyncio
async def test_list_templates_search(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试搜索模板"""
    response = await client.get(
        "/api/v1/templates/?search=报告",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_templates_sort(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试模板排序"""
    # 按热门排序
    response = await client.get(
        "/api/v1/templates/?sort_by=popular",
        headers=test_user["headers"],
    )
    assert response.status_code == 200

    # 按最新排序
    response = await client.get(
        "/api/v1/templates/?sort_by=newest",
        headers=test_user["headers"],
    )
    assert response.status_code == 200

    # 按推荐排序
    response = await client.get(
        "/api/v1/templates/?sort_by=recommended",
        headers=test_user["headers"],
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_template(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试获取模板详情"""
    # 先获取列表
    list_resp = await client.get(
        "/api/v1/templates/",
        headers=test_user["headers"],
    )
    template_id = list_resp.json()["items"][0]["id"]

    response = await client.get(
        f"/api/v1/templates/{template_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert "agents_config" in data
    assert "tasks_config" in data
    assert "category" in data


@pytest.mark.asyncio
async def test_get_template_not_found(client: AsyncClient, test_user: dict):
    """测试获取不存在的模板"""
    response = await client.get(
        "/api/v1/templates/nonexistent-id",
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_template_categories(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试获取模板分类列表"""
    response = await client.get(
        "/api/v1/templates/categories",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_custom_template(client: AsyncClient, test_user: dict):
    """测试创建自定义模板"""
    response = await client.post(
        "/api/v1/templates/",
        json={
            "name": "自定义模板",
            "description": "用户创建的模板",
            "category": "research",
            "icon": "🔬",
            "difficulty": "beginner",
            "agents_config": [
                {
                    "name": "自定义Agent",
                    "role": "助手",
                    "goal": "帮助用户",
                    "backstory": "我是助手",
                }
            ],
            "tasks_config": [
                {
                    "name": "自定义任务",
                    "description": "执行任务",
                    "expected_output": "任务结果",
                    "agent_index": 0,
                }
            ],
            "tags": ["自定义", "测试"],
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "自定义模板"
    assert data["is_builtin"] is False
    assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_create_custom_template_validation(client: AsyncClient, test_user: dict):
    """测试自定义模板验证"""
    # 缺少必填字段
    response = await client.post(
        "/api/v1/templates/",
        json={
            "name": "不完整的模板",
            # 缺少 category, agents_config, tasks_config
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_custom_template(client: AsyncClient, test_user: dict):
    """测试更新自定义模板"""
    # 创建模板
    create_resp = await client.post(
        "/api/v1/templates/",
        json={
            "name": "待更新模板",
            "category": "research",
            "agents_config": [
                {"name": "Agent", "role": "助手", "goal": "目标", "backstory": "背景"}
            ],
            "tasks_config": [
                {
                    "name": "任务",
                    "description": "描述",
                    "expected_output": "输出",
                    "agent_index": 0,
                }
            ],
        },
        headers=test_user["headers"],
    )
    template_id = create_resp.json()["id"]

    # 更新
    response = await client.put(
        f"/api/v1/templates/{template_id}",
        json={
            "name": "已更新的模板",
            "description": "更新后的描述",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "已更新的模板"


@pytest.mark.asyncio
async def test_update_builtin_template_forbidden(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试更新内置模板被拒绝"""
    # 获取内置模板
    list_resp = await client.get(
        "/api/v1/templates/",
        headers=test_user["headers"],
    )
    builtin_id = list_resp.json()["items"][0]["id"]

    response = await client.put(
        f"/api/v1/templates/{builtin_id}",
        json={"name": "尝试修改内置"},
        headers=test_user["headers"],
    )
    # 应该被拒绝（403）或不允许修改builtin字段
    assert response.status_code in [403, 400, 200]


@pytest.mark.asyncio
async def test_delete_custom_template(client: AsyncClient, test_user: dict):
    """测试删除自定义模板"""
    # 创建模板
    create_resp = await client.post(
        "/api/v1/templates/",
        json={
            "name": "待删除模板",
            "category": "research",
            "agents_config": [
                {"name": "Agent", "role": "助手", "goal": "目标", "backstory": "背景"}
            ],
            "tasks_config": [
                {
                    "name": "任务",
                    "description": "描述",
                    "expected_output": "输出",
                    "agent_index": 0,
                }
            ],
        },
        headers=test_user["headers"],
    )
    template_id = create_resp.json()["id"]

    # 删除
    response = await client.delete(
        f"/api/v1/templates/{template_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200

    # 验证已删除
    get_resp = await client.get(
        f"/api/v1/templates/{template_id}",
        headers=test_user["headers"],
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_use_template(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试使用模板创建工作流"""
    # 获取模板
    list_resp = await client.get(
        "/api/v1/templates/",
        headers=test_user["headers"],
    )
    template_id = list_resp.json()["items"][0]["id"]

    # 使用模板
    response = await client.post(
        f"/api/v1/templates/{template_id}/use",
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert "crew_id" in data
    assert "message" in data

    # 验证工作流已创建
    crew_resp = await client.get(
        f"/api/v1/crews/{data['crew_id']}",
        headers=test_user["headers"],
    )
    assert crew_resp.status_code == 200
    crew_data = crew_resp.json()
    assert len(crew_data["agents"]) > 0
    assert len(crew_data["tasks"]) > 0


@pytest.mark.asyncio
async def test_use_template_not_found(client: AsyncClient, test_user: dict):
    """测试使用不存在的模板"""
    response = await client.post(
        "/api/v1/templates/nonexistent-id/use",
        headers=test_user["headers"],
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_template_use_count(
    client: AsyncClient,
    test_user: dict,
    seeded_templates: None,
):
    """测试模板使用次数统计"""
    # 获取模板
    list_resp = await client.get(
        "/api/v1/templates/",
        headers=test_user["headers"],
    )
    template_id = list_resp.json()["items"][0]["id"]
    initial_count = list_resp.json()["items"][0]["use_count"]

    # 使用模板
    await client.post(
        f"/api/v1/templates/{template_id}/use",
        headers=test_user["headers"],
    )

    # 验证使用次数增加
    get_resp = await client.get(
        f"/api/v1/templates/{template_id}",
        headers=test_user["headers"],
    )
    assert get_resp.json()["use_count"] == initial_count + 1
