"""SQLAlchemy models for Dashboard Exports and Dashboard Shares."""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.system import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class ExportFormat(str, enum.Enum):
    PDF = "pdf"
    PNG = "png"
    CSV = "csv"
    JSON = "json"


class DashboardExport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dashboard_exports"

    dashboard_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(sa.String(20), nullable=False, default=ExportFormat.PDF.value)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default=ExportStatus.COMPLETED.value)
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(sa.String(500), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    content_type: Mapped[str] = mapped_column(sa.String(100), nullable=False, default="application/pdf")
    filter_snapshot: Mapped[Dict[str, Any]] = mapped_column(sa.JSON, nullable=False, default=dict)
    metadata_snapshot: Mapped[Dict[str, Any]] = mapped_column(sa.JSON, nullable=False, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    dashboard = relationship("Dashboard", lazy="joined")
    user = relationship("User", lazy="joined")


class DashboardShare(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dashboard_shares"

    dashboard_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    share_token: Mapped[str] = mapped_column(
        sa.String(128), unique=True, nullable=False, index=True
    )
    access_type: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="read_only")
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    is_snapshot: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    snapshot_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(sa.JSON, nullable=True)
    allowed_filters: Mapped[List[str]] = mapped_column(sa.JSON, nullable=False, default=list)
    view_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    # Relationships
    dashboard = relationship("Dashboard", lazy="joined")
    owner = relationship("User", lazy="joined")
