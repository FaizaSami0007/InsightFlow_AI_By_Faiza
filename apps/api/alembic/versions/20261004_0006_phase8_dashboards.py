"""Phase 8 Dashboards and widgets migration

Revision ID: 20261004_0006
Revises: 20261004_0005
Create Date: 2026-10-05 01:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261004_0006"
down_revision: Union[str, None] = "20261004_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create dashboards table
    op.create_table(
        "dashboards",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="READY"),
        sa.Column("theme", sa.String(length=50), nullable=False, server_default="default"),
        sa.Column("layout_type", sa.String(length=50), nullable=False, server_default="grid_12"),
        sa.Column("layout_config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dashboards_dataset_id", "dashboards", ["dataset_id"])
    op.create_index("ix_dashboards_dataset_version_id", "dashboards", ["dataset_version_id"])
    op.create_index("ix_dashboards_user_id", "dashboards", ["user_id"])

    # 2. Create dashboard_widgets table
    op.create_table(
        "dashboard_widgets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dashboard_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=True),
        sa.Column("widget_type", sa.String(length=50), nullable=False, server_default="chart"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("chart_spec_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("grid_x", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("grid_y", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("grid_w", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("grid_h", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dashboard_id"], ["dashboards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dashboard_widgets_dashboard_id", "dashboard_widgets", ["dashboard_id"])
    op.create_index("ix_dashboard_widgets_analysis_id", "dashboard_widgets", ["analysis_id"])

    # 3. Create dashboard_filters table
    op.create_table(
        "dashboard_filters",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dashboard_id", sa.String(length=36), nullable=False),
        sa.Column("column_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("filter_type", sa.String(length=50), nullable=False, server_default="categorical"),
        sa.Column("operator", sa.String(length=50), nullable=False, server_default="eq"),
        sa.Column("current_value", sa.JSON(), nullable=True),
        sa.Column("allowed_values", sa.JSON(), nullable=True),
        sa.Column("scope", sa.String(length=50), nullable=False, server_default="global"),
        sa.Column("target_widget_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dashboard_id"], ["dashboards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dashboard_filters_dashboard_id", "dashboard_filters", ["dashboard_id"])


def downgrade() -> None:
    op.drop_index("ix_dashboard_filters_dashboard_id", table_name="dashboard_filters")
    op.drop_table("dashboard_filters")

    op.drop_index("ix_dashboard_widgets_analysis_id", table_name="dashboard_widgets")
    op.drop_index("ix_dashboard_widgets_dashboard_id", table_name="dashboard_widgets")
    op.drop_table("dashboard_widgets")

    op.drop_index("ix_dashboards_user_id", table_name="dashboards")
    op.drop_index("ix_dashboards_dataset_version_id", table_name="dashboards")
    op.drop_index("ix_dashboards_dataset_id", table_name="dashboards")
    op.drop_table("dashboards")
