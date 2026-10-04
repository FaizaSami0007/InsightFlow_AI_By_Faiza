"""Phase 4 deterministic analytics engine migration

Revision ID: 20261004_0003
Revises: 20261004_0002
Create Date: 2026-10-04 23:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261004_0003"
down_revision: Union[str, None] = "20261004_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=False),
        sa.Column("filters_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_jobs_user_id"), "analysis_jobs", ["user_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_dataset_id"), "analysis_jobs", ["dataset_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_dataset_version_id"), "analysis_jobs", ["dataset_version_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_operation"), "analysis_jobs", ["operation"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_status"), "analysis_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_jobs_status"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_operation"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_dataset_version_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_dataset_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_user_id"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
