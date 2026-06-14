"""人工审核 API 端点"""


from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.engine.executor import ExecutionEngine
from app.models.execution import Execution
from app.models.human_review import HumanReviewRequest

router = APIRouter()


class ReviewAction(BaseModel):
    result: dict | None = None
    comment: str | None = None


@router.get("/pending")
async def get_pending_reviews(
    db: DatabaseSession,
    current_user: CurrentUser,
    execution_id: str | None = Query(None, description="按执行ID过滤"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取待审核的请求（仅返回当前用户关联的执行中的审核）"""
    query = (
        select(HumanReviewRequest)
        .join(Execution, HumanReviewRequest.execution_id == Execution.id)
        .where(
            HumanReviewRequest.status == "pending",
            Execution.user_id == current_user.id,
        )
        .order_by(HumanReviewRequest.created_at.desc())
    )

    if execution_id:
        query = query.where(HumanReviewRequest.execution_id == execution_id)

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    reviews = result.scalars().all()

    return reviews


@router.get("/{review_id}")
async def get_review_detail(
    review_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """获取审核详情"""
    result = await db.execute(
        select(HumanReviewRequest).where(HumanReviewRequest.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="审核请求不存在")
    return review


@router.post("/{review_id}/approve")
async def approve_review(
    review_id: str,
    action: ReviewAction,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """批准审核"""
    try:
        await ExecutionEngine.submit_review(
            review_request_id=review_id,
            user_id=current_user.id,
            action="approve",
            result=action.result,
            comment=action.comment,
        )
        return {"message": "审核已批准"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{review_id}/reject")
async def reject_review(
    review_id: str,
    action: ReviewAction,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """拒绝审核"""
    try:
        await ExecutionEngine.submit_review(
            review_request_id=review_id,
            user_id=current_user.id,
            action="reject",
            comment=action.comment,
        )
        return {"message": "审核已拒绝"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{review_id}/skip")
async def skip_review(
    review_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """跳过审核"""
    try:
        await ExecutionEngine.submit_review(
            review_request_id=review_id,
            user_id=current_user.id,
            action="skip",
        )
        return {"message": "审核已跳过"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
