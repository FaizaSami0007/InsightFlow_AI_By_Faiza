"""FastAPI REST API router for Phase 16 Production MLOps and Model Lifecycle."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.mlops import MLModelType, MLModelVersionStatus
from app.database.models.user import User
from app.database.session import get_db
from app.mlops.schemas import (
    MLExperimentCreateRequest,
    MLExperimentResponse,
    MLModelAlertListResponse,
    MLModelAlertResponse,
    MLModelCreateRequest,
    MLModelDriftCheckRequest,
    MLModelDriftReportResponse,
    MLModelEvaluationRequest,
    MLModelEvaluationResponse,
    MLModelListResponse,
    MLModelPromotionRequest,
    MLModelResponse,
    MLModelRollbackRequest,
    MLModelUpdateRequest,
    MLModelVersionCreateRequest,
    MLModelVersionResponse,
)
from app.mlops.service import (
    InvalidModelTransitionError,
    MLOpsService,
    MLOpsServiceError,
    ModelNotFoundError,
    UnauthorizedModelAccessError,
)
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/mlops", tags=["MLOps & Model Lifecycle"])


# ==============================================================================
# 1. MODEL REGISTRY ENDPOINTS
# ==============================================================================


@router.post(
    "/models",
    response_model=MLModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new ML model",
)
async def create_model(
    payload: MLModelCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    model = await service.create_model(current_user, payload)
    return MLModelResponse(
        id=model.id,
        user_id=model.user_id,
        workspace_id=model.workspace_id,
        name=model.name,
        description=model.description,
        model_type=model.model_type,
        task_type=model.task_type,
        framework=model.framework,
        provider=model.provider,
        status=model.status,
        owner=model.owner,
        tags=model.tags,
        metadata_json=model.metadata_json,
        versions_count=len(model.versions) if model.versions else 0,
        active_production_version=None,
        health_status="GOOD",
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.get(
    "/models",
    response_model=MLModelListResponse,
    summary="List all registered models",
)
async def list_models(
    model_type: Optional[MLModelType] = Query(None, description="Filter by model family"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by model status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    models = await service.list_models(current_user, model_type=model_type, status=status_filter)
    items = []
    for m in models:
        prod_v = next((v.version for v in m.versions if v.status == MLModelVersionStatus.PRODUCTION), None)
        items.append(
            MLModelResponse(
                id=m.id,
                user_id=m.user_id,
                workspace_id=m.workspace_id,
                name=m.name,
                description=m.description,
                model_type=m.model_type,
                task_type=m.task_type,
                framework=m.framework,
                provider=m.provider,
                status=m.status,
                owner=m.owner,
                tags=m.tags,
                metadata_json=m.metadata_json,
                versions_count=len(m.versions) if m.versions else 0,
                active_production_version=prod_v,
                health_status="GOOD" if not m.versions else m.versions[0].health_status,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
        )
    return MLModelListResponse(items=items, total=len(items))


@router.get(
    "/models/{model_id}",
    response_model=MLModelResponse,
    summary="Get model details by ID",
)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        m = await service.get_model(model_id, current_user)
        prod_v = next((v.version for v in m.versions if v.status == MLModelVersionStatus.PRODUCTION), None)
        return MLModelResponse(
            id=m.id,
            user_id=m.user_id,
            workspace_id=m.workspace_id,
            name=m.name,
            description=m.description,
            model_type=m.model_type,
            task_type=m.task_type,
            framework=m.framework,
            provider=m.provider,
            status=m.status,
            owner=m.owner,
            tags=m.tags,
            metadata_json=m.metadata_json,
            versions_count=len(m.versions) if m.versions else 0,
            active_production_version=prod_v,
            health_status="GOOD" if not m.versions else m.versions[0].health_status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedModelAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch(
    "/models/{model_id}",
    response_model=MLModelResponse,
    summary="Update model metadata",
)
async def update_model(
    model_id: str,
    payload: MLModelUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        m = await service.update_model(model_id, current_user, payload)
        prod_v = next((v.version for v in m.versions if v.status == MLModelVersionStatus.PRODUCTION), None)
        return MLModelResponse(
            id=m.id,
            user_id=m.user_id,
            workspace_id=m.workspace_id,
            name=m.name,
            description=m.description,
            model_type=m.model_type,
            task_type=m.task_type,
            framework=m.framework,
            provider=m.provider,
            status=m.status,
            owner=m.owner,
            tags=m.tags,
            metadata_json=m.metadata_json,
            versions_count=len(m.versions) if m.versions else 0,
            active_production_version=prod_v,
            health_status="GOOD" if not m.versions else m.versions[0].health_status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedModelAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==============================================================================
# 2. MODEL VERSIONING ENDPOINTS
# ==============================================================================


@router.post(
    "/models/{model_id}/versions",
    response_model=MLModelVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new model version",
)
async def create_model_version(
    model_id: str,
    payload: MLModelVersionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        v = await service.create_model_version(model_id, current_user, payload)
        return MLModelVersionResponse(
            id=v.id,
            model_id=v.model_id,
            model_name=v.model.name if v.model else None,
            model_type=v.model.model_type if v.model else None,
            version=v.version,
            artifact_location=v.artifact_location,
            checksum=v.checksum,
            training_dataset_id=v.training_dataset_id,
            training_dataset_version_id=v.training_dataset_version_id,
            feature_schema=v.feature_schema,
            preprocessing_version=v.preprocessing_version,
            parameters=v.parameters,
            metrics=v.metrics,
            baseline_metrics=v.baseline_metrics,
            status=v.status,
            approval_record=v.approval_record,
            health_status=v.health_status,
            health_details=v.health_details,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
    except (ModelNotFoundError, MLOpsServiceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/versions/{version_id}",
    response_model=MLModelVersionResponse,
    summary="Get model version details",
)
async def get_model_version(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        v = await service.get_model_version(version_id, current_user)
        return MLModelVersionResponse(
            id=v.id,
            model_id=v.model_id,
            model_name=v.model.name if v.model else None,
            model_type=v.model.model_type if v.model else None,
            version=v.version,
            artifact_location=v.artifact_location,
            checksum=v.checksum,
            training_dataset_id=v.training_dataset_id,
            training_dataset_version_id=v.training_dataset_version_id,
            feature_schema=v.feature_schema,
            preprocessing_version=v.preprocessing_version,
            parameters=v.parameters,
            metrics=v.metrics,
            baseline_metrics=v.baseline_metrics,
            status=v.status,
            approval_record=v.approval_record,
            health_status=v.health_status,
            health_details=v.health_details,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedModelAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==============================================================================
# 3. EXPERIMENT TRACKING ENDPOINTS
# ==============================================================================


@router.post(
    "/models/{model_id}/experiments",
    response_model=MLExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a model training experiment",
)
async def create_experiment(
    model_id: str,
    payload: MLExperimentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        exp = await service.create_experiment(model_id, current_user, payload)
        return MLExperimentResponse(
            id=exp.id,
            model_id=exp.model_id,
            name=exp.name,
            dataset_id=exp.dataset_id,
            dataset_version_id=exp.dataset_version_id,
            features=exp.features,
            preprocessing_config=exp.preprocessing_config,
            parameters=exp.parameters,
            metrics=exp.metrics,
            evaluation_config=exp.evaluation_config,
            status=exp.status,
            created_at=exp.created_at,
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==============================================================================
# 4. EVALUATION & PROMOTION ENDPOINTS
# ==============================================================================


@router.post(
    "/versions/{version_id}/evaluate",
    response_model=MLModelEvaluationResponse,
    summary="Evaluate model version against test data and baselines",
)
async def evaluate_model_version(
    version_id: str,
    payload: MLModelEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        eval_record = await service.evaluate_model_version(version_id, current_user, payload)
        return MLModelEvaluationResponse(
            id=eval_record.id,
            model_version_id=eval_record.model_version_id,
            dataset_id=eval_record.dataset_id,
            dataset_version_id=eval_record.dataset_version_id,
            evaluation_type=eval_record.evaluation_type,
            metrics=eval_record.metrics,
            baseline_comparison=eval_record.baseline_comparison,
            passed_validation=eval_record.passed_validation,
            warnings=eval_record.warnings,
            evaluated_at=eval_record.evaluated_at,
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/versions/{version_id}/promote",
    response_model=MLModelVersionResponse,
    summary="Promote model version through lifecycle stages",
)
async def promote_model_version(
    version_id: str,
    payload: MLModelPromotionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        v = await service.promote_model_version(version_id, current_user, payload)
        return MLModelVersionResponse(
            id=v.id,
            model_id=v.model_id,
            model_name=v.model.name if v.model else None,
            model_type=v.model.model_type if v.model else None,
            version=v.version,
            artifact_location=v.artifact_location,
            checksum=v.checksum,
            training_dataset_id=v.training_dataset_id,
            training_dataset_version_id=v.training_dataset_version_id,
            feature_schema=v.feature_schema,
            preprocessing_version=v.preprocessing_version,
            parameters=v.parameters,
            metrics=v.metrics,
            baseline_metrics=v.baseline_metrics,
            status=v.status,
            approval_record=v.approval_record,
            health_status=v.health_status,
            health_details=v.health_details,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
    except InvalidModelTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/versions/{version_id}/rollback",
    response_model=MLModelVersionResponse,
    summary="Rollback deployment to a prior validated version",
)
async def rollback_model_version(
    version_id: str,
    payload: MLModelRollbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        v = await service.rollback_model_version(version_id, current_user, payload)
        return MLModelVersionResponse(
            id=v.id,
            model_id=v.model_id,
            model_name=v.model.name if v.model else None,
            model_type=v.model.model_type if v.model else None,
            version=v.version,
            artifact_location=v.artifact_location,
            checksum=v.checksum,
            training_dataset_id=v.training_dataset_id,
            training_dataset_version_id=v.training_dataset_version_id,
            feature_schema=v.feature_schema,
            preprocessing_version=v.preprocessing_version,
            parameters=v.parameters,
            metrics=v.metrics,
            baseline_metrics=v.baseline_metrics,
            status=v.status,
            approval_record=v.approval_record,
            health_status=v.health_status,
            health_details=v.health_details,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
    except (ModelNotFoundError, MLOpsServiceError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# 5. DRIFT, HEALTH, LINEAGE & ALERTS ENDPOINTS
# ==============================================================================


@router.post(
    "/versions/{version_id}/drift",
    response_model=MLModelDriftReportResponse,
    summary="Run drift check and data quality audit",
)
async def check_drift(
    version_id: str,
    payload: MLModelDriftCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        report = await service.run_drift_check(version_id, current_user, payload)
        return MLModelDriftReportResponse(
            id=report.id,
            model_version_id=report.model_version_id,
            dataset_id=report.dataset_id,
            dataset_version_id=report.dataset_version_id,
            drift_detected=report.drift_detected,
            data_drift_score=report.data_drift_score,
            feature_drift_results=report.feature_drift_results,
            prediction_drift_results=report.prediction_drift_results,
            concept_drift_results=report.concept_drift_results,
            data_quality_results=report.data_quality_results,
            recommendation=report.recommendation,
            evaluated_at=report.evaluated_at,
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/versions/{version_id}/health",
    summary="Get multi-dimensional model health indicators",
)
async def get_model_health(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        return await service.get_model_health(version_id, current_user)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/versions/{version_id}/lineage",
    summary="Get model provenance and lineage graph",
)
async def get_model_lineage(
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        return await service.get_model_lineage(version_id, current_user)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/models/{model_id}/compare",
    summary="Compare model versions across metrics, features and parameters",
)
async def compare_model_versions(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        return await service.compare_model_versions(model_id, current_user)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/alerts",
    response_model=MLModelAlertListResponse,
    summary="List all MLOps monitoring alerts",
)
async def list_alerts(
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    unacknowledged_only: bool = Query(False, description="Filter unacknowledged alerts"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    alerts = await service.list_alerts(current_user, model_id=model_id, unacknowledged_only=unacknowledged_only)
    items = [
        MLModelAlertResponse(
            id=a.id,
            model_id=a.model_id,
            model_version_id=a.model_version_id,
            model_name=a.model.name if a.model else None,
            alert_type=a.alert_type,
            severity=a.severity,
            metric_name=a.metric_name,
            observed_value=a.observed_value,
            threshold=a.threshold,
            message=a.message,
            evidence=a.evidence,
            is_acknowledged=a.is_acknowledged,
            created_at=a.created_at,
        )
        for a in alerts
    ]
    return MLModelAlertListResponse(items=items, total=len(items))


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=MLModelAlertResponse,
    summary="Acknowledge a monitoring alert",
)
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = MLOpsService(db)
    try:
        a = await service.acknowledge_alert(alert_id, current_user)
        return MLModelAlertResponse(
            id=a.id,
            model_id=a.model_id,
            model_version_id=a.model_version_id,
            model_name=a.model.name if a.model else None,
            alert_type=a.alert_type,
            severity=a.severity,
            metric_name=a.metric_name,
            observed_value=a.observed_value,
            threshold=a.threshold,
            message=a.message,
            evidence=a.evidence,
            is_acknowledged=a.is_acknowledged,
            created_at=a.created_at,
        )
    except ModelNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
