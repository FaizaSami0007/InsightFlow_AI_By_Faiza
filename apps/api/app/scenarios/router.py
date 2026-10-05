"""API router for Phase 13 Decision Intelligence & Scenario Simulation."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_db
from app.scenarios.schemas import (
    ScenarioComparisonRequest,
    ScenarioListResponse,
    ScenarioResultResponse,
    SensitivityAnalysisRequest,
    WhatIfScenarioRequest,
)
from app.scenarios.service import ScenarioService, ScenarioServiceError
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/scenarios", tags=["Decision Intelligence & Scenario Simulation"])


def get_scenario_service(db: AsyncSession = Depends(get_db)) -> ScenarioService:
    return ScenarioService(db)


@router.post(
    "",
    response_model=ScenarioResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute validated what-if scenario simulation",
)
@router.post(
    "/run",
    response_model=ScenarioResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute validated what-if scenario simulation (run alias)",
)
async def run_what_if_scenario(
    request: WhatIfScenarioRequest,
    current_user: User = Depends(get_current_user),
    service: ScenarioService = Depends(get_scenario_service),
) -> ScenarioResultResponse:
    """Trigger deterministic what-if scenario simulation against validated dataset baseline."""
    try:
        return await service.run_what_if_scenario(current_user.id, request)
    except ScenarioServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario execution failed: {str(exc)}",
        )


@router.post(
    "/sensitivity",
    response_model=ScenarioResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-point sensitivity analysis sweep",
)
async def run_sensitivity_analysis(
    request: SensitivityAnalysisRequest,
    current_user: User = Depends(get_current_user),
    service: ScenarioService = Depends(get_scenario_service),
) -> ScenarioResultResponse:
    """Generate sensitivity curve across varying driver levels."""
    try:
        return await service.run_sensitivity_analysis(current_user.id, request)
    except ScenarioServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sensitivity analysis failed: {str(exc)}",
        )


@router.post(
    "/compare",
    response_model=ScenarioResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate and compare side-by-side scenario branches",
)
async def run_scenario_comparison(
    request: ScenarioComparisonRequest,
    current_user: User = Depends(get_current_user),
    service: ScenarioService = Depends(get_scenario_service),
) -> ScenarioResultResponse:
    """Compare multiple scenario branches (e.g. Optimistic vs Conservative) against common baseline."""
    try:
        return await service.run_scenario_comparison(current_user.id, request)
    except ScenarioServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario comparison failed: {str(exc)}",
        )


@router.get(
    "",
    response_model=ScenarioListResponse,
    summary="List saved scenarios with optional filtering",
)
async def list_scenarios(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    target_metric: Optional[str] = Query(None, description="Filter by target metric"),
    current_user: User = Depends(get_current_user),
    service: ScenarioService = Depends(get_scenario_service),
) -> ScenarioListResponse:
    """Query stored scenario runs belonging to current user."""
    items = await service.list_scenarios(
        user_id=current_user.id,
        dataset_id=dataset_id,
        target_metric=target_metric,
    )
    return ScenarioListResponse(items=items, total=len(items))


@router.get(
    "/{scenario_id}",
    response_model=ScenarioResultResponse,
    summary="Retrieve single scenario simulation detail",
)
async def get_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    service: ScenarioService = Depends(get_scenario_service),
) -> ScenarioResultResponse:
    """Fetch detailed scenario record with full provenance and assumptions."""
    try:
        return await service.get_scenario(current_user.id, scenario_id)
    except ScenarioServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{scenario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete scenario simulation",
)
async def delete_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    service: ScenarioService = Depends(get_scenario_service),
) -> None:
    """Delete a saved scenario run."""
    try:
        await service.delete_scenario(current_user.id, scenario_id)
    except ScenarioServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
