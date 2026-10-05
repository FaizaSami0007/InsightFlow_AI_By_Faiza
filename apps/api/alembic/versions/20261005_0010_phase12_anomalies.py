"""Phase 12 Anomaly Detection and Proactive Insight Intelligence migration

Revision ID: 20261005_0010
Revises: 20261005_0009
Create Date: 2026-10-05 22:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261005_0010"
down_revision: Union[str, None] = "20261005_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anomaly_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("metric_field", sa.String(length=255), nullable=False),
        sa.Column("dimension_field", sa.String(length=255), nullable=True),
        sa.Column("dimension_value", sa.String(length=255), nullable=True),
        sa.Column("period", sa.String(length=100), nullable=False),
        sa.Column("observed_value", sa.Float(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("deviation", sa.Float(), nullable=False),
        sa.Column("deviation_pct", sa.Float(), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("anomaly_type", sa.String(length=32), nullable=False, server_default="POINT"),
        sa.Column("detection_method", sa.String(length=64), nullable=False, server_default="ROBUST_Z_SCORE"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DETECTED"),
        sa.Column("root_causes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("dedup_key", sa.String(length=255), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_anomalies_user_id", "anomaly_records", ["user_id"])
    op.create_index("ix_anomalies_dataset_id", "anomaly_records", ["dataset_id"])
    op.create_index("ix_anomalies_dataset_version_id", "anomaly_records", ["dataset_version_id"])
    op.create_index("ix_anomalies_severity", "anomaly_records", ["severity"])
    op.create_index("ix_anomalies_status", "anomaly_records", ["status"])
    op.create_index("ix_anomalies_dedup_key", "anomaly_records", ["dedup_key"])
    op.create_index("ix_anomalies_user_dataset", "anomaly_records", ["user_id", "dataset_id"])
    op.create_index("ix_anomalies_dedup", "anomaly_records", ["dataset_id", "dedup_key"])

    op.create_table(
        "insight_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("anomaly_id", sa.String(length=36), nullable=True),
        sa.Column("insight_type", sa.String(length=32), nullable=False, server_default="ANOMALY"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="INFO"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DETECTED"),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("dedup_key", sa.String(length=255), nullable=False),
        sa.Column("feedback", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["anomaly_id"], ["anomaly_records.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_insights_user_id", "insight_records", ["user_id"])
    op.create_index("ix_insights_dataset_id", "insight_records", ["dataset_id"])
    op.create_index("ix_insights_anomaly_id", "insight_records", ["anomaly_id"])
    op.create_index("ix_insights_severity", "insight_records", ["severity"])
    op.create_index("ix_insights_status", "insight_records", ["status"])
    op.create_index("ix_insights_dedup_key", "insight_records", ["dedup_key"])
    op.create_index("ix_insights_user_dataset", "insight_records", ["user_id", "dataset_id"])
    op.create_index("ix_insights_dedup", "insight_records", ["dataset_id", "dedup_key"])


def downgrade() -> None:
    op.drop_table("insight_records")
    op.drop_table("anomaly_records")
