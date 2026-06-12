"""WebSocket功能测试"""

import asyncio
import pytest
import json
import sys
from pathlib import Path

# 添加backend到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.asyncio
async def test_websocket_connection():
    """测试WebSocket连接"""
    # 注意：这个测试需要实际运行的服务器
    # 这里只是验证WebSocket端点是否存在
    from app.api.v1.websocket import router
    assert router is not None


@pytest.mark.asyncio
async def test_websocket_stats_endpoint():
    """测试WebSocket统计端点"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ws/ws/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_connections" in data
        assert "active_executions" in data


def test_websocket_manager():
    """测试WebSocket管理器"""
    from app.core.websocket_manager import WebSocketManager

    manager = WebSocketManager()
    assert manager.get_total_connections() == 0
    assert manager.get_connection_count("test") == 0


def test_event_publisher():
    """测试事件发布器"""
    from app.services.event_publisher import EventPublisher, EventType

    publisher = EventPublisher()
    assert publisher is not None
    assert EventType.AGENT_THINKING == "agent.thinking"
    assert EventType.TASK_STARTED == "task.started"
    assert EventType.CREW_COMPLETED == "crew.completed"


if __name__ == "__main__":
    print("Running WebSocket tests...")
    asyncio.run(test_websocket_stats_endpoint())
    test_websocket_manager()
    test_event_publisher()
    print("All tests passed!")
