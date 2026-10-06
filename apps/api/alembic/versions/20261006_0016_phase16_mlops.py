"""Phase 16 Production MLOps, Model Lifecycle & Model Monitoring migration

Revision ID: 20261006_0016
Revises: 20261006_0015
Create Date: 2026-10-06 13:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_0016"
down_revision: Union[str, None] = "20261006_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ML Models Table (Central Model Registry)
    op.create_table(
        "ml_models",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("model_type", sa.String(length=40), nullable=False),
        sa.Column("task_type", sa.String(length=80), nullable=False),
        sa.Column("framework", sa.String(length=60), nullable=False, server_default="statsmodels"),
        sa.Column("provider", sa.String(length=60), nullable=False, server_default="insightflow_native"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="ACTIVE"),
        sa.Column("owner", sa.String(length=120), nullable=False, server_default="system"),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ml_models_user_id", "ml_models", ["user_id"])
    op.create_index("ix_ml_models_name", "ml_models", ["name"])
    op.create_index("ix_ml_models_model_type", "ml_models", ["model_type"])
    op.create_index("ix_ml_models_task_type", "ml_models", ["task_type"])
    op.create_index("ix_ml_models_status", "ml_models", ["status"])
    op.create_index("ix_ml_models_workspace_id", "ml_models", ["workspace_id"])
    op.create_index("ix_ml_models_user_type", "ml_models", ["user_id", "model_type"])

    # 2. ML Model Versions Table
    op.create_table(
        "ml_model_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.String(length=30), nullable=False),
        sa.Column("artifact_location", sa.String(length=255), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("training_dataset_id", sa.String(length=36), nullable=True),
        sa.Column("training_dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("feature_schema", sa.JSON(), nullable=False),
        sa.Column("preprocessing_version", sa.String(length=60), nullable=False, server_default="v1.0.0"),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("baseline_metrics", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="DRAFT"),
        sa.Column("approval_record", sa.JSON(), nullable=True),
        sa.Column("health_status", sa.String(length=20), nullable=False, server_default="GOOD"),
        sa.Column("health_details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["ml_models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["training_dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["training_dataset_version_id"], ["dataset_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ml_model_versions_model_id", "ml_model_versions", ["model_id"])
    op.create_index("ix_ml_model_versions_version", "ml_model_versions", ["version"])
    op.create_index("ix_ml_model_versions_status", "ml_model_versions", ["status"])
    op.create_index("ix_ml_model_versions_health_status", "ml_model_versions", ["health_status"])
    op.create_index("ix_ml_model_versions_unique", "ml_model_versions", ["model_id", "version"], unique=True)

    # 3. ML Experiments Table
    op.create_table(
        "ml_experiments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=True),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("preprocessing_config", sa.JSON(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("evaluation_config", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="COMPLETED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["ml_models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ml_experiments_model_id", "ml_experiments", ["model_id"])
    op.create_index("ix_ml_experiments_name", "ml_experiments", ["name"])

    # 4. ML Model Evaluations Table
    op.create_table(
        "ml_model_evaluations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_version_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=True),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("evaluation_type", sa.String(length=60), nullable=False, server_default="HOLDOUT"),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("baseline_comparison", sa.JSON(), nullable=False),
        sa.Column("passed_validation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["model_version_id"], ["ml_model_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ml_model_evaluations_model_version_id", "ml_model_evaluations", ["model_version_id"])

    # 5. ML Model Deployments Table
    op.create_table(
        "ml_model_deployments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_version_id", sa.String(length=36), nullable=False),
        sa.Column("environment", sa.String(length=30), nullable=False, server_default="DEVELOPMENT"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ACTIVE"),
        sa.Column("deployed_by", sa.String(length=120), nullable=False, server_default="system"),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("deployed_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["model_version_id"], ["ml_model_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ml_model_deployments_model_version_id", "ml_model_deployments", ["model_version_id"])
    op.create_index("ix_ml_model_deployments_environment", "ml_model_deployments", ["environment"])
    op.create_index("ix_ml_model_deployments_status", "ml_model_deployments", ["status"])

    # 6. ML Model Drift Reports Table
    op.create_table(
        "ml_model_drift_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_version_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=True),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("drift_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_drift_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("feature_drift_results", sa.JSON(), nullable=False),
        sa.Column("prediction_drift_results", sa.JSON(), nullable=False),
        sa.Column("concept_drift_results", sa.JSON(), nullable=False),
        sa.Column("data_quality_results", sa.JSON(), nullable=False),
        sa.Column("recommendation", sa.String(length=60), nullable=False, server_default="NO_ACTION"),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["model_version_id"], ["ml_model_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ml_model_drift_reports_model_version_id", "ml_model_drift_reports", ["model_version_id"])
    op.create_index("ix_ml_model_drift_reports_drift_detected", "ml_model_drift_reports", ["drift_detected"])

    # 7. ML Model Alerts Table
    op.create_table(
        "ml_model_alerts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_id", sa.String(length=36), nullable=False),
        sa.Column("model_version_id", sa.String(length=36), nullable=True),
        sa.Column("alert_type", sa.String(length=60), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="WARNING"),
        sa.Column("metric_name", sa.String(length=80), nullable=False),
        sa.Column("observed_value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("is_acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["ml_models.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_version_id"], ["ml_model_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ml_model_alerts_model_id", "ml_model_alerts", ["model_id"])
    op.create_index("ix_ml_model_alerts_model_version_id", "ml_model_alerts", ["model_version_id"])
    op.create_index("ix_ml_model_alerts_alert_type", "ml_model_alerts", ["alert_type"])
    op.create_index("ix_ml_model_alerts_severity", "ml_model_alerts", ["severity"])
    op.create_index("ix_ml_model_alerts_is_acknowledged", "ml_model_alerts", ["is_acknowledged"])


def downgrade() -> None:
    op.drop_table("ml_model_alerts")
    op.drop_table("ml_model_drift_reports")
    op.drop_table("ml_model_deployments")
    op.drop_table("ml_model_evaluations")
    op.drop_table("ml_experiments")
    op.drop_table("ml_model_versions")
    op.drop_table("ml_models")
