import math
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.logging import logger
from app.database.models.dataset import Dataset, DatasetStatus, DatasetVersion
from app.database.models.user import User
from app.datasets.schemas import DatasetListResponse, DatasetResponse, DatasetVersionResponse
from app.datasets.storage import get_storage_provider
from app.datasets.validator import validate_dataset_file


async def create_dataset_with_file(
    session: AsyncSession,
    user: User,
    file_bytes: bytes,
    original_filename: str,
    name: str,
    description: Optional[str] = None,
) -> Dataset:
    """Validate file, store on disk, and create Dataset + Version 1 records transactionally."""
    # 1. Validate file format and structure
    validation_info = validate_dataset_file(file_bytes, original_filename)
    storage = get_storage_provider()

    # 2. Save physical file to storage
    storage_ref = storage.save_file(file_bytes, original_filename)

    try:
        # 3. Create Dataset header record
        dataset = Dataset(
            owner_id=user.id,
            name=name.strip(),
            description=description.strip() if description else None,
            status=DatasetStatus.READY,
        )
        session.add(dataset)
        await session.flush()  # Flush to obtain generated dataset.id

        # 4. Create initial DatasetVersion record (v1)
        version = DatasetVersion(
            dataset_id=dataset.id,
            version_number=1,
            file_name=original_filename,
            file_format=validation_info.file_format,
            file_size=validation_info.file_size,
            storage_reference=storage_ref,
            checksum=validation_info.checksum,
            status=DatasetStatus.READY,
            row_count=validation_info.row_count,
            column_count=validation_info.column_count,
        )
        session.add(version)
        await session.commit()
        await session.refresh(dataset)
        logger.info(f"Created dataset '{dataset.name}' (id={dataset.id}) with version 1")
        return dataset
    except Exception as exc:
        await session.rollback()
        # Clean up stored file to prevent orphan disk storage
        storage.delete_file(storage_ref)
        logger.error(f"Database error while saving dataset, cleaned up file {storage_ref}: {exc}")
        raise


async def create_dataset_version(
    session: AsyncSession,
    user: User,
    dataset_id: str,
    file_bytes: bytes,
    original_filename: str,
) -> DatasetVersion:
    """Validate file and add a new incremented version to an existing dataset."""
    dataset = await get_user_dataset_by_id(session, user.id, dataset_id)
    if not dataset:
        raise NotFoundError("Dataset not found or access denied", details={"dataset_id": dataset_id})

    validation_info = validate_dataset_file(file_bytes, original_filename)
    storage = get_storage_provider()
    storage_ref = storage.save_file(file_bytes, original_filename)

    try:
        # Determine next version number
        max_version_stmt = select(func.max(DatasetVersion.version_number)).where(
            DatasetVersion.dataset_id == dataset_id
        )
        max_ver_result = await session.execute(max_version_stmt)
        current_max = max_ver_result.scalar() or 0
        next_version = current_max + 1

        version = DatasetVersion(
            dataset_id=dataset.id,
            version_number=next_version,
            file_name=original_filename,
            file_format=validation_info.file_format,
            file_size=validation_info.file_size,
            storage_reference=storage_ref,
            checksum=validation_info.checksum,
            status=DatasetStatus.READY,
            row_count=validation_info.row_count,
            column_count=validation_info.column_count,
        )
        session.add(version)
        dataset.status = DatasetStatus.READY
        await session.commit()
        await session.refresh(version)
        logger.info(f"Created version {next_version} for dataset {dataset_id}")
        return version
    except Exception as exc:
        await session.rollback()
        storage.delete_file(storage_ref)
        logger.error(f"Error creating dataset version, cleaned up file {storage_ref}: {exc}")
        raise


async def get_user_datasets(
    session: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> DatasetListResponse:
    """Retrieve paginated datasets owned by user."""
    safe_page = max(1, page)
    safe_page_size = min(100, max(1, page_size))
    offset = (safe_page - 1) * safe_page_size

    # Total count query
    count_stmt = select(func.count(Dataset.id)).where(Dataset.owner_id == user_id)
    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    # Paginated entities with eager loading
    stmt = (
        select(Dataset)
        .where(Dataset.owner_id == user_id)
        .options(selectinload(Dataset.versions))
        .order_by(Dataset.updated_at.desc())
        .offset(offset)
        .limit(safe_page_size)
    )
    result = await session.execute(stmt)
    datasets = result.scalars().all()

    items: List[DatasetResponse] = []
    for d in datasets:
        latest = d.versions[0] if d.versions else None
        items.append(
            DatasetResponse(
                id=d.id,
                name=d.name,
                description=d.description,
                status=d.status,
                created_at=d.created_at,
                updated_at=d.updated_at,
                version_count=len(d.versions),
                latest_version=DatasetVersionResponse.model_validate(latest) if latest else None,
            )
        )

    total_pages = math.ceil(total / safe_page_size) if total > 0 else 1

    return DatasetListResponse(
        items=items,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
        total_pages=total_pages,
    )


async def get_user_dataset_by_id(
    session: AsyncSession,
    user_id: str,
    dataset_id: str,
) -> Optional[Dataset]:
    """Retrieve single dataset ensuring ownership isolation."""
    stmt = select(Dataset).where(Dataset.id == dataset_id).options(selectinload(Dataset.versions))
    result = await session.execute(stmt)
    dataset = result.scalar_one_or_none()

    if not dataset:
        return None

    if dataset.owner_id != user_id:
        # Enforce server-side ownership isolation: return None or raise PermissionDenied
        raise PermissionDeniedError("You do not have permission to access this dataset.")

    return dataset


async def get_dataset_versions(
    session: AsyncSession,
    user_id: str,
    dataset_id: str,
) -> List[DatasetVersion]:
    """Retrieve full version history for a user's dataset."""
    dataset = await get_user_dataset_by_id(session, user_id, dataset_id)
    if not dataset:
        raise NotFoundError("Dataset not found", details={"dataset_id": dataset_id})

    stmt = (
        select(DatasetVersion)
        .where(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_dataset_file_for_download(
    session: AsyncSession,
    user_id: str,
    dataset_id: str,
    version_number: Optional[int] = None,
) -> Tuple[DatasetVersion, Path]:
    """Verify ownership and return version metadata and physical file path."""
    dataset = await get_user_dataset_by_id(session, user_id, dataset_id)
    if not dataset:
        raise NotFoundError("Dataset not found", details={"dataset_id": dataset_id})

    if version_number is not None:
        stmt = select(DatasetVersion).where(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.version_number == version_number,
        )
    else:
        # Default to latest version
        stmt = (
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version_number.desc())
            .limit(1)
        )

    result = await session.execute(stmt)
    version = result.scalar_one_or_none()
    if not version:
        raise NotFoundError("Dataset version not found", details={"version_number": version_number})

    storage = get_storage_provider()
    file_path = storage.get_file_path(version.storage_reference)
    return version, file_path
