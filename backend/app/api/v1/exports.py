# backend/app/api/v1/exports.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.deps import CurrentUser, DatabaseSession
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/crews/{crew_id}/export/json")
async def export_crew_json(
    crew_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """导出工作流为JSON"""
    export_service = ExportService(db, current_user.id)
    try:
        data = await export_service.export_crew_json(crew_id)
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": f"attachment; filename=workflow-{crew_id}.json"
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/executions/{execution_id}/export/markdown")
async def export_execution_markdown(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """导出执行结果为Markdown"""
    export_service = ExportService(db, current_user.id)
    try:
        markdown = await export_service.export_execution_markdown(execution_id)
        return PlainTextResponse(
            content=markdown,
            headers={
                "Content-Disposition": f"attachment; filename=execution-{execution_id}.md"
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/executions/{execution_id}/export/json")
async def export_execution_json(
    execution_id: str,
    db: DatabaseSession,
    current_user: CurrentUser,
):
    """导出执行结果为JSON"""
    export_service = ExportService(db, current_user.id)
    try:
        data = await export_service.export_execution_json(execution_id)
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": f"attachment; filename=execution-{execution_id}.json"
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
