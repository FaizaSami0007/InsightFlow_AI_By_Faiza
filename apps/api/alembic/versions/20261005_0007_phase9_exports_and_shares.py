"""Phase 9 Exports and Dashboard Shares migration

Revision ID: 20261005_0007
Revises: 20261004_0006
Create Date: 2026-10-05 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261005_0007"
down_revision: Union[str, None] = "20261004_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create dashboard_exports table
    op.create_table(
        "dashboard_exports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dashboard_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False, server_default="pdf"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="COMPLETED"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=False, server_default="application/pdf"),
        sa.Column("filter_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("metadata_snapshot", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dashboard_id"], ["dashboards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dashboard_exports_dashboard_id", "dashboard_exports", ["dashboard_id"])
    op.create_index("ix_dashboard_exports_user_id", "dashboard_exports", ["user_id"])

    # 2. Create dashboard_shares table
    op.create_table(
        "dashboard_shares",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dashboard_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("share_token", sa.String(length=128), nullable=False),
        sa.Column("access_type", sa.String(length=50), nullable=False, server_default="read_only"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_snapshot", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("snapshot_data", sa.JSON(), nullable=True),
        sa.Column("allowed_filters", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dashboard_id"], ["dashboards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("share_token"),
    )
    op.create_index("ix_dashboard_shares_dashboard_id", "dashboard_shares", ["dashboard_id"])
    op.create_index("ix_dashboard_shares_owner_id", "dashboard_shares", ["owner_id"])
    op.create_index("ix_dashboard_shares_share_token", "dashboard_shares", ["share_token"])


def downgrade() -> None:
    op.drop_index("ix_dashboard_shares_share_token", table_name="dashboard_shares")
    op.drop_index("ix_dashboard_shares_owner_id", table_name="dashboard_shares")
    op.drop_index("ix_dashboard_shares_dashboard_id", table_name="dashboard_shares")
    op.drop_table("dashboard_shares")

    op.drop_index("ix_dashboard_exports_user_id", table_name="dashboard_exports")
    op.drop_index("ix_dashboard_exports_dashboard_id", table_name="dashboard_exports")
    op.drop_table("dashboard_exports")
