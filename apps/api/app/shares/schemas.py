"""Pydantic schemas for Dashboard Sharing."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ShareCreateRequest(BaseModel):
    expires_in_days: Optional[int] = Field(
        default=None, ge=1, le=365, description="Number of days until share link expires (null = no expiration)"
    )
    is_snapshot: bool = Field(
        default=False, description="Whether to freeze and store a static snapshot of current dashboard data"
    )
    allowed_filters: List[str] = Field(
        default_factory=list, description="List of filter column names that shared viewers are allowed to use"
    )


class ShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dashboard_id: str
    owner_id: str
    share_token: str
    share_url: str = ""
    access_type: str = "read_only"
    is_active: bool
    is_snapshot: bool
    allowed_filters: List[str] = Field(default_factory=list)
    view_count: int = 0
    last_accessed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ShareListResponse(BaseModel):
    items: List[ShareResponse]
    total: int


class SharedDashboardViewResponse(BaseModel):
    share_token: str
    dashboard_id: str
    title: str
    description: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    is_snapshot: bool
    status: str
    theme: str
    layout_type: str
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    widgets: List[Dict[str, Any]] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    allowed_filters: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SharedFilterRefreshRequest(BaseModel):
    filter_values: Dict[str, Any] = Field(
        default_factory=dict, description="Temporary session filter values selected by the viewer"
    )
