"""Pydantic schemas for Phase 12 Anomaly Detection & Proactive Insight Intelligence."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.database.models.anomalies import (
    AnomalySeverity,
    AnomalyStatus,
    AnomalyType,
    DetectionMethod,
    InsightType,
)


class RootCauseContributor(BaseModel):
    """Explains measurable sub-dimension contribution to an anomalous period."""

    dimension_field: str = Field(..., description="Name of the categorical attribute (e.g. 'region', 'category')")
    dimension_value: str = Field(..., description="Specific category value (e.g. 'West', 'Electronics')")
    observed_value: float = Field(..., description="Observed subgroup value in anomalous period")
    baseline_value: float = Field(..., description="Expected baseline subgroup value")
    delta: float = Field(..., description="Observed minus expected difference")
    contribution_pct: float = Field(..., description="Percentage of total variation accounted for by this group")
    narrative: str = Field(..., description="Non-causal contribution explanation")


class AnomalyDetectionRequest(BaseModel):
    """Request payload to initiate statistical anomaly detection across a dataset."""

    dataset_id: str = Field(..., description="ID of the dataset to analyze")
    dataset_version_id: Optional[str] = Field(
        None, description="Optional specific version ID; defaults to latest READY"
    )
    metric_fields: Optional[List[str]] = Field(
        default=None, description="Numeric measures to analyze (e.g. ['revenue', 'orders'])"
    )
    time_field: Optional[str] = Field(default=None, description="Date/timestamp column for temporal series analysis")
    dimension_fields: Optional[List[str]] = Field(
        default=None, description="Categorical attributes for subgroup and root-cause analysis"
    )
    method: DetectionMethod = Field(default=DetectionMethod.ROBUST_Z_SCORE, description="Detection methodology")
    sensitivity: float = Field(
        default=3.0, ge=1.0, le=10.0, description="Statistical threshold multiplier (e.g. 2.5, 3.0, 3.5)"
    )
    min_severity: AnomalySeverity = Field(default=AnomalySeverity.LOW, description="Minimum severity to return")
    allow_negative: bool = Field(default=False, description="Whether negative values are valid domain values")
    filters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional filters to slice data")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Target alias
            if "metric_field" in data and "metric_fields" not in data:
                data["metric_fields"] = (
                    [data["metric_field"]] if isinstance(data["metric_field"], str) else data["metric_field"]
                )
            if "target_field" in data and "metric_fields" not in data:
                data["metric_fields"] = [data["target_field"]]
            if "dimension_field" in data and "dimension_fields" not in data:
                data["dimension_fields"] = (
                    [data["dimension_field"]] if isinstance(data["dimension_field"], str) else data["dimension_field"]
                )
            if "method" in data and isinstance(data["method"], str):
                data["method"] = data["method"].upper()
            if "min_severity" in data and isinstance(data["min_severity"], str):
                data["min_severity"] = data["min_severity"].upper()
        return data


class AnomalyPoint(BaseModel):
    """Structured representation of a single detected anomaly."""

    id: str
    dataset_id: str
    dataset_version_id: str
    metric_field: str
    dimension_field: Optional[str] = None
    dimension_value: Optional[str] = None
    period: str
    observed_value: float
    expected_value: float
    deviation: float
    deviation_pct: float
    anomaly_score: float
    severity: AnomalySeverity
    anomaly_type: AnomalyType
    detection_method: DetectionMethod
    status: AnomalyStatus
    root_causes: List[RootCauseContributor] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    dedup_key: str
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightResponse(BaseModel):
    """Structured proactive analytical insight."""

    id: str
    dataset_id: str
    anomaly_id: Optional[str] = None
    insight_type: InsightType
    title: str
    summary: str
    severity: AnomalySeverity
    status: AnomalyStatus
    evidence: Dict[str, Any] = Field(default_factory=dict)
    dedup_key: str
    feedback: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyDetectionResponse(BaseModel):
    """Complete anomaly analysis response including summary metrics and insights."""

    dataset_id: str
    dataset_version_id: str
    anomalies: List[AnomalyPoint]
    insights: List[InsightResponse]
    total_anomalies_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    execution_time_ms: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    dataset_id: str
    dataset_version_id: str
    anomalies: List[AnomalyPoint]
    insights: List[InsightResponse]
    total_anomalies_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    execution_time_ms: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyListResponse(BaseModel):
    """Paginated or listed anomalies response."""

    items: List[AnomalyPoint]
    total: int


class InsightListResponse(BaseModel):
    """Paginated or listed insights response."""

    items: List[InsightResponse]
    total: int


class AnomalyStatusUpdateRequest(BaseModel):
    """Update lifecycle status of an anomaly alert or insight."""

    status: AnomalyStatus = Field(..., description="New status ('ACKNOWLEDGED', 'DISMISSED', 'RESOLVED')")


class AnomalyFeedbackRequest(BaseModel):
    """User feedback on insight usefulness."""

    feedback: str = Field(..., description="'useful', 'not_useful', or 'expected_behavior'")
