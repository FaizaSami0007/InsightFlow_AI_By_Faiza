"""Phase 5 AI provider, structured tool calling and AI orchestrator migration

Revision ID: 20261004_0004
Revises: 20261004_0003
Create Date: 2026-10-04 23:25:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261004_0004"
down_revision: Union[str, None] = "20261004_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. AI Conversations Table
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="New Analysis Session"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_conversations_user_id"), "ai_conversations", ["user_id"], unique=False)
    op.create_index(op.f("ix_ai_conversations_dataset_id"), "ai_conversations", ["dataset_id"], unique=False)
    op.create_index(op.f("ix_ai_conversations_dataset_version_id"), "ai_conversations", ["dataset_version_id"], unique=False)

    # 2. AI Messages Table
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls_json", sa.JSON(), nullable=True),
        sa.Column("tool_results_json", sa.JSON(), nullable=True),
        sa.Column("analysis_ids", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_messages_conversation_id"), "ai_messages", ["conversation_id"], unique=False)

    # 3. AI Request Logs Table
    op.create_table(
        "ai_request_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tool_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="SUCCESS"),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_request_logs_user_id"), "ai_request_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_ai_request_logs_conversation_id"), "ai_request_logs", ["conversation_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_request_logs_conversation_id"), table_name="ai_request_logs")
    op.drop_index(op.f("ix_ai_request_logs_user_id"), table_name="ai_request_logs")
    op.drop_table("ai_request_logs")

    op.drop_index(op.f("ix_ai_messages_conversation_id"), table_name="ai_messages")
    op.drop_table("ai_messages")

    op.drop_index(op.f("ix_ai_conversations_dataset_version_id"), table_name="ai_conversations")
    op.drop_index(op.f("ix_ai_conversations_dataset_id"), table_name="ai_conversations")
    op.drop_index(op.f("ix_ai_conversations_user_id"), table_name="ai_conversations")
    op.drop_table("ai_conversations")
