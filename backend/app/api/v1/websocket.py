"""WebSocket路由端点"""

import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.database import db_session_manager
from app.core.security import decode_access_token
from app.core.websocket_manager import ws_manager
from app.models.execution import Execution

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/executions/{execution_id}")
async def websocket_execution_monitor(
    websocket: WebSocket,
    execution_id: str,
    token: str | None = Query(None),
):
    """
    WebSocket端点：监控执行状态

    连接URL: ws://localhost:8000/api/v1/ws/executions/{execution_id}?token=xxx

    消息格式（接收）:
    {
        "type": "ping"
    }

    消息格式（发送）:
    {
        "type": "agent.thinking" | "task.started" | "task.completed" | ...,
        "timestamp": "2026-06-02T12:00:00Z",
        "execution_id": "xxx",
        "agent_name": "研究员",
        "task_name": "数据收集",
        "data": {...}
    }
    """

    # 验证token（可选，也可以通过cookie验证）
    user_id = None
    if token:
        try:
            payload = decode_access_token(token)
            if not payload:
                await websocket.close(code=4001, reason="Invalid token")
                return
            user_id = payload.get("sub")
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            await websocket.close(code=4001, reason="Invalid token")
            return

        # B9: 验证执行记录归属 — 确保用户只能查看自己的执行
        try:
            async with db_session_manager.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(Execution).where(Execution.id == execution_id)
                )
                execution = result.scalar_one_or_none()
                if execution and str(execution.user_id) != str(user_id):
                    await websocket.close(code=4003, reason="Not authorized to view this execution")
                    return
        except Exception as e:
            logger.warning(f"Ownership verification failed: {e}")
            await websocket.close(code=4003, reason="Ownership verification failed")
            return

    # 建立连接
    await ws_manager.connect(websocket, execution_id)

    try:
        # 发送连接成功消息
        await ws_manager.send_personal_message(websocket, {
            "type": "connection.established",
            "data": {
                "execution_id": execution_id,
                "message": "Connected to execution monitor",
            },
        })

        # 发送已有 trace 历史事件（避免执行完成后连接导致事件丢失）
        try:
            async with db_session_manager.get_session() as db:
                from sqlalchemy import select
                result = await db.execute(
                    select(Execution).where(Execution.id == execution_id)
                )
                execution = result.scalar_one_or_none()
                if execution and isinstance(execution.trace, list) and execution.trace:
                    await ws_manager.send_personal_message(websocket, {
                        "type": "init",
                        "events": [
                            {
                                "type": t.get("event_type", ""),
                                "timestamp": t.get("timestamp", ""),
                                "execution_id": execution_id,
                                "agent_name": t.get("agent_name", ""),
                                "task_name": t.get("task_name", ""),
                                "data": t.get("data", {}),
                            }
                            for t in execution.trace
                        ],
                    })
        except Exception as e:
            logger.warning(f"Failed to send trace history: {e}")

        # 监听客户端消息（主要是心跳）
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理心跳
                if message.get("type") == "ping":
                    await ws_manager.send_personal_message(websocket, {
                        "type": "pong",
                        "data": {"timestamp": message.get("timestamp")},
                    })

                # 处理订阅确认
                elif message.get("type") == "subscribe":
                    logger.info(f"Client subscribed to execution {execution_id}")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for execution {execution_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket, execution_id)


@router.get("/ws/stats")
async def websocket_stats():
    """获取WebSocket连接统计"""
    return {
        "total_connections": ws_manager.get_total_connections(),
        "active_executions": len(ws_manager.active_connections),
        "connections_per_execution": {
            eid: len(conns)
            for eid, conns in ws_manager.active_connections.items()
        },
    }
