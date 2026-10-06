"""Phase 15 Multi-Agent Intelligence & Advanced AI Orchestration migration

Revision ID: 20261006_0015
Revises: 20261006_0014
Create Date: 2026-10-06 12:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_0015"
down_revision: Union[str, None] = "20261006_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. AI Tasks Table (Multi-Agent Task Dependency Graph Nodes)
    op.create_table(
        "ai_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("parent_task_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("dependencies_json", sa.JSON(), nullable=True),
        sa.Column("input_json", sa.JSON(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("execution_time_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_task_id"], ["ai_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_tasks_conversation_id", "ai_tasks", ["conversation_id"])
    op.create_index("ix_ai_tasks_parent_task_id", "ai_tasks", ["parent_task_id"])
    op.create_index("ix_ai_tasks_user_id", "ai_tasks", ["user_id"])
    op.create_index("ix_ai_tasks_agent_id", "ai_tasks", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_tasks_agent_id", table_name="ai_tasks")
    op.drop_index("ix_ai_tasks_user_id", table_name="ai_tasks")
    op.drop_index("ix_ai_tasks_parent_task_id", table_name="ai_tasks")
    op.drop_index("ix_ai_tasks_conversation_id", table_name="ai_tasks")
    op.drop_table("ai_tasks")
