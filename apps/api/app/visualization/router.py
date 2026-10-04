"""FastAPI router for deterministic visualization endpoints."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_db
from app.users.dependencies import get_current_user
from app.visualization.schemas import (
    ChartTypeMetadata,
    VisualizationRecommendRequest,
    VisualizationSpec,
    VisualizationValidateRequest,
    VisualizationValidationResult,
)
from app.visualization.service import visualization_service

router = APIRouter(prefix="/visualizations", tags=["Visualizations"])


@router.get(
    "/charts",
    response_model=List[ChartTypeMetadata],
    status_code=status.HTTP_200_OK,
    summary="List supported chart types and capabilities",
)
async def list_chart_types(
    current_user: User = Depends(get_current_user),
) -> List[ChartTypeMetadata]:
    """Returns all supported chart types and their data requirements."""
    return await visualization_service.get_chart_types()


@router.post(
    "/recommend",
    response_model=VisualizationSpec,
    status_code=status.HTTP_200_OK,
    summary="Recommend a context-aware chart specification for an analysis",
)
async def recommend_visualization(
    request: VisualizationRecommendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisualizationSpec:
    """Evaluates the analysis result against deterministic rules to generate a chart specification."""
    return await visualization_service.recommend_visualization(
        request=request,
        current_user=current_user,
        db=db,
    )


@router.post(
    "/validate",
    response_model=VisualizationValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate a candidate visualization specification against analysis results",
)
async def validate_visualization(
    request: VisualizationValidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisualizationValidationResult:
    """Ensures a chart specification conforms to column schemas, data types, and security constraints."""
    return await visualization_service.validate_visualization(
        request=request,
        current_user=current_user,
        db=db,
    )
