"""SQLAlchemy models for Dashboards, Dashboard Widgets, and Dashboard Filters."""

import enum
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.system import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DashboardStatus(str, enum.Enum):
    GENERATING = "GENERATING"
    READY = "READY"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class Dashboard(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dashboards"

    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    dataset_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_version_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default=DashboardStatus.READY.value)
    theme: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="default")
    layout_type: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="grid_12")
    layout_config: Mapped[Dict[str, Any]] = mapped_column(sa.JSON, nullable=False, default=dict)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(sa.JSON, nullable=False, default=dict)

    # Relationships
    widgets: Mapped[List["DashboardWidget"]] = relationship(
        "DashboardWidget",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        order_by="DashboardWidget.grid_y, DashboardWidget.grid_x",
    )
    filters: Mapped[List["DashboardFilter"]] = relationship(
        "DashboardFilter",
        back_populates="dashboard",
        cascade="all, delete-orphan",
    )
    dataset = relationship("Dataset", lazy="joined")
    dataset_version = relationship("DatasetVersion", lazy="joined")
    user = relationship("User", lazy="joined")


class DashboardWidget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dashboard_widgets"

    dashboard_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_id: Mapped[Optional[str]] = mapped_column(
        sa.String(36), sa.ForeignKey("analysis_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    widget_type: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="chart")
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    chart_spec_json: Mapped[Dict[str, Any]] = mapped_column(sa.JSON, nullable=False, default=dict)
    grid_x: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    grid_y: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    grid_w: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=6)
    grid_h: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=4)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(sa.JSON, nullable=False, default=dict)

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="widgets")
    analysis = relationship("AnalysisJob", lazy="joined")


class DashboardFilter(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "dashboard_filters"

    dashboard_id: Mapped[str] = mapped_column(
        sa.String(36), sa.ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    column_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    filter_type: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="categorical")
    operator: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="eq")
    current_value: Mapped[Any] = mapped_column(sa.JSON, nullable=True)
    allowed_values: Mapped[Optional[List[Any]]] = mapped_column(sa.JSON, nullable=True)
    scope: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="global")
    target_widget_ids: Mapped[List[str]] = mapped_column(sa.JSON, nullable=False, default=list)

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="filters")
