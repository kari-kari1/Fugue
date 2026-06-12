"""WebSocket连接管理器"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # execution_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.heartbeat_interval = 30  # 30秒心跳
        self._heartbeat_tasks: Dict[int, asyncio.Task] = {}  # websocket id -> heartbeat task

    async def connect(self, websocket: WebSocket, execution_id: str):
        """建立WebSocket连接"""
        await websocket.accept()

        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = set()
        self.active_connections[execution_id].add(websocket)

        # H1: 启动心跳任务
        ws_id = id(websocket)
        self._heartbeat_tasks[ws_id] = asyncio.create_task(
            self._heartbeat_loop(websocket, execution_id)
        )

        logger.info(f"WebSocket connected for execution {execution_id}. "
                    f"Total connections: {len(self.active_connections[execution_id])}")

    async def disconnect(self, websocket: WebSocket, execution_id: str):
        """断开WebSocket连接"""
        # H1: 清理心跳任务
        ws_id = id(websocket)
        heartbeat_task = self._heartbeat_tasks.pop(ws_id, None)
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()

        if execution_id in self.active_connections:
            self.active_connections[execution_id].discard(websocket)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
            logger.info(f"WebSocket disconnected for execution {execution_id}")

    async def _heartbeat_loop(self, websocket: WebSocket, execution_id: str):
        """定期发送心跳ping，保持连接活跃"""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    logger.warning(f"Heartbeat send failed for execution {execution_id}, disconnecting")
                    await self.disconnect(websocket, execution_id)
                    break
        except asyncio.CancelledError:
            pass  # 正常清理

    async def broadcast(self, execution_id: str, message: dict):
        """广播消息到指定执行的所有订阅者"""
        if execution_id not in self.active_connections:
            return

        disconnected = set()
        message_json = json.dumps(message, ensure_ascii=False)

        for websocket in self.active_connections[execution_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message: {e}")
                disconnected.add(websocket)

        # 清理断开的连接
        for ws in disconnected:
            self.active_connections[execution_id].discard(ws)

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """发送消息到单个连接"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")

    def get_connection_count(self, execution_id: str) -> int:
        """获取指定执行的连接数"""
        return len(self.active_connections.get(execution_id, set()))

    def get_total_connections(self) -> int:
        """获取总连接数"""
        return sum(len(conns) for conns in self.active_connections.values())


# 全局WebSocket管理器实例
ws_manager = WebSocketManager()
