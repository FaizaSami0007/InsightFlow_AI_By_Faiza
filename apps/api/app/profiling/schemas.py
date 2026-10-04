from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.database.models.profiling import ConceptualType, ProfileStatus, SemanticRole


class ColumnProfileResponse(BaseModel):
    id: str
    column_name: str
    normalized_name: str
    ordinal_position: int
    data_type: str
    conceptual_type: ConceptualType
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    is_constant: bool
    is_near_constant: bool
    numeric_stats: Optional[Dict[str, Any]] = None
    categorical_stats: Optional[Dict[str, Any]] = None
    temporal_stats: Optional[Dict[str, Any]] = None
    boolean_stats: Optional[Dict[str, Any]] = None
    outlier_count: int
    outlier_percentage: float

    model_config = {"from_attributes": True}


class DataQualityResponse(BaseModel):
    id: str
    overall_score: float
    grade: str
    total_issues: int
    missing_summary: Dict[str, Any]
    duplicate_summary: Dict[str, Any]
    constant_columns: List[str]
    outlier_summary: Dict[str, Any]
    warnings: List[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class SemanticColumnResponse(BaseModel):
    id: str
    column_name: str
    inferred_role: SemanticRole
    inferred_confidence: float
    user_role: Optional[SemanticRole] = None
    is_dimension: bool
    is_measure: bool
    is_identifier: bool
    is_temporal: bool
    possible_currency: bool
    description: Optional[str] = None
    unit: Optional[str] = None
    format_hint: Optional[str] = None

    model_config = {"from_attributes": True}


class DatasetProfileResponse(BaseModel):
    id: str
    dataset_version_id: str
    status: ProfileStatus
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    memory_size_bytes: Optional[int] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    column_profiles: List[ColumnProfileResponse] = Field(default_factory=list)
    quality_report: Optional[DataQualityResponse] = None
    semantic_columns: List[SemanticColumnResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SemanticOverrideRequest(BaseModel):
    user_role: Optional[SemanticRole] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    format_hint: Optional[str] = None


class AnalyticalQueryRequest(BaseModel):
    query: str = Field(..., min_length=5, description="Safe SQL SELECT query")
    parameters: Optional[List[Any]] = Field(default=None, description="Optional parameter list")
    max_rows: Optional[int] = Field(default=100, le=1000, description="Max rows to return (capped at 1000)")


class AnalyticalQueryResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float
    metadata: Dict[str, Any]
