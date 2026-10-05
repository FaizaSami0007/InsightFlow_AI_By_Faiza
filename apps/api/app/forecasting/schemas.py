"""Pydantic schemas for Phase 11 Predictive Analytics & Time-Series Forecasting."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.database.models.forecasting import ForecastModelType, ForecastStatus


class ForecastRunRequest(BaseModel):
    """Request payload to initiate a validated time-series forecast."""

    dataset_id: str = Field(..., description="ID of the dataset to forecast")
    dataset_version_id: Optional[str] = Field(None, description="Optional specific version ID; defaults to latest READY")
    target_field: str = Field(..., description="Numeric column name to predict (e.g. 'revenue', 'orders')")
    time_field: str = Field(..., description="Date/timestamp column name (e.g. 'order_date')")
    frequency: Optional[str] = Field(None, description="Optional frequency ('D', 'W', 'M', 'Q', 'Y'); auto-detected if omitted")
    forecast_horizon: int = Field(default=6, ge=1, le=100, description="Number of future periods to forecast")
    confidence_level: float = Field(default=0.95, ge=0.50, le=0.99, description="Prediction interval confidence (e.g. 0.80, 0.90, 0.95)")
    model_type: ForecastModelType = Field(default=ForecastModelType.AUTO, description="Preferred algorithm or AUTO for backtested selection")
    allow_negative: bool = Field(default=False, description="Whether negative predictions are valid for this target")
    filters: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional filters to slice the time-series before fitting")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases_and_case(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Target alias
            if "target_column" in data and "target_field" not in data:
                data["target_field"] = data["target_column"]
            # Time alias
            if "time_column" in data and "time_field" not in data:
                data["time_field"] = data["time_column"]
            # Case insensitive model_type
            if "model_type" in data and isinstance(data["model_type"], str):
                data["model_type"] = data["model_type"].upper()
        return data


class ForecastPoint(BaseModel):
    """Single point forecast with prediction bounds."""

    date: str
    forecast: float
    lower: float
    upper: float


class HistoricalPoint(BaseModel):
    """Single historical actual observation."""

    date: str
    actual: float


class ForecastMetrics(BaseModel):
    """Backtesting and evaluation metrics comparing against historical holdouts."""

    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    mape: float = Field(..., description="Mean Absolute Percentage Error (%)")
    smape: float = Field(..., description="Symmetric Mean Absolute Percentage Error (%)")
    baseline_mae: float = Field(..., description="MAE of the Naive / Seasonal Naive baseline")
    relative_improvement_pct: float = Field(..., description="Percentage improvement over baseline (higher is better)")


class ForecastDiagnostics(BaseModel):
    """Explainable statistical diagnostics and fitted parameters."""

    frequency_detected: str
    observations_count: int
    missing_periods_imputed: int = 0
    outliers_detected: int = 0
    seasonality_detected: bool = False
    seasonality_period: Optional[int] = None
    stationarity_is_stationary: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)
    transformations: List[str] = Field(default_factory=list)


class ForecastResponse(BaseModel):
    """Complete validated forecast result with historical context, prediction intervals, and provenance."""

    id: str
    dataset_id: str
    dataset_version_id: str
    target_field: str
    time_field: str
    frequency: str
    forecast_horizon: int
    confidence_level: float
    requested_model_type: ForecastModelType
    selected_model_name: str
    status: ForecastStatus
    metrics: ForecastMetrics
    predictions: List[ForecastPoint]
    historical_points: List[HistoricalPoint]
    diagnostics: ForecastDiagnostics
    provenance: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForecastListResponse(BaseModel):
    """List of forecast execution summaries."""

    items: List[ForecastResponse]
    total: int
