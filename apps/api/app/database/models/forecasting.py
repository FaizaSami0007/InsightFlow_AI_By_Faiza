"""SQLAlchemy database models for Phase 11 Predictive Analytics & Time-Series Forecasting."""

import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.database.models.dataset import Dataset, DatasetVersion
    from app.database.models.user import User


class ForecastStatus(str, enum.Enum):
    """Lifecycle state of a forecasting task."""

    PENDING = "PENDING"
    TRAINING = "TRAINING"
    VALIDATING = "VALIDATING"
    FORECASTING = "FORECASTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STALE = "STALE"


class ForecastModelType(str, enum.Enum):
    """Supported forecasting algorithm families."""

    AUTO = "AUTO"
    NAIVE = "NAIVE"
    SEASONAL_NAIVE = "SEASONAL_NAIVE"
    MOVING_AVERAGE = "MOVING_AVERAGE"
    EXPONENTIAL_SMOOTHING = "EXPONENTIAL_SMOOTHING"
    ARIMA = "ARIMA"
    SARIMA = "SARIMA"


class ForecastExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores the execution metadata, evaluated model, and generated prediction intervals for a time series."""

    __tablename__ = "forecast_executions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    target_field: Mapped[str] = mapped_column(String(255), nullable=False)
    time_field: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency: Mapped[str] = mapped_column(String(32), nullable=False)  # D, W, M, Q, Y
    forecast_horizon: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)

    requested_model_type: Mapped[ForecastModelType] = mapped_column(
        SQLEnum(ForecastModelType, name="forecast_model_type_enum", native_enum=False),
        default=ForecastModelType.AUTO,
        nullable=False,
    )
    selected_model_name: Mapped[str] = mapped_column(String(128), nullable=False)

    status: Mapped[ForecastStatus] = mapped_column(
        SQLEnum(ForecastStatus, name="forecast_status_enum", native_enum=False),
        default=ForecastStatus.PENDING,
        nullable=False,
    )

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metrics (MAE, RMSE, MAPE, sMAPE, baseline_mae)
    metrics_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False
    )

    # Generated Forecast Points: [{date, forecast, lower, upper}]
    predictions_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list, nullable=False
    )

    # Historical normalized time-series points: [{date, actual}]
    historical_points_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list, nullable=False
    )

    # Diagnostic metadata (seasonality, stationarity, parameters, transformations)
    diagnostics_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False
    )

    # Provenance tracking
    provenance_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="forecasts")
    dataset: Mapped["Dataset"] = relationship("Dataset", backref="forecasts")
    dataset_version: Mapped["DatasetVersion"] = relationship("DatasetVersion", backref="forecasts")

    __table_args__ = (Index("ix_forecast_lookup", "dataset_id", "dataset_version_id", "target_field", "time_field"),)
