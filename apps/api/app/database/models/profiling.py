import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.database.models.dataset import DatasetVersion


class ProfileStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ConceptualType(str, enum.Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIME = "TIME"
    UNKNOWN = "UNKNOWN"


class SemanticRole(str, enum.Enum):
    IDENTIFIER = "IDENTIFIER"
    DIMENSION = "DIMENSION"
    MEASURE = "MEASURE"
    DATE = "DATE"
    DATETIME = "DATETIME"
    BOOLEAN = "BOOLEAN"
    CATEGORY = "CATEGORY"
    TEXT = "TEXT"
    UNKNOWN = "UNKNOWN"


class DatasetProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted deterministic profile for a specific immutable DatasetVersion."""

    __tablename__ = "dataset_profiles"

    dataset_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[ProfileStatus] = mapped_column(
        SQLEnum(ProfileStatus, name="profile_status_enum", native_enum=False),
        default=ProfileStatus.PENDING,
        nullable=False,
    )
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memory_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    version: Mapped["DatasetVersion"] = relationship(
        "DatasetVersion",
        back_populates="profile",
    )
    column_profiles: Mapped[List["ColumnProfile"]] = relationship(
        "ColumnProfile",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="ColumnProfile.ordinal_position.asc()",
        lazy="selectin",
    )
    quality_report: Mapped[Optional["DataQualityReport"]] = relationship(
        "DataQualityReport",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    semantic_columns: Mapped[List["SemanticColumn"]] = relationship(
        "SemanticColumn",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="SemanticColumn.column_name.asc()",
        lazy="selectin",
    )

    __table_args__ = (UniqueConstraint("dataset_version_id", name="uq_dataset_version_profile"),)


class ColumnProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Detailed structural and statistical summary for an individual column."""

    __tablename__ = "column_profiles"

    profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ordinal_position: Mapped[int] = mapped_column(Integer, nullable=False)
    data_type: Mapped[str] = mapped_column(String(64), nullable=False)
    conceptual_type: Mapped[ConceptualType] = mapped_column(
        SQLEnum(ConceptualType, name="conceptual_type_enum", native_enum=False),
        default=ConceptualType.UNKNOWN,
        nullable=False,
    )
    null_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    null_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unique_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_constant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_near_constant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Statistical JSON payloads
    numeric_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    categorical_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    temporal_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    boolean_stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Outliers
    outlier_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outlier_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    profile: Mapped["DatasetProfile"] = relationship(
        "DatasetProfile",
        back_populates="column_profiles",
    )

    __table_args__ = (Index("ix_column_profile_lookup", "profile_id", "column_name"),)


class DataQualityReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Explainable dataset quality audit with score breakdown and rule warnings."""

    __tablename__ = "data_quality_reports"

    profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 100.0
    grade: Mapped[str] = mapped_column(String(4), nullable=False)  # A, B, C, D, F
    total_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    missing_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    duplicate_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    constant_columns: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    outlier_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    warnings: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)

    # Relationships
    profile: Mapped["DatasetProfile"] = relationship(
        "DatasetProfile",
        back_populates="quality_report",
    )


class SemanticColumn(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Semantic metadata for a column with confidence and user override support."""

    __tablename__ = "semantic_columns"

    profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    inferred_role: Mapped[SemanticRole] = mapped_column(
        SQLEnum(SemanticRole, name="semantic_role_enum", native_enum=False),
        nullable=False,
    )
    inferred_confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    user_role: Mapped[Optional[SemanticRole]] = mapped_column(
        SQLEnum(SemanticRole, name="user_semantic_role_enum", native_enum=False),
        nullable=True,
    )

    is_dimension: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_measure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_identifier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_temporal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    possible_currency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    format_hint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    profile: Mapped["DatasetProfile"] = relationship(
        "DatasetProfile",
        back_populates="semantic_columns",
    )

    __table_args__ = (UniqueConstraint("profile_id", "column_name", name="uq_profile_column_semantics"),)
