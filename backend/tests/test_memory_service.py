"""记忆服务单元测试"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.crew import Crew
from app.services.memory_service import MemoryService


async def create_test_agent(db_session: AsyncSession, agent_id: str) -> None:
    """创建测试用的 agent 记录（满足外键约束）"""
    # 先创建一个 crew
    crew = Crew(
        id=f"crew-for-{agent_id}",
        name=f"Test Crew for {agent_id}",
        user_id="test-user-id",
    )
    db_session.add(crew)

    # 创建 agent
    agent = Agent(
        id=agent_id,
        crew_id=crew.id,
        name=f"Test Agent {agent_id}",
        role="tester",
    )
    db_session.add(agent)
    await db_session.flush()


@pytest.mark.asyncio
async def test_save_and_recall_memory(db_session: AsyncSession):
    """测试保存记忆后能通过 recall 检索到"""
    service = MemoryService(db_session)
    agent_id = "agent-test-001"

    # 先创建 agent（满足外键约束）
    await create_test_agent(db_session, agent_id)

    # 保存一条记忆
    memory = await service.save_memory(
        agent_id=agent_id,
        content="用户偏好使用 CSV 格式输出数据",
        memory_type="conclusion",
        importance=4.0,
    )

    assert memory.id is not None
    assert memory.content == "用户偏好使用 CSV 格式输出数据"
    assert memory.memory_type == "conclusion"

    # 通过 recall 检索（向量存储可能不可用，走 DB 降级路径）
    results = await service.recall_memories(
        agent_id=agent_id,
        query="CSV 格式",
        top_k=5,
    )

    assert len(results) >= 1
    contents = [r["content"] for r in results]
    assert any("CSV" in c for c in contents)


@pytest.mark.asyncio
async def test_save_multiple_memories(db_session: AsyncSession):
    """测试保存多条记忆并验证全部可检索"""
    service = MemoryService(db_session)
    agent_id = "agent-multi-001"

    # 先创建 agent（满足外键约束）
    await create_test_agent(db_session, agent_id)

    # 保存多条记忆
    await service.save_memory(agent_id, "项目使用 Python 3.11", "conclusion", 3.0)
    await service.save_memory(agent_id, "数据库使用 PostgreSQL 15", "pattern", 4.0)
    await service.save_memory(agent_id, "用户反馈: 输出格式需要更清晰", "feedback", 5.0)

    results = await service.recall_memories(agent_id, "数据库", top_k=3)
    assert len(results) >= 1
    # 至少有一条包含 PostgreSQL
    contents = [r["content"] for r in results]
    assert any("PostgreSQL" in c for c in contents), f"Expected PostgreSQL in contents: {contents}"


@pytest.mark.asyncio
async def test_context_window_query(db_session: AsyncSession):
    """测试 get_context_window 返回空列表（无执行数据时）"""
    service = MemoryService(db_session)

    # 查询不存在的执行ID，应返回空列表
    results = await service.get_context_window(
        execution_id="nonexistent-exec-id",
        window_size=10,
    )

    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_vector_store_search_fallback(db_session: AsyncSession):
    """测试向量存储不可用时检索走 DB 降级路径"""
    service = MemoryService(db_session)
    agent_id = "agent-vs-fallback"

    # 先创建 agent（满足外键约束）
    await create_test_agent(db_session, agent_id)

    # 保存一条记忆（vector store 会尝试写入但可能失败，不影响 DB）
    await service.save_memory(
        agent_id=agent_id,
        content="训练数据使用 ImageNet 子集",
        memory_type="pattern",
        importance=3.0,
    )

    # 即使向量存储不可用，DB 降级应能返回结果
    results = await service.recall_memories(
        agent_id=agent_id,
        query="训练数据",
        top_k=5,
    )
    assert len(results) >= 1
    assert any("ImageNet" in r["content"] for r in results)


@pytest.mark.asyncio
async def test_composite_score():
    """测试复合评分计算"""
    score = MemoryService.composite_score(
        recency=0.8,
        semantic=0.9,
        importance=0.7,
        alpha=0.4, beta=0.4, gamma=0.2,
    )
    expected = 0.4 * 0.8 + 0.4 * 0.9 + 0.2 * 0.7
    assert score == pytest.approx(expected)


@pytest.mark.asyncio
async def test_composite_score_default_weights():
    """测试默认权重下的复合评分"""
    score = MemoryService.composite_score(
        recency=0.5,
        semantic=0.5,
        importance=0.5,
    )
    # 默认: alpha=0.4, beta=0.4, gamma=0.2 → sum=1.0
    expected = 0.4 * 0.5 + 0.4 * 0.5 + 0.2 * 0.5
    assert score == pytest.approx(expected)


@pytest.mark.asyncio
async def test_save_memory_scoped(db_session: AsyncSession):
    """测试 scoped 记忆保存后可通过 scope 检索"""
    service = MemoryService(db_session)
    agent_id = "agent-scoped-001"

    # 先创建 agent（满足外键约束）
    await create_test_agent(db_session, agent_id)

    scope = MemoryService.build_scope("crew-001", "agent", agent_id)
    await service.save_memory_scoped(
        agent_id=agent_id,
        content="此Agent专精于时间序列预测",
        scope=scope,
        memory_type="conclusion",
        importance=4.0,
    )

    results = await service.recall_by_scope(scope, top_k=10)
    assert len(results) >= 1
    assert any("时间序列" in r["content"] for r in results)


@pytest.mark.asyncio
async def test_build_scope():
    """测试 scope 路径构建"""
    scope = MemoryService.build_scope("crew-001", "agent", "agent-123")
    assert scope == "/project/crew-001/agent/agent-123"

    shared = MemoryService.build_scope("crew-001", "shared")
    assert shared == "/project/crew-001/shared"


@pytest.mark.asyncio
async def test_recall_by_scope_prefix(db_session: AsyncSession):
    """测试按 scope 前缀检索可匹配多个实体"""
    service = MemoryService(db_session)

    # 先创建 agents（满足外键约束）
    await create_test_agent(db_session, "agent-a")
    await create_test_agent(db_session, "agent-b")

    # 保存不同 scope 的记忆
    scope_a = MemoryService.build_scope("crew-scope", "agent", "agent-a")
    scope_b = MemoryService.build_scope("crew-scope", "agent", "agent-b")

    await service.save_memory_scoped("agent-a", "记忆A内容", scope_a, importance=3.0)
    await service.save_memory_scoped("agent-b", "记忆B内容", scope_b, importance=4.0)

    # 用项目级别前缀检索
    project_scope = "/project/crew-scope/"
    results = await service.recall_by_scope(project_scope, top_k=20)
    assert len(results) >= 2


@pytest.mark.asyncio
async def test_memory_tree(db_session: AsyncSession):
    """测试记忆树结构"""
    service = MemoryService(db_session)
    tree = await service.memory_tree("crew-tree")

    assert "project_id" in tree
    assert tree["project_id"] == "crew-tree"
    assert "scopes" in tree
    assert "total_memories" in tree
    assert isinstance(tree["total_memories"], int)


@pytest.mark.asyncio
async def test_forget_by_scope(db_session: AsyncSession):
    """测试按 scope 删除记忆"""
    service = MemoryService(db_session)

    # 先创建 agent（满足外键约束）
    await create_test_agent(db_session, "agent-del")

    forget_scope = MemoryService.build_scope("crew-forget", "agent", "agent-del")

    await service.save_memory_scoped("agent-del", "将被删除的记忆", forget_scope)
    deleted_count = await service.forget_by_scope(forget_scope)
    assert deleted_count >= 1

    # 验证已删除
    results = await service.recall_by_scope(forget_scope, top_k=10)
    assert len(results) == 0
