from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.engine.registry import analysis_registry
from app.analytics.schemas import (
    AnalysisHistoryItem,
    AnalysisResponse,
    AnalysisRunRequest,
    AnalysisToolsResponse,
)
from app.analytics.service import analytics_service
from app.database.models.user import User
from app.database.session import get_db
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """
    Executes a deterministic analytical operation against an authorized dataset version.
    Records provenance and execution metrics.
    """
    return await analytics_service.run_analysis(request=request, current_user=current_user, db=db)


@router.get("/tools", response_model=AnalysisToolsResponse)
async def list_tools(
    current_user: User = Depends(get_current_user),
) -> AnalysisToolsResponse:
    """
    Returns machine-readable catalog of all registered analysis tools with schemas.
    """
    tools = analysis_registry.list_tools()
    return AnalysisToolsResponse(tools=tools)


@router.get("/history", response_model=List[AnalysisHistoryItem])
async def list_analysis_history(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID filter"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[AnalysisHistoryItem]:
    """
    Lists past analysis executions for the authenticated user.
    """
    return await analytics_service.list_history(current_user=current_user, dataset_id=dataset_id, db=db, limit=limit)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """
    Retrieves the execution status, structured results, and provenance of an analysis.
    """
    return await analytics_service.get_analysis(analysis_id=analysis_id, current_user=current_user, db=db)
