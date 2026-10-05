"""API router for Phase 11 Predictive Analytics & Time-Series Forecasting."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_db
from app.forecasting.models.registry import ForecastModelRegistry
from app.forecasting.schemas import (
    ForecastListResponse,
    ForecastResponse,
    ForecastRunRequest,
)
from app.forecasting.service import ForecastService, ForecastServiceError
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/forecasts", tags=["Predictive Analytics & Forecasting"])


def get_forecast_service(db: AsyncSession = Depends(get_db)) -> ForecastService:
    return ForecastService(db)


@router.post(
    "",
    response_model=ForecastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute validated time-series forecast",
)
@router.post(
    "/run",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute validated time-series forecast (run alias)",
)
async def run_forecast(
    request: ForecastRunRequest,
    current_user: User = Depends(get_current_user),
    service: ForecastService = Depends(get_forecast_service),
) -> ForecastResponse:
    """Trigger deterministic, backtested time-series forecasting against a dataset."""
    try:
        return await service.run_forecast(current_user.id, request)
    except ForecastServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting execution failed: {str(exc)}",
        )


@router.get(
    "/models",
    response_model=List[Dict[str, Any]],
    summary="List supported forecast model families",
)
async def list_models(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Retrieve metadata and descriptions for all supported forecasting estimators."""
    return ForecastModelRegistry.list_supported_models()


@router.get(
    "",
    response_model=ForecastListResponse,
    summary="List historical forecast executions",
)
async def list_forecasts(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    current_user: User = Depends(get_current_user),
    service: ForecastService = Depends(get_forecast_service),
) -> ForecastListResponse:
    """List previous forecasting results for the current authenticated user."""
    items = await service.list_forecasts(current_user.id, dataset_id)
    return ForecastListResponse(items=items, total=len(items))


@router.get(
    "/dataset/{dataset_id}",
    response_model=ForecastListResponse,
    summary="List historical forecast executions for a dataset",
)
async def list_dataset_forecasts(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    service: ForecastService = Depends(get_forecast_service),
) -> ForecastListResponse:
    """List previous forecasting results for a specific dataset."""
    items = await service.list_forecasts(current_user.id, dataset_id)
    return ForecastListResponse(items=items, total=len(items))


@router.get(
    "/{forecast_id}",
    response_model=ForecastResponse,
    summary="Get forecast execution details",
)
async def get_forecast(
    forecast_id: str,
    current_user: User = Depends(get_current_user),
    service: ForecastService = Depends(get_forecast_service),
) -> ForecastResponse:
    """Retrieve full prediction intervals, diagnostics, and metrics for a specific forecast ID."""
    try:
        return await service.get_forecast(current_user.id, forecast_id)
    except ForecastServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{forecast_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a forecast execution",
)
async def delete_forecast(
    forecast_id: str,
    current_user: User = Depends(get_current_user),
    service: ForecastService = Depends(get_forecast_service),
) -> None:
    """Delete a stored forecast execution record."""
    await service.delete_forecast(current_user.id, forecast_id)
