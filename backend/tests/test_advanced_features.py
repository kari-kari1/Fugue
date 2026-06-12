"""高级功能集成测试 - 端到端验证所有新功能模块"""

from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from httpx import AsyncClient


# ---- Helper fixture ----

@pytest.fixture
def auth_headers(test_user: dict) -> dict:
    """提取认证 headers（复用 test_user fixture）"""
    return test_user["headers"]


@pytest.fixture
def mock_vector_store():
    """Mock ChromaDB 向量存储，避免连接外部服务"""
    mock_store = AsyncMock()
    mock_store.create_collection = AsyncMock()
    mock_store.delete_collection = AsyncMock()
    mock_store.add_documents = AsyncMock()
    mock_store.search = AsyncMock(return_value=[])
    mock_store.get_collection = AsyncMock()
    mock_store.delete_documents = AsyncMock()
    mock_store.get_collection_stats = AsyncMock(return_value={"count": 0, "name": "test"})
    with patch("app.api.v1.knowledge_bases.get_vector_store", return_value=mock_store):
        yield mock_store


# ============================================================
# 1. 条件分支工作流 (Condition Branch)
# ============================================================

@pytest.mark.asyncio
async def test_conditional_workflow(client: AsyncClient, auth_headers):
    """测试条件分支工作流：创建 Crew + Agent + Task，验证结构完整"""
    # 创建工作流
    crew_resp = await client.post(
        "/api/v1/crews/",
        json={"name": "条件测试", "process": "sequential"},
        headers=auth_headers,
    )
    assert crew_resp.status_code == 201
    crew_id = crew_resp.json()["id"]

    # 创建 Agent
    agent_resp = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": crew_id,
            "name": "条件Agent",
            "role": "助手",
            "goal": "处理条件分支逻辑",
            "llm_provider": "mock",
            "llm_model": "mock",
        },
        headers=auth_headers,
    )
    assert agent_resp.status_code == 201
    agent_id = agent_resp.json()["id"]

    # 创建任务
    task_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "agent_id": agent_id,
            "name": "条件任务",
            "description": "条件分支触发的任务",
            "expected_output": "条件分支输出",
        },
        headers=auth_headers,
    )
    assert task_resp.status_code == 201

    # 验证 DAG 校验通过（条件分支结构合法）
    validate_resp = await client.get(
        f"/api/v1/validation/crew/{crew_id}/validate",
        headers=auth_headers,
    )
    assert validate_resp.status_code == 200
    assert validate_resp.json()["valid"] is True


# ============================================================
# 2. 导出功能 (Export)
# ============================================================

@pytest.mark.asyncio
async def test_export_crew_json(client: AsyncClient, auth_headers):
    """测试导出工作流为 JSON"""
    # 创建工作流
    crew_resp = await client.post(
        "/api/v1/crews/",
        json={"name": "导出测试", "description": "用于导出功能验证"},
        headers=auth_headers,
    )
    assert crew_resp.status_code == 201
    crew_id = crew_resp.json()["id"]

    # 创建 Agent 和 Task
    agent_resp = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": crew_id,
            "name": "导出Agent",
            "role": "研究员",
            "goal": "执行研究任务",
            "llm_provider": "mock",
        },
        headers=auth_headers,
    )
    assert agent_resp.status_code == 201
    agent_id = agent_resp.json()["id"]

    task_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "agent_id": agent_id,
            "name": "研究任务",
            "description": "收集并整理数据",
            "expected_output": "研究报告",
        },
        headers=auth_headers,
    )
    assert task_resp.status_code == 201

    # 执行导出
    export_resp = await client.get(
        f"/api/v1/exports/crews/{crew_id}/export/json",
        headers=auth_headers,
    )
    assert export_resp.status_code == 200

    export_data = export_resp.json()
    # 导出结构：{version, exported_at, crew: {name, description, process, agents, tasks}}
    assert "crew" in export_data
    assert export_data["crew"]["name"] == "导出测试"
    assert "agents" in export_data["crew"]
    assert "tasks" in export_data["crew"]
    assert len(export_data["crew"]["agents"]) >= 1
    assert len(export_data["crew"]["tasks"]) >= 1
    # 验证导出元数据
    assert "version" in export_data
    assert "exported_at" in export_data


