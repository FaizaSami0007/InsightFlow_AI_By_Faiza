"""Pydantic schemas and contracts for the deterministic Dashboard Intelligence engine."""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.visualization.schemas import ChartType, VisualizationSpec


class WidgetType(str, enum.Enum):
    KPI = "kpi"
    CHART = "chart"
    TABLE = "table"


class PatchOp(str, enum.Enum):
    ADD_WIDGET = "ADD_WIDGET"
    REMOVE_WIDGET = "REMOVE_WIDGET"
    MOVE_WIDGET = "MOVE_WIDGET"
    RESIZE_WIDGET = "RESIZE_WIDGET"
    CHANGE_CHART = "CHANGE_CHART"
    CHANGE_METRIC = "CHANGE_METRIC"
    CHANGE_FILTER = "CHANGE_FILTER"
    RENAME_DASHBOARD = "RENAME_DASHBOARD"


class LayoutPosition(BaseModel):
    model_config = ConfigDict(extra="ignore")
    x: int = Field(..., ge=0, le=11, description="Grid X coordinate (0-11)")
    y: int = Field(..., ge=0, description="Grid Y coordinate (>=0)")
    w: int = Field(..., ge=1, le=12, description="Grid width in columns (1-12)")
    h: int = Field(..., ge=1, le=24, description="Grid height in rows (1-24)")


class DashboardWidgetPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: Optional[str] = Field(None, description="Client or planned widget identifier")
    title: str = Field(..., description="Human-readable widget title")
    description: Optional[str] = Field(None, description="Widget analytical description")
    widget_type: WidgetType = Field(WidgetType.CHART, description="Type of widget (kpi, chart, table)")
    operation: str = Field(..., description="Analytics tool operation name (e.g. group_by, describe_dataset)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Deterministic analytics parameters")
    preferred_chart_type: Optional[ChartType] = Field(None, description="Preferred chart type")
    grid_w: Optional[int] = Field(None, ge=1, le=12, description="Planned width in 12-col grid")
    grid_h: Optional[int] = Field(None, ge=1, le=24, description="Planned height in rows")


class DashboardPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = Field(..., description="Proposed dashboard title")
    purpose: str = Field(..., description="Specific analytical purpose")
    dataset_id: str = Field(..., description="Target dataset ID")
    dataset_version_id: str = Field(..., description="Target dataset version ID")
    widgets: List[DashboardWidgetPlan] = Field(..., min_length=1, max_length=12, description="Planned widgets")
    suggested_filters: List[str] = Field(default_factory=list, description="Suggested categorical or temporal filter fields")
    reasoning_summary: Optional[str] = Field(None, description="User-safe rationale for composition")


class DashboardPatch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    op: PatchOp = Field(..., description="Patch operation type")
    widget_id: Optional[str] = Field(None, description="Target widget ID if modifying widget")
    filter_id: Optional[str] = Field(None, description="Target filter ID if modifying filter")
    params: Dict[str, Any] = Field(default_factory=dict, description="Modification parameters")


class DashboardFilterSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")
    column_name: str
    display_name: str
    filter_type: str = "categorical"  # categorical, temporal, numeric
    operator: str = "eq"
    current_value: Optional[Any] = None
    allowed_values: Optional[List[Any]] = None
    scope: str = "global"  # global or widget
    target_widget_ids: List[str] = Field(default_factory=list)


class DashboardFilterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: str
    dashboard_id: str
    column_name: str
    display_name: str
    filter_type: str
    operator: str
    current_value: Optional[Any] = None
    allowed_values: Optional[List[Any]] = None
    scope: str
    target_widget_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DashboardWidgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: str
    dashboard_id: str
    analysis_id: Optional[str] = None
    widget_type: str
    title: str
    description: Optional[str] = None
    chart_spec: Optional[VisualizationSpec] = None
    grid_x: int
    grid_y: int
    grid_w: int
    grid_h: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    analysis_status: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: str
    name: str
    description: Optional[str] = None
    dataset_id: str
    dataset_name: Optional[str] = None
    dataset_version_id: str
    dataset_version_num: Optional[int] = None
    user_id: str
    status: str
    theme: str
    layout_type: str
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    widgets: List[DashboardWidgetResponse] = Field(default_factory=list)
    filters: List[DashboardFilterResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DashboardGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dataset_id: str = Field(..., description="Dataset ID to generate dashboard for")
    dataset_version_id: str = Field(..., description="Dataset Version ID")
    purpose: Optional[str] = Field(None, description="Analytical purpose preset (e.g. sales, operations, overview)")
    intent: Optional[str] = Field(None, description="Natural language intent for dashboard composition")
    min_widgets: int = Field(3, ge=1, le=12, description="Minimum widget count")
    max_widgets: int = Field(8, ge=1, le=12, description="Maximum widget count")


class DashboardCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(..., min_length=1, max_length=255)
    dataset_id: str
    dataset_version_id: str
    description: Optional[str] = None
    theme: str = "default"


class DashboardUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None


class DashboardApplyPatchesRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    patches: List[DashboardPatch] = Field(..., min_length=1)


class DashboardRefineRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    instruction: str = Field(..., min_length=2, description="Natural language dashboard modification prompt")


class DashboardQualityReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Explainable quality score (0-100)")
    valid_widget_ratio: float = Field(..., description="Percentage of widgets successfully rendered")
    visual_diversity_score: float = Field(..., description="Variety of visualization types used")
    redundancy_penalty: float = Field(..., description="Penalty for duplicate or near-identical widgets")
    data_coverage_score: float = Field(..., description="Coverage of measures and key dimensions")
    breakdown: Dict[str, Any] = Field(default_factory=dict)
