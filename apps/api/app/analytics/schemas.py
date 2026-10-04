from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field

from app.analytics.engine.contracts import (
    AnalysisProvenance,
    AnalysisToolMetadata,
    FilterCondition,
    FilterGroup,
    SortSpecification,
)


class AnalysisRunRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    operation: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    filters: Optional[Union[FilterGroup, FilterCondition, dict[str, Any]]] = None
    sort_by: Optional[List[SortSpecification]] = None
    limit: Optional[int] = Field(default=1000, ge=1, le=10000)
    offset: Optional[int] = Field(default=0, ge=0)


class AnalysisResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    dataset_version_id: str
    operation: str
    status: str
    columns: List[str] = Field(default_factory=list)
    rows: List[dict[str, Any]] = Field(default_factory=list)
    summary: Optional[dict[str, Any]] = None
    execution_time_ms: float = 0.0
    row_count: int = 0
    provenance: Optional[AnalysisProvenance] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class AnalysisHistoryItem(BaseModel):
    id: str
    dataset_id: str
    dataset_version_id: str
    operation: str
    status: str
    execution_time_ms: Optional[float] = None
    row_count: Optional[int] = None
    created_at: datetime
    error_message: Optional[str] = None


class AnalysisToolsResponse(BaseModel):
    tools: List[AnalysisToolMetadata]
