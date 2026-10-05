"""Phase 10 Dataset Collections and Relationships migration

Revision ID: 20261005_0008
Revises: 20261005_0007
Create Date: 2026-10-05 14:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261005_0008"
down_revision: Union[str, None] = "20261005_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create dataset_collections table
    op.create_table(
        "dataset_collections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_collections_user_id", "dataset_collections", ["user_id"])

    # 2. Create dataset_collection_items table
    op.create_table(
        "dataset_collection_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("collection_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["collection_id"], ["dataset_collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_collection_items_collection_id", "dataset_collection_items", ["collection_id"])
    op.create_index("ix_dataset_collection_items_dataset_id", "dataset_collection_items", ["dataset_id"])

    # 3. Create dataset_relationships table
    op.create_table(
        "dataset_relationships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("collection_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("source_dataset_id", sa.String(length=36), nullable=False),
        sa.Column("source_version_id", sa.String(length=36), nullable=False),
        sa.Column("source_field", sa.String(length=255), nullable=False),
        sa.Column("target_dataset_id", sa.String(length=36), nullable=False),
        sa.Column("target_version_id", sa.String(length=36), nullable=False),
        sa.Column("target_field", sa.String(length=255), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False, server_default="MANY_TO_ONE"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PROPOSED"),
        sa.Column("coverage_ratio", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("source_unique_ratio", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("target_unique_ratio", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("null_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["collection_id"], ["dataset_collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_relationships_collection_id", "dataset_relationships", ["collection_id"])
    op.create_index("ix_dataset_relationships_user_id", "dataset_relationships", ["user_id"])
    op.create_index("ix_dataset_relationships_source_dataset_id", "dataset_relationships", ["source_dataset_id"])
    op.create_index("ix_dataset_relationships_target_dataset_id", "dataset_relationships", ["target_dataset_id"])
    op.create_index("ix_dataset_relationships_status", "dataset_relationships", ["status"])


def downgrade() -> None:
    op.drop_index("ix_dataset_relationships_status", table_name="dataset_relationships")
    op.drop_index("ix_dataset_relationships_target_dataset_id", table_name="dataset_relationships")
    op.drop_index("ix_dataset_relationships_source_dataset_id", table_name="dataset_relationships")
    op.drop_index("ix_dataset_relationships_user_id", table_name="dataset_relationships")
    op.drop_index("ix_dataset_relationships_collection_id", table_name="dataset_relationships")
    op.drop_table("dataset_relationships")

    op.drop_index("ix_dataset_collection_items_dataset_id", table_name="dataset_collection_items")
    op.drop_index("ix_dataset_collection_items_collection_id", table_name="dataset_collection_items")
    op.drop_table("dataset_collection_items")

    op.drop_index("ix_dataset_collections_user_id", table_name="dataset_collections")
    op.drop_table("dataset_collections")
