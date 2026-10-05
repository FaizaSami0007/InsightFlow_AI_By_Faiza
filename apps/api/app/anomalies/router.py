"""API router for Phase 12 Anomaly Detection & Proactive Insight Intelligence."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.anomalies.detectors.registry import AnomalyDetectorRegistry
from app.anomalies.schemas import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyFeedbackRequest,
    AnomalyListResponse,
    AnomalyPoint,
    AnomalyStatusUpdateRequest,
    InsightListResponse,
    InsightResponse,
)
from app.anomalies.service import AnomalyService, AnomalyServiceError
from app.database.models.anomalies import AnomalySeverity, AnomalyStatus
from app.database.models.user import User
from app.database.session import get_db
from app.users.dependencies import get_current_user

router = APIRouter(tags=["Anomaly Detection & Proactive Insights"])


def get_anomaly_service(db: AsyncSession = Depends(get_db)) -> AnomalyService:
    return AnomalyService(db)


@router.post(
    "/anomalies/detect",
    response_model=AnomalyDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute validated statistical anomaly detection and insight extraction",
)
@router.post(
    "/anomalies",
    response_model=AnomalyDetectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger anomaly detection (alias)",
)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    current_user: User = Depends(get_current_user),
    service: AnomalyService = Depends(get_anomaly_service),
) -> AnomalyDetectionResponse:
    """Execute deterministic statistical anomaly detection across requested dataset."""
    try:
        return await service.detect_anomalies(current_user.id, request)
    except AnomalyServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection execution failed: {str(exc)}",
        )


@router.get(
    "/anomalies/methods",
    response_model=List[Dict[str, Any]],
    summary="List supported anomaly detection methodologies",
)
async def list_methods(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Return available anomaly detection methods, description, and applicable data conditions."""
    methods = AnomalyDetectorRegistry.list_methods()
    return [
        {
            "id": m.value,
            "name": m.value.replace("_", " ").title(),
            "description": f"Statistical detector for {m.value.lower()}",
            "method": m.value,
        }
        for m in methods
    ]


@router.get(
    "/anomalies",
    response_model=AnomalyListResponse,
    summary="List detected anomalies with optional filtering",
)
async def list_anomalies(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    severity: Optional[AnomalySeverity] = Query(None, description="Filter by severity level"),
    status_filter: Optional[AnomalyStatus] = Query(None, alias="status", description="Filter by alert status"),
    current_user: User = Depends(get_current_user),
    service: AnomalyService = Depends(get_anomaly_service),
) -> AnomalyListResponse:
    """Query stored anomalies belonging to current user."""
    items = await service.list_anomalies(
        user_id=current_user.id,
        dataset_id=dataset_id,
        severity=severity,
        status=status_filter,
    )
    return AnomalyListResponse(items=items, total=len(items))


@router.get(
    "/anomalies/{anomaly_id}",
    response_model=AnomalyPoint,
    summary="Retrieve single anomaly detail with root causes and evidence",
)
async def get_anomaly(
    anomaly_id: str,
    current_user: User = Depends(get_current_user),
    service: AnomalyService = Depends(get_anomaly_service),
) -> AnomalyPoint:
    """Fetch detailed anomaly record with full provenance and root-cause breakdown."""
    try:
        return await service.get_anomaly(current_user.id, anomaly_id)
    except AnomalyServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/anomalies/{anomaly_id}/status",
    response_model=AnomalyPoint,
    summary="Update lifecycle status of an anomaly record",
)
async def update_anomaly_status(
    anomaly_id: str,
    request: AnomalyStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: AnomalyService = Depends(get_anomaly_service),
) -> AnomalyPoint:
    """Acknowledge, dismiss, or resolve a detected anomaly alert."""
    try:
        return await service.update_anomaly_status(current_user.id, anomaly_id, request)
    except AnomalyServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/insights",
    response_model=InsightListResponse,
    summary="Query proactive insights feed",
)
async def list_insights(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    min_severity: Optional[AnomalySeverity] = Query(None, description="Filter by minimum severity"),
    current_user: User = Depends(get_current_user),
    service: AnomalyService = Depends(get_anomaly_service),
) -> InsightListResponse:
    """Retrieve feed of explainable proactive insights."""
    items = await service.list_insights(
        user_id=current_user.id,
        dataset_id=dataset_id,
        min_severity=min_severity,
    )
    return InsightListResponse(items=items, total=len(items))


@router.post(
    "/insights/{insight_id}/feedback",
    response_model=InsightResponse,
    summary="Submit user feedback on proactive insight usefulness",
)
async def submit_insight_feedback(
    insight_id: str,
    request: AnomalyFeedbackRequest,
    current_user: User = Depends(get_current_user),
    service: AnomalyService = Depends(get_anomaly_service),
) -> InsightResponse:
    """Record user feedback ('useful', 'not_useful', 'expected_behavior') for an insight."""
    try:
        return await service.submit_feedback(current_user.id, insight_id, request)
    except AnomalyServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
