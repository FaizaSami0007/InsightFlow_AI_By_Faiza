"""API Router for Dashboard Exports."""

from typing import List

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_db
from app.exports.schemas import ExportRequest, ExportResponse
from app.exports.service import ExportService
from app.users.dependencies import get_current_user

router = APIRouter(tags=["Exports"])


@router.post(
    "/dashboards/{dashboard_id}/exports",
    response_model=ExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new export (PDF, PNG, CSV, JSON) for a dashboard",
)
async def create_dashboard_export(
    dashboard_id: str,
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportResponse:
    service = ExportService(db)
    return await service.create_export(dashboard_id, current_user.id, request)


@router.get(
    "/dashboards/{dashboard_id}/exports",
    response_model=List[ExportResponse],
    summary="List all exports generated for a dashboard",
)
async def list_dashboard_exports(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ExportResponse]:
    service = ExportService(db)
    return await service.list_exports(dashboard_id, current_user.id)


@router.get(
    "/exports/{export_id}",
    response_model=ExportResponse,
    summary="Get export metadata and status",
)
async def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportResponse:
    service = ExportService(db)
    return await service.get_export(export_id, current_user.id)


@router.get(
    "/exports/{export_id}/download",
    summary="Download export file",
)
async def download_export_file(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)
    file_path, filename, content_type = await service.get_export_file_for_download(export_id, current_user.id)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=content_type,
    )
