from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.dataset import DatasetStatus, FileFormat


class DatasetVersionResponse(BaseModel):
    """Metadata response for a specific physical version of a dataset."""

    id: str
    dataset_id: str
    version_number: int
    file_name: str
    file_format: FileFormat
    file_size: int
    checksum: str
    status: DatasetStatus
    row_count: Optional[int]
    column_count: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetResponse(BaseModel):
    """Summary response for a dataset including its latest active version."""

    id: str
    name: str
    description: Optional[str]
    status: DatasetStatus
    created_at: datetime
    updated_at: datetime
    version_count: int = 1
    latest_version: Optional[DatasetVersionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetDetailResponse(BaseModel):
    """Full detail response including complete version history."""

    id: str
    name: str
    description: Optional[str]
    status: DatasetStatus
    created_at: datetime
    updated_at: datetime
    versions: List[DatasetVersionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DatasetListResponse(BaseModel):
    """Paginated list envelope for datasets."""

    items: List[DatasetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
