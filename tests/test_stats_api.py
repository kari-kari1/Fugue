"""统计API测试"""

import asyncio
import sys
from pathlib import Path

# 添加backend到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_stats_endpoint():
    """测试统计端点"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 先注册和登录获取token
        import random
        uid = random.randint(10000, 99999)
        email = f"stats_test_{uid}@example.com"

        # 注册
        register_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"statsuser_{uid}",
                "password": "TestPass123",
            },
        )
        assert register_resp.status_code == 201, f"Register failed: {register_resp.status_code}"

        # 登录
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "TestPass123"},
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.status_code}"

        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 测试统计端点
        stats_resp = await client.get("/api/v1/executions/stats/summary", headers=headers)
        assert stats_resp.status_code == 200, f"Stats API failed: {stats_resp.status_code}"

        stats_data = stats_resp.json()
        print(f"Stats response: {stats_data}")

        # 验证返回结构
        assert "total_executions" in stats_data, "Missing total_executions"
        assert "completed_executions" in stats_data, "Missing completed_executions"
        assert "success_rate" in stats_data, "Missing success_rate"
        assert "total_tokens" in stats_data, "Missing total_tokens"
        assert "total_cost" in stats_data, "Missing total_cost"

        # 新用户应该都是0
        assert stats_data["total_executions"] == 0, f"Expected 0, got {stats_data['total_executions']}"
        assert stats_data["completed_executions"] == 0, f"Expected 0, got {stats_data['completed_executions']}"
        assert stats_data["success_rate"] == 0, f"Expected 0, got {stats_data['success_rate']}"
        assert stats_data["total_tokens"] == 0, f"Expected 0, got {stats_data['total_tokens']}"
        assert stats_data["total_cost"] == 0.0, f"Expected 0.0, got {stats_data['total_cost']}"

        print("✅ Stats API test passed!")


if __name__ == "__main__":
    asyncio.run(test_stats_endpoint())
