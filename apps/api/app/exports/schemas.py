"""Pydantic schemas for Dashboard Exports."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.exports import ExportFormat


class ExportRequest(BaseModel):
    format: ExportFormat = Field(default=ExportFormat.PDF, description="Export file format: pdf, png, csv, json")
    page_size: str = Field(default="A4", description="Page size for PDF: A4, Letter")
    orientation: str = Field(default="landscape", description="Orientation for PDF/PNG: landscape, portrait")
    include_provenance: bool = Field(default=True, description="Whether to include analytical provenance in export")
    include_filters: bool = Field(default=True, description="Whether to include active filter criteria in export")
    title_override: Optional[str] = Field(default=None, description="Optional custom title for the generated report")
    filter_values: Optional[Dict[str, Any]] = Field(default=None, description="Active dashboard filter values")
    widget_id: Optional[str] = Field(default=None, description="Optional target widget ID for single-widget CSV export")


class ExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dashboard_id: str
    user_id: str
    format: str
    status: str
    title: str
    file_size_bytes: Optional[int] = None
    content_type: str
    filter_snapshot: Dict[str, Any] = Field(default_factory=dict)
    metadata_snapshot: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    download_url: str = ""
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ExportListResponse(BaseModel):
    items: List[ExportResponse]
    total: int
