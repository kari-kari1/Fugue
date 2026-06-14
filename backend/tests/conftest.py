"""测试配置和fixtures"""
import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import db_session_manager, get_db
from app.main import app
from app.models.base import Base

# 测试数据库URL：优先使用环境变量（CI使用PostgreSQL），否则用SQLite
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# 统一全局数据库管理器使用测试数据库，确保executor也能访问测试数据
db_session_manager.reset_for_testing(TEST_DATABASE_URL)

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

# 测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """在测试会话开始时创建所有表"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 测试结束后清理
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 创建会话
    async with TestSessionLocal() as session:
        yield session

    # 清理所有表的数据（使用 TRUNCATE 避免锁竞争）
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试HTTP客户端"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(client: AsyncClient) -> dict:
    """创建测试用户"""
    import random
    uid = random.randint(10000, 99999)
    email = f"test_{uid}@example.com"
    username = f"testuser_{uid}"
    password = "Test@1234"

    # 注册
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == 201

    # 登录
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {
        "email": email,
        "username": username,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "id": response.json().get("user_id"),
    }


@pytest_asyncio.fixture
async def test_superuser(client: AsyncClient, db_session) -> dict:
    """创建超级管理员用户"""
    import random

    from app.core.security import get_password_hash
    from app.models.user import User

    uid = random.randint(10000, 99999)
    email = f"admin_{uid}@example.com"
    username = f"admin_{uid}"
    password = "Admin@1234"

    # 直接在数据库中创建超级管理员
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 登录获取token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {
        "id": str(user.id),
        "email": email,
        "username": username,
        "password": password,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest_asyncio.fixture
async def test_crew(client: AsyncClient, test_user: dict) -> dict:
    """创建测试工作流"""
    response = await client.post(
        "/api/v1/crews/",
        json={
            "name": "测试工作流",
            "description": "集成测试用工作流",
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_agents(client: AsyncClient, test_user: dict, test_crew: dict) -> list:
    """创建测试Agent"""
    crew_id = test_crew["id"]
    agents = []

    for i, (name, role) in enumerate([
        ("研究员", "研究"),
        ("写手", "写作"),
    ]):
        response = await client.post(
            "/api/v1/agents/",
            json={
                "crew_id": crew_id,
                "name": name,
                "role": role,
                "goal": f"测试{role}",
                "llm_provider": "mock",
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        agents.append(response.json())

    return agents


@pytest_asyncio.fixture
async def test_tasks(
    client: AsyncClient,
    test_user: dict,
    test_crew: dict,
    test_agents: list,
) -> list:
    """创建测试Task（带依赖关系）"""
    crew_id = test_crew["id"]
    tasks = []

    # Task 1
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "name": "研究任务",
            "description": "收集数据",
            "agent_id": test_agents[0]["id"],
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    tasks.append(response.json())

    # Task 2 (依赖Task 1)
    response = await client.post(
        "/api/v1/tasks/",
        json={
            "crew_id": crew_id,
            "name": "写作任务",
            "description": "撰写报告",
            "agent_id": test_agents[1]["id"],
            "context_task_ids": [tasks[0]["id"]],
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    tasks.append(response.json())

    return tasks
