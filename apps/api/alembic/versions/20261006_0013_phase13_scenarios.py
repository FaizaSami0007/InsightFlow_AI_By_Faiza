"""Phase 13 Decision Intelligence & Scenario Simulation migration

Revision ID: 20261006_0013
Revises: 20261005_0010
Create Date: 2026-10-06 01:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_0013"
down_revision: Union[str, None] = "20261005_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scenario_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("target_metric", sa.String(length=255), nullable=False),
        sa.Column("baseline_source", sa.String(length=100), nullable=False),
        sa.Column("baseline_value", sa.Float(), nullable=False),
        sa.Column("scenario_value", sa.Float(), nullable=False),
        sa.Column("absolute_change", sa.Float(), nullable=False),
        sa.Column("percentage_change", sa.Float(), nullable=True),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("sensitivity_results", sa.JSON(), nullable=True),
        sa.Column("comparison_scenarios", sa.JSON(), nullable=True),
        sa.Column("engine_version", sa.String(length=50), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scenarios_user_id", "scenarios", ["user_id"])
    op.create_index("ix_scenarios_dataset_id", "scenarios", ["dataset_id"])
    op.create_index("ix_scenarios_user_dataset", "scenarios", ["user_id", "dataset_id"])
    op.create_index("ix_scenarios_target_status", "scenarios", ["target_metric", "status"])


def downgrade() -> None:
    op.drop_index("ix_scenarios_target_status", table_name="scenarios")
    op.drop_index("ix_scenarios_user_dataset", table_name="scenarios")
    op.drop_index("ix_scenarios_dataset_id", table_name="scenarios")
    op.drop_index("ix_scenarios_user_id", table_name="scenarios")
    op.drop_table("scenarios")
