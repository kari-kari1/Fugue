"""认证系统集成测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """测试用户注册成功"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "StrongPass123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """测试重复邮箱注册被拒绝"""
    # 第一次注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "Pass123456",
        },
    )

    # 第二次注册相同邮箱
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "Pass123456",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """测试无效邮箱格式"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-email",
            "username": "testuser",
            "password": "Pass123456",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """测试弱密码被拒绝"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "123",  # 太短
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: dict):
    """测试登录成功"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: dict):
    """测试错误密码被拒绝"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """测试不存在的用户登录"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Pass123456",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user: dict):
    """测试获取当前用户信息"""
    response = await client.get(
        "/api/v1/auth/me",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["username"] == test_user["username"]


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """测试无token访问被拒绝"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """测试无效token被拒绝"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"},
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient, test_user: dict):
    """测试Token刷新"""
    response = await client.post(
        "/api/v1/auth/refresh",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    # Token可能相同（如果在同一个时间窗口内生成）


@pytest.mark.asyncio
async def test_token_info(client: AsyncClient, test_user: dict):
    """测试获取Token信息"""
    response = await client.get(
        "/api/v1/auth/token-info",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    # API返回的字段名是remaining_seconds和is_expiring_soon
    assert "remaining_seconds" in data or "expires_in" in data
    assert "is_expiring_soon" in data
    assert isinstance(data["is_expiring_soon"], bool)


# ──────────────────────────────────────────────
# 密码重置测试
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_forgot_password_existing_email(client: AsyncClient, test_user: dict):
    """测试忘记密码：已注册邮箱返回成功消息"""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user["email"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client: AsyncClient):
    """测试忘记密码：未注册邮箱不泄露信息，返回相同消息"""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    # 不应返回token
    assert "reset_token" not in data


@pytest.mark.asyncio
async def test_reset_password_success(client: AsyncClient, test_user: dict):
    """测试重置密码成功"""
    from app.api.v1.auth import reset_tokens as _rt

    # 先发起忘记密码（生成token到模块级dict）
    await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user["email"]},
    )
    # 从 reset_tokens 中获取最新 token
    token = list(_rt.keys())[-1]

    # 使用token重置密码
    new_password = "NewSecurePass123"
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": token, "new_password": new_password},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "密码重置成功"

    # 验证新密码可以登录
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user["email"], "password": new_password},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """测试重置密码：无效token被拒绝"""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": "invalid_token", "new_password": "NewPass123"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_token_single_use(client: AsyncClient, test_user: dict):
    """测试重置密码：token只能使用一次"""
    from app.api.v1.auth import reset_tokens as _rt

    await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user["email"]},
    )
    token = list(_rt.keys())[-1]

    # 第一次使用
    await client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": token, "new_password": "NewPass123"},
    )

    # 第二次使用应失败
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"reset_token": token, "new_password": "NewPass456"},
    )
    assert response.status_code == 400


# ──────────────────────────────────────────────
# /auth/me is_superuser 字段测试
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_returns_is_superuser(client: AsyncClient, test_user: dict):
    """测试 GET /auth/me 返回 is_superuser 字段"""
    response = await client.get(
        "/api/v1/auth/me",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_superuser" in data
    assert isinstance(data["is_superuser"], bool)
    assert data["is_superuser"] is False  # 普通用户不是超级管理员


@pytest.mark.asyncio
async def test_me_superuser_flag(client: AsyncClient, test_superuser: dict):
    """测试超级管理员的 /auth/me 返回 is_superuser=True"""
    response = await client.get(
        "/api/v1/auth/me",
        headers=test_superuser["headers"],
    )
    assert response.status_code == 200
    assert response.json()["is_superuser"] is True


# ──────────────────────────────────────────────
# RBAC 管理员接口测试
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users_requires_admin(client: AsyncClient, test_user: dict):
    """测试列出用户接口：普通用户被拒绝"""
    response = await client.get(
        "/api/v1/auth/users",
        headers=test_user["headers"],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_admin_success(client: AsyncClient, test_superuser: dict, test_user: dict):
    """测试列出用户接口：管理员可以访问"""
    response = await client.get(
        "/api/v1/auth/users",
        headers=test_superuser["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # 至少包含test_user和test_superuser


@pytest.mark.asyncio
async def test_toggle_superuser_requires_admin(client: AsyncClient, test_user: dict):
    """测试切换超级管理员：普通用户被拒绝"""
    response = await client.patch(
        f"/api/v1/auth/users/{test_user.get('id', 'fake-id')}/toggle-superuser",
        headers=test_user["headers"],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_toggle_superuser_admin_success(client: AsyncClient, test_superuser: dict, test_user: dict):
    """测试切换超级管理员：管理员可以切换普通用户状态"""
    # 先获取test_user的id
    users_resp = await client.get(
        "/api/v1/auth/users",
        headers=test_superuser["headers"],
    )
    users = users_resp.json()
    target_user = next(u for u in users if u["email"] == test_user["email"])

    assert target_user["is_superuser"] is False

    response = await client.patch(
        f"/api/v1/auth/users/{target_user['id']}/toggle-superuser",
        headers=test_superuser["headers"],
    )
    assert response.status_code == 200
    assert response.json()["is_superuser"] is True

    # 再次切换回来
    response = await client.patch(
        f"/api/v1/auth/users/{target_user['id']}/toggle-superuser",
        headers=test_superuser["headers"],
    )
    assert response.status_code == 200
    assert response.json()["is_superuser"] is False


@pytest.mark.asyncio
async def test_toggle_superuser_nonexistent_user(client: AsyncClient, test_superuser: dict):
    """测试切换超级管理员：不存在的用户返回404"""
    response = await client.patch(
        "/api/v1/auth/users/99999/toggle-superuser",
        headers=test_superuser["headers"],
    )
    assert response.status_code == 404


# ──────────────────────────────────────────────
# Demo 接口 RBAC 测试
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_seed_templates_requires_admin(client: AsyncClient, test_user: dict):
    """测试模板种子接口：普通用户被拒绝"""
    response = await client.post(
        "/api/v1/demo/seed-templates",
        headers=test_user["headers"],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_seed_demo_workflow_requires_admin(client: AsyncClient, test_user: dict):
    """测试演示工作流种子接口：普通用户被拒绝"""
    response = await client.post(
        "/api/v1/demo/seed-demo-workflow",
        headers=test_user["headers"],
    )
    assert response.status_code == 403
