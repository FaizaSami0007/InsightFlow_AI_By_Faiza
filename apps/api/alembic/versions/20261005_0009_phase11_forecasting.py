"""Phase 11 Predictive Analytics and Forecasting migration

Revision ID: 20261005_0009
Revises: 20261005_0008
Create Date: 2026-10-05 15:18:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261005_0009"
down_revision: Union[str, None] = "20261005_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forecast_executions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("target_field", sa.String(length=255), nullable=False),
        sa.Column("time_field", sa.String(length=255), nullable=False),
        sa.Column("frequency", sa.String(length=32), nullable=False),
        sa.Column("forecast_horizon", sa.Integer(), nullable=False),
        sa.Column("confidence_level", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("requested_model_type", sa.String(length=64), nullable=False, server_default="AUTO"),
        sa.Column("selected_model_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metrics_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("predictions_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("historical_points_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("diagnostics_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("provenance_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forecast_executions_user_id", "forecast_executions", ["user_id"])
    op.create_index("ix_forecast_executions_dataset_id", "forecast_executions", ["dataset_id"])
    op.create_index("ix_forecast_executions_dataset_version_id", "forecast_executions", ["dataset_version_id"])
    op.create_index(
        "ix_forecast_lookup",
        "forecast_executions",
        ["dataset_id", "dataset_version_id", "target_field", "time_field"],
    )


def downgrade() -> None:
    op.drop_index("ix_forecast_lookup", table_name="forecast_executions")
    op.drop_index("ix_forecast_executions_dataset_version_id", table_name="forecast_executions")
    op.drop_index("ix_forecast_executions_dataset_id", table_name="forecast_executions")
    op.drop_index("ix_forecast_executions_user_id", table_name="forecast_executions")
    op.drop_table("forecast_executions")
