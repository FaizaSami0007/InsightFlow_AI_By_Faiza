"""FastAPI router for Dashboard Intelligence endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboards.planner.planner import DashboardPlanner
from app.dashboards.schemas import (
    DashboardApplyPatchesRequest,
    DashboardCreateRequest,
    DashboardGenerateRequest,
    DashboardPlan,
    DashboardQualityReport,
    DashboardResponse,
    DashboardUpdateRequest,
)
from app.dashboards.service import DashboardService
from app.database.models.dataset import DatasetVersion
from app.database.models.profiling import DatasetProfile, SemanticColumn
from app.database.models.user import User
from app.database.session import get_db
from app.users.router import get_current_user

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.post("/generate", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def generate_dashboard(
    request: DashboardGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """
    Generates a complete, context-aware dashboard from dataset semantics and user intent.
    Executes all required analytical tools, creates visualization specs, and computes grid layout.
    """
    return await DashboardService.generate_dashboard(
        db=db,
        user_id=current_user.id,
        request=request,
    )


@router.post("/plan-preview", response_model=DashboardPlan)
async def preview_dashboard_plan(
    request: DashboardGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardPlan:
    """
    Constructs and previews a structured DashboardPlan without executing full analytical queries.
    Allows user inspection and confirmation of planned widgets before commitment.
    """
    v_res = await db.execute(
        select(DatasetVersion).where(
            DatasetVersion.id == request.dataset_version_id,
            DatasetVersion.dataset_id == request.dataset_id,
        )
    )
    version = v_res.scalars().first()
    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found.")

    p_res = await db.execute(
        select(DatasetProfile).where(DatasetProfile.dataset_version_id == version.id)
    )
    profile = p_res.scalars().first()
    if not profile:
        raise HTTPException(status_code=400, detail="Dataset version must be profiled first.")

    sc_res = await db.execute(
        select(SemanticColumn).where(SemanticColumn.profile_id == profile.id)
    )
    semantic_cols = {sc.column_name: sc for sc in sc_res.scalars().all()}

    return DashboardPlanner.generate_plan(
        dataset_id=request.dataset_id,
        dataset_version_id=request.dataset_version_id,
        profile=profile,
        semantic_columns=semantic_cols,
        intent=request.intent,
        purpose=request.purpose,
        min_widgets=request.min_widgets,
        max_widgets=request.max_widgets,
    )


@router.get("", response_model=List[DashboardResponse])
async def list_dashboards(
    dataset_id: Optional[str] = Query(None, description="Optional filter by dataset ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DashboardResponse]:
    """Lists all dashboards owned by the current authenticated user."""
    return await DashboardService.list_dashboards(db=db, user_id=current_user.id, dataset_id=dataset_id)


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    request: DashboardCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Creates a new empty dashboard."""
    return await DashboardService.create_dashboard(db=db, user_id=current_user.id, request=request)


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Retrieves a specific dashboard with all widgets, visual specs, and analytical outputs."""
    return await DashboardService.get_dashboard(db=db, user_id=current_user.id, dashboard_id=dashboard_id)


@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    request: DashboardUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Updates dashboard name, description, or visual theme."""
    return await DashboardService.update_dashboard(
        db=db, user_id=current_user.id, dashboard_id=dashboard_id, request=request
    )


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Deletes a dashboard and its widgets."""
    await DashboardService.delete_dashboard(db=db, user_id=current_user.id, dashboard_id=dashboard_id)


@router.post("/{dashboard_id}/duplicate", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_dashboard(
    dashboard_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Creates an independent clone of an existing dashboard."""
    return await DashboardService.duplicate_dashboard(
        db=db, user_id=current_user.id, dashboard_id=dashboard_id
    )


@router.post("/{dashboard_id}/patches", response_model=DashboardResponse)
async def apply_dashboard_patches(
    dashboard_id: str,
    request: DashboardApplyPatchesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Applies a sequence of structured atomic modifications (move, resize, change chart, add, remove)."""
    return await DashboardService.apply_patches(
        db=db, user_id=current_user.id, dashboard_id=dashboard_id, patches=request.patches
    )


@router.post("/{dashboard_id}/refresh", response_model=DashboardResponse)
async def refresh_dashboard(
    dashboard_id: str,
    filter_overrides: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Re-executes underlying analytical queries with active filter values."""
    return await DashboardService.refresh_dashboard(
        db=db,
        user_id=current_user.id,
        dashboard_id=dashboard_id,
        filter_overrides=filter_overrides,
    )


@router.get("/{dashboard_id}/quality", response_model=DashboardQualityReport)
async def get_dashboard_quality(
    dashboard_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardQualityReport:
    """Calculates an explainable quality and redundancy report for the dashboard."""
    dashboard = await DashboardService.get_dashboard_entity(db, current_user.id, dashboard_id)
    return DashboardService.calculate_quality_score(dashboard)

