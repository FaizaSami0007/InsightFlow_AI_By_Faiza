"""Phase 19 Scalability, Performance & Production Observability migration

Revision ID: 20261006_0019
Revises: 20261006_0018
Create Date: 2026-10-06 15:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_0019"
down_revision: Union[str, None] = "20261006_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create performance_metric_snapshots table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "performance_metric_snapshots" not in tables:
        op.create_table(
            "performance_metric_snapshots",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("p50_latency_ms", sa.Float(), nullable=False),
            sa.Column("p95_latency_ms", sa.Float(), nullable=False),
            sa.Column("p99_latency_ms", sa.Float(), nullable=False),
            sa.Column("requests_per_second", sa.Float(), nullable=False),
            sa.Column("error_rate_percent", sa.Float(), nullable=False),
            sa.Column("memory_rss_mb", sa.Float(), nullable=False),
            sa.Column("cpu_percent", sa.Float(), nullable=False),
            sa.Column("total_requests", sa.Integer(), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_perf_metrics_timestamp", "performance_metric_snapshots", ["timestamp"])


def downgrade() -> None:
    op.drop_table("performance_metric_snapshots")
