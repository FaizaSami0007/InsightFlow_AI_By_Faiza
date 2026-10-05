"""API Router for Dashboard Sharing and Public Links."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_db
from app.shares.schemas import (
    ShareCreateRequest,
    SharedDashboardViewResponse,
    SharedFilterRefreshRequest,
    ShareResponse,
)
from app.shares.service import ShareService
from app.users.dependencies import get_current_user

router = APIRouter(tags=["Sharing"])


@router.post(
    "/dashboards/{dashboard_id}/shares",
    response_model=ShareResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a secure share link for a dashboard",
)
async def create_dashboard_share(
    dashboard_id: str,
    request: ShareCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    service = ShareService(db)
    return await service.create_share(dashboard_id, current_user.id, request)


@router.get(
    "/dashboards/{dashboard_id}/shares",
    response_model=List[ShareResponse],
    summary="List all share links created for a dashboard (Owner only)",
)
async def list_dashboard_shares(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ShareResponse]:
    service = ShareService(db)
    return await service.list_shares(dashboard_id, current_user.id)


@router.delete(
    "/shares/{share_id}",
    response_model=ShareResponse,
    summary="Revoke a share link (Owner only)",
)
async def revoke_dashboard_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    service = ShareService(db)
    return await service.revoke_share(share_id, current_user.id)


@router.post(
    "/shares/{share_id}/revoke",
    response_model=ShareResponse,
    summary="Revoke a share link (POST alternative)",
)
async def revoke_dashboard_share_post(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    service = ShareService(db)
    return await service.revoke_share(share_id, current_user.id)


# Public / Unauthenticated Shared Dashboard Read-Only Routes
@router.get(
    "/shared/dashboards/{share_token}",
    response_model=SharedDashboardViewResponse,
    summary="View a shared dashboard via token (Read-Only)",
)
async def view_shared_dashboard(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> SharedDashboardViewResponse:
    service = ShareService(db)
    return await service.get_shared_dashboard(share_token)


@router.post(
    "/shared/dashboards/{share_token}/refresh",
    response_model=SharedDashboardViewResponse,
    summary="Test temporary session filters on a shared dashboard",
)
async def refresh_shared_dashboard_filters(
    share_token: str,
    request: SharedFilterRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> SharedDashboardViewResponse:
    service = ShareService(db)
    return await service.refresh_shared_filters(share_token, request)