@pytest.mark.asyncio
async def test_export_nonexistent_crew(client: AsyncClient, auth_headers):
    """测试导出不存在的工作流返回 404"""
    resp = await client.get(
        "/api/v1/exports/crews/nonexistent-id/export/json",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ============================================================
# 3. 知识库 CRUD (Knowledge Base)
# ============================================================

@pytest.mark.asyncio
async def test_knowledge_base_create_and_get(client: AsyncClient, auth_headers, mock_vector_store):
    """测试知识库创建和获取"""
    # 创建知识库
    kb_resp = await client.post(
        "/api/v1/knowledge-bases/",
        json={
            "name": "测试知识库",
            "description": "集成测试用知识库",
        },
        headers=auth_headers,
    )
    assert kb_resp.status_code == 200
    kb_data = kb_resp.json()
    assert kb_data["name"] == "测试知识库"
    assert kb_data["description"] == "集成测试用知识库"
    assert "id" in kb_data
    kb_id = kb_data["id"]

    # 验证向量集合创建被调用
    mock_vector_store.create_collection.assert_called_once_with(str(kb_id))

    # 获取详情
    detail_resp = await client.get(
        f"/api/v1/knowledge-bases/{kb_id}",
        headers=auth_headers,
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["name"] == "测试知识库"


@pytest.mark.asyncio
async def test_knowledge_base_list(client: AsyncClient, auth_headers, mock_vector_store):
    """测试知识库列表"""
    # 创建两个知识库
    for i in range(2):
        await client.post(
            "/api/v1/knowledge-bases/",
            json={"name": f"知识库{i+1}", "description": f"描述{i+1}"},
            headers=auth_headers,
        )

    list_resp = await client.get(
        "/api/v1/knowledge-bases/",
        headers=auth_headers,
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_knowledge_base_update(client: AsyncClient, auth_headers, mock_vector_store):
    """测试知识库更新"""
    # 创建
    create_resp = await client.post(
        "/api/v1/knowledge-bases/",
        json={"name": "待更新", "description": "原始描述"},
        headers=auth_headers,
    )
    kb_id = create_resp.json()["id"]

    # 更新
    update_resp = await client.put(
        f"/api/v1/knowledge-bases/{kb_id}",
        json={"name": "已更新", "description": "新描述"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "已更新"
    assert update_resp.json()["description"] == "新描述"


@pytest.mark.asyncio
async def test_knowledge_base_delete(client: AsyncClient, auth_headers, mock_vector_store):
    """测试知识库删除"""
    # 创建
    create_resp = await client.post(
        "/api/v1/knowledge-bases/",
        json={"name": "待删除"},
        headers=auth_headers,
    )
    kb_id = create_resp.json()["id"]

    # 删除
    delete_resp = await client.delete(
        f"/api/v1/knowledge-bases/{kb_id}",
        headers=auth_headers,
    )
    assert delete_resp.status_code == 200
    assert "已删除" in delete_resp.json()["message"]

    # 验证向量集合也被删除
    mock_vector_store.delete_collection.assert_called_once_with(str(kb_id))

    # 验证记录已删除
    get_resp = await client.get(
        f"/api/v1/knowledge-bases/{kb_id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_knowledge_base_not_found(client: AsyncClient, auth_headers):
    """测试获取不存在的知识库返回 404"""
    resp = await client.get(
        "/api/v1/knowledge-bases/nonexistent-id",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ============================================================
# 4. 人工审核 (Human Review)
# ============================================================

@pytest.mark.asyncio
async def test_get_pending_reviews(client: AsyncClient, auth_headers):
    """测试获取待审核请求列表"""
    resp = await client.get(
        "/api/v1/reviews/pending",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_review_not_found(client: AsyncClient, auth_headers):
    """测试获取不存在的审核详情返回 404"""
    resp = await client.get(
        "/api/v1/reviews/nonexistent-id",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_approve_nonexistent_review(client: AsyncClient, auth_headers):
    """测试批准不存在的审核返回 400"""
    with patch(
        "app.engine.executor.ExecutionEngine.submit_review",
        side_effect=ValueError("审核请求不存在"),
    ):
        resp = await client.post(
            "/api/v1/reviews/nonexistent-id/approve",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "审核请求不存在" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reject_nonexistent_review(client: AsyncClient, auth_headers):
    """测试拒绝不存在的审核返回 400"""
    with patch(
        "app.engine.executor.ExecutionEngine.submit_review",
        side_effect=ValueError("审核请求不存在"),
    ):
        resp = await client.post(
            "/api/v1/reviews/nonexistent-id/reject",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "审核请求不存在" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_skip_nonexistent_review(client: AsyncClient, auth_headers):
    """测试跳过不存在的审核返回 400"""
    with patch(
        "app.engine.executor.ExecutionEngine.submit_review",
        side_effect=ValueError("审核请求不存在"),
    ):
        resp = await client.post(
            "/api/v1/reviews/nonexistent-id/skip",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "审核请求不存在" in resp.json()["detail"]


# ============================================================
# 5. DAG 校验 (Validation)
# ============================================================

@pytest.mark.asyncio
async def test_dag_validation_valid(client: AsyncClient, auth_headers):
    """测试合法 DAG 校验通过"""
    crew_resp = await client.post(
        "/api/v1/crews/",
        json={"name": "DAG测试", "process": "sequential"},
        headers=auth_headers,
    )
    assert crew_resp.status_code == 201
    crew_id = crew_resp.json()["id"]

    agent_resp = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": crew_id,
            "name": "DAG Agent",
            "role": "助手",
            "goal": "验证 DAG 结构",
            "llm_provider": "mock",
        },
        headers=auth_headers,
    )
    assert agent_resp.status_code == 201
    agent_id = agent_resp.json()["id"]

    task1_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "agent_id": agent_id,
            "name": "前置任务",
            "description": "第一个任务",
            "expected_output": "输出1",
        },
        headers=auth_headers,
    )
    assert task1_resp.status_code == 201
    task1_id = task1_resp.json()["id"]

    task2_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "agent_id": agent_id,
            "name": "后续任务",
            "description": "依赖前置任务",
            "expected_output": "输出2",
            "context_task_ids": [task1_id],
        },
        headers=auth_headers,
    )
    assert task2_resp.status_code == 201

    validate_resp = await client.get(
        f"/api/v1/validation/crew/{crew_id}/validate",
        headers=auth_headers,
    )
    assert validate_resp.status_code == 200
    data = validate_resp.json()
    assert data["valid"] is True
    assert data["stats"]["agents"] == 1
    assert data["stats"]["tasks"] == 2
    assert data["stats"]["tasks_with_agent"] == 2
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_dag_validation_empty_crew(client: AsyncClient, auth_headers):
    """测试空工作流 DAG 校验报错"""
    crew_resp = await client.post(
        "/api/v1/crews/",
        json={"name": "空工作流"},
        headers=auth_headers,
    )
    crew_id = crew_resp.json()["id"]

    validate_resp = await client.get(
        f"/api/v1/validation/crew/{crew_id}/validate",
        headers=auth_headers,
    )
    assert validate_resp.status_code == 200
    data = validate_resp.json()
    assert data["valid"] is False
    assert len(data["errors"]) >= 2


@pytest.mark.asyncio
async def test_dag_validation_cycle_detection(client: AsyncClient, auth_headers):
    """测试循环依赖检测"""
    crew_resp = await client.post(
        "/api/v1/crews/",
        json={"name": "循环测试"},
        headers=auth_headers,
    )
    crew_id = crew_resp.json()["id"]

    agent_resp = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": crew_id,
            "name": "循环Agent",
            "role": "助手",
            "goal": "测试循环检测",
            "llm_provider": "mock",
        },
        headers=auth_headers,
    )
    agent_id = agent_resp.json()["id"]

    task_a_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "agent_id": agent_id,
            "name": "任务A",
            "description": "任务A",
        },
        headers=auth_headers,
    )
    task_a_id = task_a_resp.json()["id"]

    task_b_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "agent_id": agent_id,
            "name": "任务B",
            "description": "依赖A",
            "context_task_ids": [task_a_id],
        },
        headers=auth_headers,
    )
    task_b_id = task_b_resp.json()["id"]

    # 更新 task A 依赖 B（形成环）
    await client.put(
        f"/api/v1/tasks/{task_a_id}",
        json={"context_task_ids": [task_b_id]},
        headers=auth_headers,
    )

    validate_resp = await client.get(
        f"/api/v1/validation/crew/{crew_id}/validate",
        headers=auth_headers,
    )
    assert validate_resp.status_code == 200
    data = validate_resp.json()
    assert data["valid"] is False
    assert any("循环" in e or "cycle" in e.lower() for e in data["errors"])


