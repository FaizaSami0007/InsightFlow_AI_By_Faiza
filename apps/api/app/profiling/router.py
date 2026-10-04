from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.user import User
from app.database.session import get_db
from app.datasets.service import get_user_dataset_by_id
from app.datasets.storage import StorageProvider, get_storage_provider
from app.profiling.schemas import (
    AnalyticalQueryRequest,
    AnalyticalQueryResponse,
    DataQualityResponse,
    DatasetProfileResponse,
    SemanticColumnResponse,
    SemanticOverrideRequest,
)
from app.profiling.service import ProfilingService
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/datasets", tags=["Profiling & Analytics"])


def get_profiling_service() -> ProfilingService:
    return ProfilingService()


async def get_verified_dataset_and_version(
    dataset_id: str,
    version_id: str | None,
    user: User,
    db: AsyncSession,
) -> tuple[Dataset, DatasetVersion]:
    """Verify dataset ownership and resolve specific or latest version."""
    try:
        dataset = await get_user_dataset_by_id(db, user.id, dataset_id)
    except PermissionDeniedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found or unauthorized.",
        )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    if version_id:
        version = next((v for v in dataset.versions if v.id == version_id), None)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset version '{version_id}' not found.",
            )
    else:
        if not dataset.versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset has no uploaded versions.",
            )
        version = dataset.versions[0]

    return dataset, version


@router.post(
    "/{dataset_id}/versions/{version_id}/profile",
    response_model=DatasetProfileResponse,
    summary="Trigger or refresh dataset profiling",
)
async def profile_dataset_version(
    dataset_id: str,
    version_id: str,
    force: bool = Query(default=False, description="Force re-profiling even if cached"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    profiling_service: ProfilingService = Depends(get_profiling_service),
    storage: StorageProvider = Depends(get_storage_provider),
) -> DatasetProfileResponse:
    _, version = await get_verified_dataset_and_version(dataset_id, version_id, current_user, db)
    profile = await profiling_service.profile_version(db, version, storage, force_refresh=force)
    return profile  # type: ignore


@router.get(
    "/{dataset_id}/versions/{version_id}/profile",
    response_model=DatasetProfileResponse,
    summary="Get profile for specific dataset version",
)
async def get_version_profile(
    dataset_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    profiling_service: ProfilingService = Depends(get_profiling_service),
    storage: StorageProvider = Depends(get_storage_provider),
) -> DatasetProfileResponse:
    _, version = await get_verified_dataset_and_version(dataset_id, version_id, current_user, db)
    profile = await profiling_service.get_profile(db, version.id)
    if not profile:
        profile = await profiling_service.profile_version(db, version, storage, force_refresh=False)
    return profile  # type: ignore


@router.get(
    "/{dataset_id}/profile",
    response_model=DatasetProfileResponse,
    summary="Get profile for latest dataset version",
)
async def get_latest_dataset_profile(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    profiling_service: ProfilingService = Depends(get_profiling_service),
    storage: StorageProvider = Depends(get_storage_provider),
) -> DatasetProfileResponse:
    _, version = await get_verified_dataset_and_version(dataset_id, None, current_user, db)
    profile = await profiling_service.get_profile(db, version.id)
    if not profile:
        profile = await profiling_service.profile_version(db, version, storage, force_refresh=False)
    return profile  # type: ignore


@router.get(
    "/{dataset_id}/versions/{version_id}/quality",
    response_model=DataQualityResponse,
    summary="Get data quality report",
)
async def get_data_quality_report(
    dataset_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    profiling_service: ProfilingService = Depends(get_profiling_service),
    storage: StorageProvider = Depends(get_storage_provider),
) -> DataQualityResponse:
    _, version = await get_verified_dataset_and_version(dataset_id, version_id, current_user, db)
    profile = await profiling_service.get_profile(db, version.id)
    if not profile or not profile.quality_report:
        profile = await profiling_service.profile_version(db, version, storage)
    if not profile.quality_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quality report unavailable.")
    return profile.quality_report  # type: ignore


@router.get(
    "/{dataset_id}/versions/{version_id}/semantics",
    response_model=List[SemanticColumnResponse],
    summary="Get semantic columns metadata",
)
async def get_semantic_metadata(
    dataset_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    profiling_service: ProfilingService = Depends(get_profiling_service),
    storage: StorageProvider = Depends(get_storage_provider),
) -> List[SemanticColumnResponse]:
    _, version = await get_verified_dataset_and_version(dataset_id, version_id, current_user, db)
    profile = await profiling_service.get_profile(db, version.id)
    if not profile:
        profile = await profiling_service.profile_version(db, version, storage)
    return profile.semantic_columns  # type: ignore


@router.patch(
    "/{dataset_id}/versions/{version_id}/semantics/{column_name}",
    response_model=SemanticColumnResponse,
    summary="Override semantic role or description for a column",
)
async def override_column_semantics(
    dataset_id: str,
    version_id: str,
    column_name: str,
    override: SemanticOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    profiling_service: ProfilingService = Depends(get_profiling_service),
) -> SemanticColumnResponse:
    _, version = await get_verified_dataset_and_version(dataset_id, version_id, current_user, db)
    try:
        updated_sem = await profiling_service.update_semantic_override(db, version.id, column_name, override)
        return updated_sem  # type: ignore
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{dataset_id}/versions/{version_id}/query",
    response_model=AnalyticalQueryResponse,
    summary="Execute safe read-only SQL query in DuckDB",
)
async def execute_analytical_query(
    dataset_id: str,
    version_id: str,
    query_request: AnalyticalQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    profiling_service: ProfilingService = Depends(get_profiling_service),
    storage: StorageProvider = Depends(get_storage_provider),
) -> AnalyticalQueryResponse:
    _, version = await get_verified_dataset_and_version(dataset_id, version_id, current_user, db)
    try:
        return profiling_service.execute_analytical_query(version, storage, query_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Query failed: {str(e)}")
