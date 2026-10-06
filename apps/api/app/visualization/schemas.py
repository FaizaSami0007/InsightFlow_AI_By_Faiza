"""Pydantic schemas and specifications for the deterministic visualization intelligence layer."""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ChartType(str, enum.Enum):
    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOXPLOT = "boxplot"
    KPI = "kpi"
    TABLE = "table"


class NumberFormat(str, enum.Enum):
    INTEGER = "integer"
    DECIMAL = "decimal"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    COMPACT = "compact"


class AxisDataType(str, enum.Enum):
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"


class AxisConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    column: str = Field(..., description="Column name mapped to axis")
    label: Optional[str] = Field(None, description="Human readable axis title")
    data_type: AxisDataType = Field(AxisDataType.CATEGORICAL, description="Data type of mapped column")
    format: Optional[NumberFormat] = Field(None, description="Display formatting for values")


class VisualizationProvenance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    analysis_id: str = Field(..., description="Analysis Job ID that generated the data")
    dataset_id: str = Field(..., description="Dataset ID")
    dataset_version_id: str = Field(..., description="Dataset Version ID")
    operation: str = Field(..., description="Deterministic analytical operation")
    row_count: int = Field(0, description="Row count of the visualized result")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VisualizationSpec(BaseModel):
    """
    Complete, validated specification for deterministic chart rendering.
    LLMs or rules may propose specifications, but they MUST pass validation before rendering.
    """

    model_config = ConfigDict(extra="ignore")

    chart_type: ChartType = Field(..., description="Type of chart to render")
    title: str = Field(..., description="Human-readable chart title")
    subtitle: Optional[str] = Field(None, description="Optional dataset/provenance subtitle")

    x_axis: Optional[str] = Field(None, description="Column name for X axis")
    y_axis: Optional[Union[str, List[str]]] = Field(None, description="Column name(s) for Y axis / measures")
    series: Optional[str] = Field(None, description="Column name for grouping or color series")

    sort: Optional[str] = Field(None, description="Sort direction: asc, desc, or none")
    limit: Optional[int] = Field(None, description="Limit for visible categories")
    format: Optional[str] = Field(None, description="Default number/date format")
    cardinality: Optional[int] = Field(None, description="Number of distinct categories in result")

    options: Dict[str, Any] = Field(default_factory=dict, description="Chart-specific rendering options")
    provenance: Optional[VisualizationProvenance] = Field(None, description="Traceability provenance")
    explanation: Optional[str] = Field(None, description="Why this visualization was recommended")

    is_fallback: bool = Field(False, description="True if this is a fallback due to an invalid request")
    available_chart_types: List[ChartType] = Field(
        default_factory=list, description="Compatible alternate chart types the user can switch to"
    )


class VisualizationRecommendRequest(BaseModel):
    analysis_id: str = Field(..., description="Analysis Job ID to generate visualization for")
    preferred_chart_type: Optional[ChartType] = Field(None, description="User or AI requested chart type override")
    intent: Optional[str] = Field(None, description="Natural language visual intent")


class VisualizationValidateRequest(BaseModel):
    analysis_id: str = Field(..., description="Analysis Job ID containing source analytical result")
    spec: VisualizationSpec = Field(..., description="Candidate visualization specification to validate")


class VisualizationValidationResult(BaseModel):
    valid: bool = Field(..., description="Whether the specification is strictly valid")
    errors: List[str] = Field(default_factory=list, description="Validation failure reasons")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking recommendations or warnings")
    validated_spec: Optional[VisualizationSpec] = Field(None, description="Validated, sanitized specification")
    fallback_spec: Optional[VisualizationSpec] = Field(None, description="Safe fallback specification if invalid")


class ChartTypeMetadata(BaseModel):
    chart_type: ChartType
    label: str
    description: str
    required_axes: List[str]
    max_cardinality: Optional[int] = None
    min_values: Optional[int] = None
    supports_series: bool = False
