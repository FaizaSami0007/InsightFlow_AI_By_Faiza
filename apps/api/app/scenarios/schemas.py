"""Pydantic schemas for Phase 13 Decision Intelligence & Scenario Simulation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.database.models.scenarios import (
    AssumptionOperation,
    ScenarioStatus,
    ScenarioType,
)


class AssumptionSpec(BaseModel):
    """Structured analytical assumption modifying a specific baseline driver."""

    variable: str = Field(..., description="Target driver or feature column name (e.g. 'price', 'quantity')")
    operation: AssumptionOperation = Field(
        default=AssumptionOperation.PERCENTAGE_CHANGE,
        description="Type of transformation to apply",
    )
    value: float = Field(..., description="Numeric value or delta modifier (e.g. 10.0 for +10%)")
    unit: Optional[str] = Field(default="%", description="Unit descriptor (e.g. '%', '$', 'units')")
    min_bound: Optional[float] = Field(default=None, description="Optional lower physical/domain boundary")
    max_bound: Optional[float] = Field(default=None, description="Optional upper physical/domain boundary")
    is_non_negative: bool = Field(default=True, description="Enforce non-negative constraint on simulated variable")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "field" in data and "variable" not in data:
                data["variable"] = data["field"]
            if "operation" in data and isinstance(data["operation"], str):
                data["operation"] = data["operation"].upper()
                if data["operation"] in ["PERCENTAGE", "PCT", "PERCENT", "SENSITIVITY_SWEEP", "SWEEP"]:
                    data["operation"] = "PERCENTAGE_CHANGE"
                elif data["operation"] in ["ABSOLUTE", "DELTA", "ADD"]:
                    data["operation"] = "ABSOLUTE_CHANGE"
                elif data["operation"] in ["SET", "EXACT"]:
                    data["operation"] = "DIRECT_SET"
        return data


class WhatIfScenarioRequest(BaseModel):
    """Request payload to simulate a single or multi-variable what-if scenario."""

    dataset_id: str = Field(..., description="ID of the dataset to analyze")
    dataset_version_id: Optional[str] = Field(None, description="Specific version ID; defaults to latest READY")
    name: Optional[str] = Field(None, description="User-friendly scenario name")
    description: Optional[str] = Field(None, description="Scenario description or rationale")
    target_metric: str = Field(..., description="Primary output measure to evaluate (e.g. 'revenue', 'profit')")
    time_field: Optional[str] = Field(None, description="Optional date/time column for temporal simulation")
    assumptions: List[AssumptionSpec] = Field(..., min_length=1, description="List of structured assumptions")
    filters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional filters to slice baseline")
    baseline_source: str = Field(default="HISTORICAL_AGGREGATE", description="Baseline data source")


class SensitivityAnalysisRequest(BaseModel):
    """Request payload to compute sensitivity sweeps across a spectrum of variable modifications."""

    dataset_id: str = Field(..., description="ID of the dataset to analyze")
    dataset_version_id: Optional[str] = Field(None, description="Specific version ID; defaults to latest READY")
    name: Optional[str] = Field(None, description="Sensitivity analysis title")
    target_metric: str = Field(..., description="Output metric to measure sensitivity against")
    variable: str = Field(..., description="Driver variable to vary across the sensitivity range")
    range_min_pct: float = Field(default=-20.0, description="Minimum percentage variation (e.g. -20%)")
    range_max_pct: float = Field(default=20.0, description="Maximum percentage variation (e.g. +20%)")
    step_pct: float = Field(default=5.0, gt=0, description="Step increment percentage (e.g. 5%)")
    max_scenarios: int = Field(default=25, ge=1, le=50, description="Safety limit on generated scenario steps")
    filters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional data filters")


class ScenarioComparisonRequest(BaseModel):
    """Request payload to simulate and compare side-by-side scenarios (e.g. Optimistic vs Conservative)."""

    dataset_id: str = Field(..., description="ID of the dataset to analyze")
    dataset_version_id: Optional[str] = Field(None, description="Specific version ID")
    name: Optional[str] = Field(None, description="Comparison title")
    target_metric: str = Field(..., description="Target outcome metric")
    scenarios: Dict[str, List[AssumptionSpec]] = Field(
        ...,
        description="Named scenario dictionary (e.g. {'Optimistic': [...], 'Conservative': [...]})",
    )
    filters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional filters")


class SensitivityStep(BaseModel):
    """Single evaluated step in a sensitivity analysis."""

    variation_pct: float
    variable_value: float
    simulated_target: float
    absolute_change: float
    percentage_change: Optional[float] = None


class ScenarioComparisonItem(BaseModel):
    """Result for one branch in a multi-scenario comparison."""

    scenario_name: str
    simulated_value: float
    absolute_change: float
    percentage_change: Optional[float] = None
    assumptions_summary: str


class ScenarioResultResponse(BaseModel):
    """Complete structured response for a validated decision scenario simulation."""

    id: str
    name: str
    description: Optional[str] = None
    scenario_type: ScenarioType
    status: ScenarioStatus
    dataset_id: str
    dataset_version_id: str
    target_metric: str
    baseline_source: str
    baseline_value: float
    scenario_value: float
    absolute_change: float
    percentage_change: Optional[float] = None
    assumptions: List[AssumptionSpec]
    sensitivity_results: Optional[List[SensitivityStep]] = None
    comparison_scenarios: Optional[List[ScenarioComparisonItem]] = None
    engine_version: str
    provenance: Dict[str, Any] = Field(default_factory=dict)
    narrative: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScenarioListResponse(BaseModel):
    """Paginated or listed scenarios response."""

    items: List[ScenarioResultResponse]
    total: int
