"""审批管理 API

提供审批请求的查询、批准、拒绝等HTTP端点。
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.schemas.approval import (
    ApprovalAction,
    ApprovalRequestResponse,
)
from app.services.approval_manager import get_approval_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["approvals"])


@router.get(
    "/pending",
    response_model=list[ApprovalRequestResponse],
    summary="获取待审批请求列表",
)
async def list_pending_approvals(current_user: CurrentUser, execution_id: str = None):
    """查询所有pending状态的审批请求，支持按execution_id过滤。"""
    manager = get_approval_manager()
    pending = manager.get_pending_requests(execution_id=execution_id)
    return [_to_response(r) for r in pending]


@router.post(
    "/{request_id}/approve",
    response_model=ApprovalRequestResponse,
    summary="批准审批请求",
)
async def approve_approval_request(
    current_user: CurrentUser,
    request_id: str,
    body: ApprovalAction = None,
):
    """批准指定的审批请求。"""
    manager = get_approval_manager()
    try:
        result = await manager.approve_request(
            request_id,
            approved_by=body.approved_by if body else None,
        )
        return _to_response(result)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"审批请求 '{request_id}' 不存在",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post(
    "/{request_id}/reject",
    response_model=ApprovalRequestResponse,
    summary="拒绝审批请求",
)
async def reject_approval_request(
    current_user: CurrentUser,
    request_id: str,
    body: ApprovalAction = None,
):
    """拒绝指定的审批请求。"""
    manager = get_approval_manager()
    try:
        result = await manager.reject_request(
            request_id,
            reason=(body.reason or "") if body else "",
        )
        return _to_response(result)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"审批请求 '{request_id}' 不存在",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


def _to_response(req: dict) -> dict:
    """将内部请求字典转为API响应格式"""
    return ApprovalRequestResponse(
        request_id=req["request_id"],
        execution_id=req["execution_id"],
        tool_name=req["tool_name"],
        tool_args=req["tool_args"],
        risk_level=req["risk_level"].value
            if hasattr(req["risk_level"], "value")
            else req["risk_level"],
        status=req["status"].value
            if hasattr(req["status"], "value")
            else req["status"],
        approved_by=req.get("approved_by"),
        approved_at=req.get("approved_at"),
        rejected_at=req.get("rejected_at"),
        reject_reason=req.get("reject_reason"),
        created_at=req["created_at"],
    )
