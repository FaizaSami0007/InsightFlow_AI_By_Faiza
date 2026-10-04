from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database.models.user import User
from app.database.session import get_db
from app.datasets.schemas import (
    DatasetDetailResponse,
    DatasetListResponse,
    DatasetResponse,
    DatasetVersionResponse,
)
from app.datasets.service import (
    create_dataset_version,
    create_dataset_with_file,
    get_dataset_file_for_download,
    get_dataset_versions,
    get_user_dataset_by_id,
    get_user_datasets,
)
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post(
    "",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and register a new dataset",
)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(..., min_length=1, max_length=255),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Upload a CSV or Parquet file to create a new versioned dataset."""
    file_bytes = await file.read()
    filename = file.filename or "dataset.csv"

    dataset = await create_dataset_with_file(
        session=session,
        user=current_user,
        file_bytes=file_bytes,
        original_filename=filename,
        name=name,
        description=description,
    )

    latest = dataset.versions[0] if dataset.versions else None

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        status=dataset.status,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        version_count=len(dataset.versions),
        latest_version=DatasetVersionResponse.model_validate(latest) if latest else None,
    )


@router.post(
    "/{dataset_id}/versions",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new version for an existing dataset",
)
async def upload_version(
    dataset_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DatasetVersionResponse:
    """Upload a replacement CSV/Parquet file incrementing the dataset version number."""
    file_bytes = await file.read()
    filename = file.filename or "dataset.csv"

    version = await create_dataset_version(
        session=session,
        user=current_user,
        dataset_id=dataset_id,
        file_bytes=file_bytes,
        original_filename=filename,
    )

    return DatasetVersionResponse.model_validate(version)


@router.get("", response_model=DatasetListResponse, summary="List current user's datasets")
async def list_datasets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DatasetListResponse:
    """Retrieve a paginated list of datasets owned by the current user."""
    return await get_user_datasets(session, current_user.id, page=page, page_size=page_size)


@router.get("/{dataset_id}", response_model=DatasetDetailResponse, summary="Get dataset details")
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DatasetDetailResponse:
    """Retrieve metadata and full version history for a specific dataset."""
    dataset = await get_user_dataset_by_id(session, current_user.id, dataset_id)
    if not dataset:
        raise NotFoundError("Dataset not found", details={"dataset_id": dataset_id})

    return DatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        status=dataset.status,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        versions=[DatasetVersionResponse.model_validate(v) for v in dataset.versions],
    )


@router.get(
    "/{dataset_id}/versions", response_model=List[DatasetVersionResponse], summary="List dataset version history"
)
async def list_versions(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[DatasetVersionResponse]:
    """Retrieve immutable version records for a dataset."""
    versions = await get_dataset_versions(session, current_user.id, dataset_id)
    return [DatasetVersionResponse.model_validate(v) for v in versions]


@router.get("/{dataset_id}/download", summary="Download dataset file")
async def download_dataset(
    dataset_id: str,
    version: Optional[int] = Query(None, description="Optional version number (defaults to latest)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download the physical CSV or Parquet file for a dataset version."""
    version_record, file_path = await get_dataset_file_for_download(
        session=session,
        user_id=current_user.id,
        dataset_id=dataset_id,
        version_number=version,
    )

    media_type = "text/csv" if version_record.file_format == "CSV" else "application/octet-stream"
    return FileResponse(
        path=str(file_path),
        filename=version_record.file_name,
        media_type=media_type,
    )
