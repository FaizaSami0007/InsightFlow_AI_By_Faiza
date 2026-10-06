"""SQLAlchemy database models for Phase 16 Production MLOps, Model Lifecycle & Model Monitoring."""

import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.database.models.dataset import Dataset, DatasetVersion
    from app.database.models.user import User


class MLModelType(str, enum.Enum):
    """Supported machine learning model families."""

    FORECASTING = "FORECASTING"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"
    CLASSIFICATION = "CLASSIFICATION"
    REGRESSION = "REGRESSION"
    CLUSTERING = "CLUSTERING"
    RECOMMENDATION = "RECOMMENDATION"
    EMBEDDING = "EMBEDDING"
    LLM_ADAPTER = "LLM_ADAPTER"


class MLModelVersionStatus(str, enum.Enum):
    """Lifecycle state of a registered model version."""

    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    STAGED = "STAGED"
    PRODUCTION = "PRODUCTION"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"
    FAILED = "FAILED"


class MLDeploymentEnvironment(str, enum.Enum):
    """Deployment targets for a model version."""

    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class MLDeploymentStatus(str, enum.Enum):
    """Status of an active or past model deployment."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ROLLED_BACK = "ROLLED_BACK"


class MLAlertSeverity(str, enum.Enum):
    """Severity levels for model monitoring alerts."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class MLModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Central registry entity representing a conceptual machine learning model."""

    __tablename__ = "ml_models"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    workspace_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    model_type: Mapped[MLModelType] = mapped_column(
        SQLEnum(MLModelType, name="ml_model_type_enum"),
        index=True,
        nullable=False,
    )
    task_type: Mapped[str] = mapped_column(
        String(80),
        index=True,
        nullable=False,
    )
    framework: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="statsmodels",
    )
    provider: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="insightflow_native",
    )
    status: Mapped[str] = mapped_column(
        String(40),
        index=True,
        nullable=False,
        default="ACTIVE",
    )
    owner: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="system",
    )
    tags: Mapped[List[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    versions: Mapped[List["MLModelVersion"]] = relationship(
        "MLModelVersion",
        back_populates="model",
        cascade="all, delete-orphan",
        order_by="desc(MLModelVersion.created_at)",
        lazy="selectin",
    )
    experiments: Mapped[List["MLExperiment"]] = relationship(
        "MLExperiment",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    alerts: Mapped[List["MLModelAlert"]] = relationship(
        "MLModelAlert",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_ml_models_user_type", "user_id", "model_type"),
        Index("ix_ml_models_workspace", "workspace_id", "status"),
    )


class MLModelVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Specific immutable version, artifact lineage, feature contract and metrics for a registered model."""

    __tablename__ = "ml_model_versions"

    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )
    artifact_location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    training_dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    training_dataset_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    feature_schema: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    preprocessing_version: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="v1.0.0",
    )
    parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    baseline_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    status: Mapped[MLModelVersionStatus] = mapped_column(
        SQLEnum(MLModelVersionStatus, name="ml_model_version_status_enum"),
        index=True,
        nullable=False,
        default=MLModelVersionStatus.DRAFT,
    )
    approval_record: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    health_status: Mapped[str] = mapped_column(
        String(20),
        index=True,
        nullable=False,
        default="GOOD",
    )
    health_details: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )

    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel", back_populates="versions", lazy="selectin")
    training_dataset: Mapped[Optional["Dataset"]] = relationship("Dataset", lazy="selectin")
    training_dataset_version: Mapped[Optional["DatasetVersion"]] = relationship("DatasetVersion", lazy="selectin")
    evaluations: Mapped[List["MLModelEvaluation"]] = relationship(
        "MLModelEvaluation",
        back_populates="model_version",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    deployments: Mapped[List["MLModelDeployment"]] = relationship(
        "MLModelDeployment",
        back_populates="model_version",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    drift_reports: Mapped[List["MLModelDriftReport"]] = relationship(
        "MLModelDriftReport",
        back_populates="model_version",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (Index("ix_ml_model_versions_unique", "model_id", "version", unique=True),)


class MLExperiment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks training runs, hyperparameter sweeps, feature configs and evaluation results."""

    __tablename__ = "ml_experiments"

    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(120),
        index=True,
        nullable=False,
    )
    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
    )
    dataset_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    features: Mapped[List[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    preprocessing_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    evaluation_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="COMPLETED",
    )

    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel", back_populates="experiments", lazy="selectin")


class MLModelEvaluation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Standardized validation run verifying candidate model performance against test datasets and baselines."""

    __tablename__ = "ml_model_evaluations"

    model_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
    )
    dataset_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    evaluation_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="HOLDOUT",
    )
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    baseline_comparison: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    passed_validation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    warnings: Mapped[List[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    evaluated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    model_version: Mapped["MLModelVersion"] = relationship(
        "MLModelVersion", back_populates="evaluations", lazy="selectin"
    )


class MLModelDeployment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Records the active/inactive deployment state of a model version in a specific environment."""

    __tablename__ = "ml_model_deployments"

    model_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    environment: Mapped[MLDeploymentEnvironment] = mapped_column(
        SQLEnum(MLDeploymentEnvironment, name="ml_deployment_environment_enum"),
        index=True,
        nullable=False,
        default=MLDeploymentEnvironment.DEVELOPMENT,
    )
    status: Mapped[MLDeploymentStatus] = mapped_column(
        SQLEnum(MLDeploymentStatus, name="ml_deployment_status_enum"),
        index=True,
        nullable=False,
        default=MLDeploymentStatus.ACTIVE,
    )
    deployed_by: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="system",
    )
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    deployed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    retired_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    model_version: Mapped["MLModelVersion"] = relationship(
        "MLModelVersion", back_populates="deployments", lazy="selectin"
    )


class MLModelDriftReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores statistical drift calculations, feature distribution comparisons, and data quality audits."""

    __tablename__ = "ml_model_drift_reports"

    model_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
    )
    dataset_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    drift_detected: Mapped[bool] = mapped_column(
        Boolean,
        index=True,
        nullable=False,
        default=False,
    )
    data_drift_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    feature_drift_results: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    prediction_drift_results: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    concept_drift_results: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    data_quality_results: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    recommendation: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="NO_ACTION",
    )
    evaluated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    model_version: Mapped["MLModelVersion"] = relationship(
        "MLModelVersion", back_populates="drift_reports", lazy="selectin"
    )


class MLModelAlert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Actionable monitoring alerts triggered by drift thresholds, performance degradation, or stale models."""

    __tablename__ = "ml_model_alerts"

    model_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    model_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("ml_model_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    alert_type: Mapped[str] = mapped_column(
        String(60),
        index=True,
        nullable=False,
    )
    severity: Mapped[MLAlertSeverity] = mapped_column(
        SQLEnum(MLAlertSeverity, name="ml_alert_severity_enum"),
        index=True,
        nullable=False,
        default=MLAlertSeverity.WARNING,
    )
    metric_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    observed_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        index=True,
        nullable=False,
        default=False,
    )

    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel", back_populates="alerts", lazy="selectin")
    model_version: Mapped[Optional["MLModelVersion"]] = relationship("MLModelVersion", lazy="selectin")