@pytest.mark.asyncio
async def test_dag_validation_not_found(client: AsyncClient, auth_headers):
    """测试不存在的工作流校验返回 404"""
    resp = await client.get(
        "/api/v1/validation/crew/nonexistent-id/validate",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ============================================================
# 6. 执行生命周期 (Execution Lifecycle)
# ============================================================

@pytest.mark.asyncio
async def test_execution_lifecycle_create_and_get(
    client: AsyncClient, auth_headers, test_crew, test_tasks,
):
    """测试执行创建和获取"""
    exec_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=auth_headers,
    )
    assert exec_resp.status_code == 201
    exec_data = exec_resp.json()
    assert exec_data["crew_id"] == test_crew["id"]
    assert exec_data["status"] == "pending"
    execution_id = exec_data["id"]

    get_resp = await client.get(
        f"/api/v1/executions/{execution_id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == execution_id


@pytest.mark.asyncio
async def test_execution_list(client: AsyncClient, auth_headers, test_crew, test_tasks):
    """测试执行列表"""
    await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=auth_headers,
    )

    list_resp = await client.get(
        "/api/v1/executions/",
        headers=auth_headers,
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_execution_not_found(client: AsyncClient, auth_headers):
    """测试获取不存在的执行返回 404"""
    resp = await client.get(
        "/api/v1/executions/nonexistent-id",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_nonexistent_execution(client: AsyncClient, auth_headers):
    """测试取消不存在的执行返回 404"""
    resp = await client.post(
        "/api/v1/executions/nonexistent-id/cancel",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_checkpoints_empty(client: AsyncClient, auth_headers, test_crew, test_tasks):
    """测试新执行无断点"""
    exec_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=auth_headers,
    )
    execution_id = exec_resp.json()["id"]

    ckpt_resp = await client.get(
        f"/api/v1/executions/{execution_id}/checkpoints",
        headers=auth_headers,
    )
    assert ckpt_resp.status_code == 200
    assert isinstance(ckpt_resp.json(), list)


@pytest.mark.asyncio
async def test_execution_stats(client: AsyncClient, auth_headers, test_crew, test_tasks):
    """测试执行统计接口"""
    await client.post(
        "/api/v1/executions/",
        json={"crew_id": test_crew["id"]},
        headers=auth_headers,
    )

    stats_resp = await client.get(
        "/api/v1/executions/stats/summary",
        headers=auth_headers,
    )
    assert stats_resp.status_code == 200
    data = stats_resp.json()
    assert "total_executions" in data
    assert "completed_executions" in data
    assert "success_rate" in data
    assert "total_tokens" in data
    assert "total_cost" in data
    assert data["total_executions"] >= 1


# ============================================================
# 7. 完整端到端工作流 (Full E2E)
# ============================================================

@pytest.mark.asyncio
async def test_full_e2e_workflow(client: AsyncClient, auth_headers, mock_vector_store):
    """完整端到端工作流：创建 Crew -> Agent -> Task -> 校验 -> 执行 -> 导出"""
    # 1. 创建工作流
    crew_resp = await client.post(
        "/api/v1/crews/",
        json={"name": "E2E测试", "description": "端到端集成测试", "process": "sequential"},
        headers=auth_headers,
    )
    assert crew_resp.status_code == 201
    crew_id = crew_resp.json()["id"]

    # 2. 创建 Agent
    agent_resp = await client.post(
        "/api/v1/agents/",
        json={
            "crew_id": crew_id,
            "name": "E2E Agent",
            "role": "研究员",
            "goal": "完成端到端测试任务",
            "llm_provider": "mock",
        },
        headers=auth_headers,
    )
    assert agent_resp.status_code == 201
    agent_id = agent_resp.json()["id"]

    # 3. 创建 Tasks（带依赖）
    task1_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "agent_id": agent_id,
            "name": "数据收集",
            "description": "收集测试数据",
            "expected_output": "原始数据",
        },
        headers=auth_headers,
    )
    assert task1_resp.status_code == 201
    task1_id = task1_resp.json()["id"]

    task2_resp = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "agent_id": agent_id,
            "name": "数据分析",
            "description": "分析收集的数据",
            "expected_output": "分析报告",
            "context_task_ids": [task1_id],
        },
        headers=auth_headers,
    )
    assert task2_resp.status_code == 201

    # 4. DAG 校验
    validate_resp = await client.get(
        f"/api/v1/validation/crew/{crew_id}/validate",
        headers=auth_headers,
    )
    assert validate_resp.status_code == 200
    assert validate_resp.json()["valid"] is True

    # 5. 创建执行
    exec_resp = await client.post(
        "/api/v1/executions/",
        json={"crew_id": crew_id},
        headers=auth_headers,
    )
    assert exec_resp.status_code == 201
    execution_id = exec_resp.json()["id"]
    assert exec_resp.json()["status"] == "pending"

    # 6. 导出工作流
    export_resp = await client.get(
        f"/api/v1/exports/crews/{crew_id}/export/json",
        headers=auth_headers,
    )
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["crew"]["name"] == "E2E测试"
    assert len(export_data["crew"]["agents"]) == 1
    assert len(export_data["crew"]["tasks"]) == 2

    # 7. 检查执行状态
    get_exec_resp = await client.get(
        f"/api/v1/executions/{execution_id}",
        headers=auth_headers,
    )
    assert get_exec_resp.status_code == 200
    assert get_exec_resp.json()["id"] == execution_id

    # 8. 检查待审核列表
    reviews_resp = await client.get(
        "/api/v1/reviews/pending",
        headers=auth_headers,
    )
    assert reviews_resp.status_code == 200
