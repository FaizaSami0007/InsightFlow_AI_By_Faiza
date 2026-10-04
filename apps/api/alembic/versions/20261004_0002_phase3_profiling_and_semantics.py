"""Phase 3 profiling, data quality, and semantic metadata migration

Revision ID: 20261004_0002
Revises: 20261004_0001
Create Date: 2026-10-04 22:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261004_0002"
down_revision: Union[str, None] = "20261004_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Dataset Profiles table
    op.create_table(
        "dataset_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "dataset_version_id",
            sa.String(length=36),
            sa.ForeignKey("dataset_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("memory_size_bytes", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dataset_version_id", name="uq_dataset_version_profile"),
    )
    op.create_index("ix_dataset_profiles_dataset_version_id", "dataset_profiles", ["dataset_version_id"])

    # 2. Column Profiles table
    op.create_table(
        "column_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("dataset_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("column_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("ordinal_position", sa.Integer(), nullable=False),
        sa.Column("data_type", sa.String(length=64), nullable=False),
        sa.Column("conceptual_type", sa.String(length=50), nullable=False, server_default="UNKNOWN"),
        sa.Column("null_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("null_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("unique_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_constant", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_near_constant", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("numeric_stats", sa.JSON(), nullable=True),
        sa.Column("categorical_stats", sa.JSON(), nullable=True),
        sa.Column("temporal_stats", sa.JSON(), nullable=True),
        sa.Column("boolean_stats", sa.JSON(), nullable=True),
        sa.Column("outlier_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outlier_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_column_profile_lookup", "column_profiles", ["profile_id", "column_name"])

    # 3. Data Quality Reports table
    op.create_table(
        "data_quality_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("dataset_profiles.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("grade", sa.String(length=4), nullable=False),
        sa.Column("total_issues", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_summary", sa.JSON(), nullable=False),
        sa.Column("duplicate_summary", sa.JSON(), nullable=False),
        sa.Column("constant_columns", sa.JSON(), nullable=False),
        sa.Column("outlier_summary", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_data_quality_reports_profile_id", "data_quality_reports", ["profile_id"])

    # 4. Semantic Columns table
    op.create_table(
        "semantic_columns",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("dataset_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("column_name", sa.String(length=255), nullable=False),
        sa.Column("inferred_role", sa.String(length=50), nullable=False),
        sa.Column("inferred_confidence", sa.Float(), nullable=False),
        sa.Column("user_role", sa.String(length=50), nullable=True),
        sa.Column("is_dimension", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_measure", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_identifier", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_temporal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("possible_currency", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("format_hint", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("profile_id", "column_name", name="uq_profile_column_semantics"),
    )
    op.create_index("ix_semantic_columns_profile_id", "semantic_columns", ["profile_id"])


def downgrade() -> None:
    op.drop_table("semantic_columns")
    op.drop_table("data_quality_reports")
    op.drop_table("column_profiles")
    op.drop_table("dataset_profiles")
