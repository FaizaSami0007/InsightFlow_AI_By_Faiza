"""Phase 14 Knowledge Intelligence, RAG & Business Knowledge migration

Revision ID: 20261006_0014
Revises: 20261006_0013
Create Date: 2026-10-06 01:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_0014"
down_revision: Union[str, None] = "20261006_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Knowledge Collections Table
    op.create_table(
        "knowledge_collections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, default=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_collections_user_id", "knowledge_collections", ["user_id"])

    # 2. Knowledge Documents Table
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("collection_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, default=0),
        sa.Column("storage_reference", sa.String(length=512), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("knowledge_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("current_version_num", sa.Integer(), nullable=False, default=1),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["knowledge_collections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_documents_user_id", "knowledge_documents", ["user_id"])
    op.create_index("ix_knowledge_documents_collection_id", "knowledge_documents", ["collection_id"])
    op.create_index("ix_knowledge_documents_checksum", "knowledge_documents", ["checksum"])
    op.create_index("ix_knowledge_documents_status", "knowledge_documents", ["status"])

    # 3. Knowledge Document Versions Table
    op.create_table(
        "knowledge_document_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_reference", sa.String(length=512), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("extracted_text_length", sa.Integer(), nullable=False, default=0),
        sa.Column("chunk_count", sa.Integer(), nullable=False, default=0),
        sa.Column("is_ocr", sa.Boolean(), nullable=False, default=False),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_document_versions_document_id", "knowledge_document_versions", ["document_id"])

    # 4. Knowledge Chunks Table
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("document_version_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, default=0),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_heading", sa.String(length=255), nullable=True),
        sa.Column("embedding_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_version_id"], ["knowledge_document_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"])
    op.create_index("ix_knowledge_chunks_document_version_id", "knowledge_chunks", ["document_version_id"])

    # 5. Dataset Knowledge Links Table
    op.create_table(
        "dataset_knowledge_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=True),
        sa.Column("document_id", sa.String(length=36), nullable=True),
        sa.Column("collection_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("relationship_nature", sa.String(length=64), nullable=False, default="governed_by"),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["collection_id"], ["knowledge_collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_knowledge_links_dataset_id", "dataset_knowledge_links", ["dataset_id"])
    op.create_index("ix_dataset_knowledge_links_user_id", "dataset_knowledge_links", ["user_id"])


def downgrade() -> None:
    op.drop_table("dataset_knowledge_links")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_document_versions")
    op.drop_table("knowledge_documents")
    op.drop_table("knowledge_collections")
