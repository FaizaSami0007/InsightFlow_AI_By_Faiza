"""Phase 17 Enterprise Data Connectors & Real-World Data Integration migration

Revision ID: 20261006_0017
Revises: 20261006_0016
Create Date: 2026-10-06 14:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_0017"
down_revision: Union[str, None] = "20261006_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Data Connections Table
    op.create_table(
        "data_connections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("connector_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="CONFIGURED"),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("encrypted_credentials", sa.Text(), nullable=True),
        sa.Column("credential_reference", sa.String(length=120), nullable=True),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("health_status", sa.String(length=30), nullable=False, server_default="UNKNOWN"),
        sa.Column("health_details", sa.JSON(), nullable=False),
        sa.Column("sync_schedule", sa.String(length=80), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_connections_user_id", "data_connections", ["user_id"])
    op.create_index("ix_data_connections_name", "data_connections", ["name"])
    op.create_index("ix_data_connections_connector_type", "data_connections", ["connector_type"])
    op.create_index("ix_data_connections_status", "data_connections", ["status"])
    op.create_index("ix_data_connections_workspace_id", "data_connections", ["workspace_id"])
    op.create_index("ix_data_connections_health_status", "data_connections", ["health_status"])
    op.create_index("ix_data_connections_is_active", "data_connections", ["is_active"])
    op.create_index("ix_data_connections_user_type", "data_connections", ["user_id", "connector_type"])

    # 2. Data Connection Sync Jobs Table
    op.create_table(
        "data_connection_sync_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=True),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("source_resource", sa.String(length=255), nullable=False),
        sa.Column("sync_type", sa.String(length=40), nullable=False, server_default="FULL_SYNC"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="QUEUED"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rows_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("sync_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["data_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_connection_sync_jobs_connection_id", "data_connection_sync_jobs", ["connection_id"])
    op.create_index("ix_data_connection_sync_jobs_dataset_id", "data_connection_sync_jobs", ["dataset_id"])
    op.create_index("ix_data_connection_sync_jobs_dataset_version_id", "data_connection_sync_jobs", ["dataset_version_id"])
    op.create_index("ix_data_connection_sync_jobs_source_resource", "data_connection_sync_jobs", ["source_resource"])
    op.create_index("ix_data_connection_sync_jobs_status", "data_connection_sync_jobs", ["status"])

    # 3. Data Connection Schema Snapshots Table
    op.create_table(
        "data_connection_schema_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("source_resource", sa.String(length=255), nullable=False),
        sa.Column("schema_definition", sa.JSON(), nullable=False),
        sa.Column("detected_drift", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["data_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_connection_schema_snapshots_connection_id", "data_connection_schema_snapshots", ["connection_id"])
    op.create_index("ix_data_connection_schema_snapshots_source_resource", "data_connection_schema_snapshots", ["source_resource"])

    # 4. Data Connection Audit Logs Table
    op.create_table(
        "data_connection_audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="SUCCESS"),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["connection_id"], ["data_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_connection_audit_logs_connection_id", "data_connection_audit_logs", ["connection_id"])
    op.create_index("ix_data_connection_audit_logs_user_id", "data_connection_audit_logs", ["user_id"])
    op.create_index("ix_data_connection_audit_logs_action", "data_connection_audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("data_connection_audit_logs")
    op.drop_table("data_connection_schema_snapshots")
    op.drop_table("data_connection_sync_jobs")
    op.drop_table("data_connections")
