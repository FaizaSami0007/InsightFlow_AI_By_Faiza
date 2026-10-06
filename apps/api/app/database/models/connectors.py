"""SQLAlchemy models for Phase 17 Enterprise Data Connectors & Real-World Data Integration."""

import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
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


class ConnectorType(str, enum.Enum):
    """Categorization of supported external enterprise data connectors."""

    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    SQLITE = "SQLITE"
    REST_API = "REST_API"
    OBJECT_STORAGE = "OBJECT_STORAGE"
    GOOGLE_SHEETS = "GOOGLE_SHEETS"
    FILE = "FILE"


class ConnectionStatus(str, enum.Enum):
    """Lifecycle and operational status of a data connection."""

    CONFIGURED = "CONFIGURED"
    TESTING = "TESTING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"
    ERROR = "ERROR"


class SyncType(str, enum.Enum):
    """Modes of synchronization supported by connectors."""

    FULL_SYNC = "FULL_SYNC"
    INCREMENTAL_SYNC = "INCREMENTAL_SYNC"
    ONE_TIME_IMPORT = "ONE_TIME_IMPORT"


class SyncJobStatus(str, enum.Enum):
    """Execution status of an individual connector ingestion sync job."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ConnectionHealthStatus(str, enum.Enum):
    """Health classification for continuous connection observability."""

    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class DataConnection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """External source connection specification with securely encrypted credentials."""

    __tablename__ = "data_connections"

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
    connector_type: Mapped[ConnectorType] = mapped_column(
        SQLEnum(ConnectorType, name="connector_type_enum"),
        index=True,
        nullable=False,
    )
    status: Mapped[ConnectionStatus] = mapped_column(
        SQLEnum(ConnectionStatus, name="connection_status_enum"),
        index=True,
        nullable=False,
        default=ConnectionStatus.CONFIGURED,
    )
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    encrypted_credentials: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    credential_reference: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True,
    )
    last_tested_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_sync_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    health_status: Mapped[ConnectionHealthStatus] = mapped_column(
        SQLEnum(ConnectionHealthStatus, name="connection_health_status_enum"),
        index=True,
        nullable=False,
        default=ConnectionHealthStatus.UNKNOWN,
    )
    health_details: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    sync_schedule: Mapped[Optional[str]] = mapped_column(
        String(80),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        index=True,
        nullable=False,
        default=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")
    sync_jobs: Mapped[List["DataConnectionSyncJob"]] = relationship(
        "DataConnectionSyncJob",
        back_populates="connection",
        cascade="all, delete-orphan",
        order_by="desc(DataConnectionSyncJob.created_at)",
        lazy="selectin",
    )
    schema_snapshots: Mapped[List["DataConnectionSchemaSnapshot"]] = relationship(
        "DataConnectionSchemaSnapshot",
        back_populates="connection",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    audit_logs: Mapped[List["DataConnectionAuditLog"]] = relationship(
        "DataConnectionAuditLog",
        back_populates="connection",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_data_connections_user_type", "user_id", "connector_type"),
        Index("ix_data_connections_workspace", "workspace_id", "status"),
    )


class DataConnectionSyncJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks discrete execution runs ingesting external tables/endpoints into datasets."""

    __tablename__ = "data_connection_sync_jobs"

    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("data_connections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    dataset_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    source_resource: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    sync_type: Mapped[SyncType] = mapped_column(
        SQLEnum(SyncType, name="sync_type_enum"),
        index=True,
        nullable=False,
        default=SyncType.FULL_SYNC,
    )
    status: Mapped[SyncJobStatus] = mapped_column(
        SQLEnum(SyncJobStatus, name="sync_job_status_enum"),
        index=True,
        nullable=False,
        default=SyncJobStatus.QUEUED,
    )
    started_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rows_processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rows_added: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rows_updated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rows_rejected: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sync_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )

    # Relationships
    connection: Mapped["DataConnection"] = relationship("DataConnection", back_populates="sync_jobs", lazy="selectin")
    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset", lazy="selectin")
    dataset_version: Mapped[Optional["DatasetVersion"]] = relationship("DatasetVersion", lazy="selectin")


class DataConnectionSchemaSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Historical schema discovery state used for tracking schema drift and alerts."""

    __tablename__ = "data_connection_schema_snapshots"

    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("data_connections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source_resource: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    schema_definition: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    detected_drift: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )

    # Relationships
    connection: Mapped["DataConnection"] = relationship(
        "DataConnection", back_populates="schema_snapshots", lazy="selectin"
    )


class DataConnectionAuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable audit trail of all security-sensitive connection operations."""

    __tablename__ = "data_connection_audit_logs"

    connection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("data_connections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(80),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="SUCCESS",
    )
    details: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )

    # Relationships
    connection: Mapped["DataConnection"] = relationship("DataConnection", back_populates="audit_logs", lazy="selectin")
    user: Mapped["User"] = relationship("User", lazy="selectin")
