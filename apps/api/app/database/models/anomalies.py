"""SQLAlchemy database models for Phase 12 Anomaly Detection & Proactive Insight Intelligence."""

import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
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


class AnomalySeverity(str, enum.Enum):
    """Normalized severity level of an anomaly or proactive insight."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyType(str, enum.Enum):
    """Categorization of the detected anomaly pattern."""

    POINT = "POINT"
    TREND = "TREND"
    SEASONAL = "SEASONAL"
    MAGNITUDE = "MAGNITUDE"
    DISTRIBUTION = "DISTRIBUTION"
    GROUP = "GROUP"


class AnomalyStatus(str, enum.Enum):
    """Lifecycle state of an anomaly alert or insight."""

    DETECTED = "DETECTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DISMISSED = "DISMISSED"
    RESOLVED = "RESOLVED"


class DetectionMethod(str, enum.Enum):
    """Statistical detection methodology used."""

    Z_SCORE = "Z_SCORE"
    ROBUST_Z_SCORE = "ROBUST_Z_SCORE"
    IQR = "IQR"
    ROLLING_BASELINE = "ROLLING_BASELINE"
    SEASONAL_BASELINE = "SEASONAL_BASELINE"
    FORECAST_DEVIATION = "FORECAST_DEVIATION"


class InsightType(str, enum.Enum):
    """Type of proactive insight generated."""

    ANOMALY = "ANOMALY"
    TREND_CHANGE = "TREND_CHANGE"
    FORECAST_DEVIATION = "FORECAST_DEVIATION"
    CONTRIBUTION = "CONTRIBUTION"
    DATA_QUALITY = "DATA_QUALITY"


class AnomalyRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores validated, explainable anomaly detections with root-cause provenance."""

    __tablename__ = "anomaly_records"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    metric_field: Mapped[str] = mapped_column(String(255), nullable=False)
    dimension_field: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dimension_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    period: Mapped[str] = mapped_column(String(100), nullable=False)

    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    deviation: Mapped[float] = mapped_column(Float, nullable=False)
    deviation_pct: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)

    severity: Mapped[AnomalySeverity] = mapped_column(
        SQLEnum(AnomalySeverity, name="anomaly_severity_enum", native_enum=False),
        nullable=False,
        default=AnomalySeverity.MEDIUM,
        index=True,
    )
    anomaly_type: Mapped[AnomalyType] = mapped_column(
        SQLEnum(AnomalyType, name="anomaly_type_enum", native_enum=False),
        nullable=False,
        default=AnomalyType.POINT,
    )
    detection_method: Mapped[DetectionMethod] = mapped_column(
        SQLEnum(DetectionMethod, name="detection_method_enum", native_enum=False),
        nullable=False,
        default=DetectionMethod.ROBUST_Z_SCORE,
    )
    status: Mapped[AnomalyStatus] = mapped_column(
        SQLEnum(AnomalyStatus, name="anomaly_status_enum", native_enum=False),
        nullable=False,
        default=AnomalyStatus.DETECTED,
        index=True,
    )

    root_causes: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    dedup_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    provenance: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="anomalies")
    dataset: Mapped["Dataset"] = relationship("Dataset", backref="anomalies")
    dataset_version: Mapped["DatasetVersion"] = relationship("DatasetVersion", backref="anomalies")

    __table_args__ = (
        Index("ix_anomalies_user_dataset", "user_id", "dataset_id"),
        Index("ix_anomalies_dedup", "dataset_id", "dedup_key"),
    )


class InsightRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores proactive analytical insights and summaries derived from anomaly/trend engine."""

    __tablename__ = "insight_records"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    anomaly_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("anomaly_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    insight_type: Mapped[InsightType] = mapped_column(
        SQLEnum(InsightType, name="insight_type_enum", native_enum=False),
        nullable=False,
        default=InsightType.ANOMALY,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[AnomalySeverity] = mapped_column(
        SQLEnum(AnomalySeverity, name="insight_severity_enum", native_enum=False),
        nullable=False,
        default=AnomalySeverity.INFO,
        index=True,
    )
    status: Mapped[AnomalyStatus] = mapped_column(
        SQLEnum(AnomalyStatus, name="insight_status_enum", native_enum=False),
        nullable=False,
        default=AnomalyStatus.DETECTED,
        index=True,
    )

    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    dedup_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    feedback: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="insights")
    dataset: Mapped["Dataset"] = relationship("Dataset", backref="insights")
    anomaly: Mapped[Optional["AnomalyRecord"]] = relationship("AnomalyRecord", backref="insights")

    __table_args__ = (
        Index("ix_insights_user_dataset", "user_id", "dataset_id"),
        Index("ix_insights_dedup", "dataset_id", "dedup_key"),
    )
