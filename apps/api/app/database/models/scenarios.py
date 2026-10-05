"""Database models for Phase 13 Decision Intelligence & Scenario Simulation."""

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
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.database.models.dataset import Dataset
    from app.database.models.user import User

JSONType = JSON().with_variant(SQLiteJSON, "sqlite")


class ScenarioStatus(str, enum.Enum):
    """Lifecycle execution status of an analytical scenario."""

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class ScenarioType(str, enum.Enum):
    """Classification of what-if simulation experiment."""

    WHAT_IF_SINGLE = "WHAT_IF_SINGLE"
    WHAT_IF_MULTI = "WHAT_IF_MULTI"
    SENSITIVITY = "SENSITIVITY"
    COMPARISON = "COMPARISON"


class AssumptionOperation(str, enum.Enum):
    """Transformation operator applied to baseline variables."""

    PERCENTAGE_CHANGE = "PERCENTAGE_CHANGE"
    ABSOLUTE_CHANGE = "ABSOLUTE_CHANGE"
    DIRECT_SET = "DIRECT_SET"
    MULTIPLIER = "MULTIPLIER"


class ScenarioRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persistent representation of a validated decision intelligence simulation."""

    __tablename__ = "scenarios"

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
    dataset_version_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scenario_type: Mapped[ScenarioType] = mapped_column(
        SQLEnum(ScenarioType, name="scenario_type_enum", native_enum=False),
        nullable=False,
        default=ScenarioType.WHAT_IF_SINGLE,
    )
    status: Mapped[ScenarioStatus] = mapped_column(
        SQLEnum(ScenarioStatus, name="scenario_status_enum", native_enum=False),
        nullable=False,
        default=ScenarioStatus.COMPLETED,
    )

    target_metric: Mapped[str] = mapped_column(String(255), nullable=False)
    baseline_source: Mapped[str] = mapped_column(String(100), default="HISTORICAL_AGGREGATE", nullable=False)

    baseline_value: Mapped[float] = mapped_column(Float, nullable=False)
    scenario_value: Mapped[float] = mapped_column(Float, nullable=False)
    absolute_change: Mapped[float] = mapped_column(Float, nullable=False)
    percentage_change: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    assumptions: Mapped[List[Dict[str, Any]]] = mapped_column(JSONType, default=list, nullable=False)
    sensitivity_results: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONType, nullable=True)
    comparison_scenarios: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONType, nullable=True)

    engine_version: Mapped[str] = mapped_column(String(50), default="scenario_engine_v1", nullable=False)
    provenance: Mapped[Dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    dataset: Mapped["Dataset"] = relationship("Dataset", foreign_keys=[dataset_id], lazy="selectin")

    __table_args__ = (
        Index("ix_scenarios_user_dataset", "user_id", "dataset_id"),
        Index("ix_scenarios_target_status", "target_metric", "status"),
    )
