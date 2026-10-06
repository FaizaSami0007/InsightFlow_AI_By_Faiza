"""Phase 18 Production Security, Compliance & Enterprise Hardening migration

Revision ID: 20261006_0018
Revises: 20261006_0017
Create Date: 2026-10-06 15:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261006_0018"
down_revision: Union[str, None] = "20261006_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add role column to users table if not already present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("users")]
    if "role" not in columns:
        op.add_column("users", sa.Column("role", sa.String(length=32), nullable=False, server_default="admin"))

    # 2. Create security_audit_logs table
    tables = inspector.get_table_names()
    if "security_audit_logs" not in tables:
        op.create_table(
            "security_audit_logs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actor_id", sa.String(length=36), nullable=True),
            sa.Column("actor_email", sa.String(length=255), nullable=True),
            sa.Column("actor_role", sa.String(length=32), nullable=True),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("resource_type", sa.String(length=64), nullable=False),
            sa.Column("resource_id", sa.String(length=64), nullable=True),
            sa.Column("workspace_id", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("correlation_id", sa.String(length=64), nullable=True),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_security_audit_logs_timestamp", "security_audit_logs", ["timestamp"])
        op.create_index("ix_security_audit_logs_actor_id", "security_audit_logs", ["actor_id"])
        op.create_index("ix_security_audit_logs_action", "security_audit_logs", ["action"])
        op.create_index("ix_security_audit_logs_resource_type", "security_audit_logs", ["resource_type"])
        op.create_index("ix_security_audit_logs_workspace_id", "security_audit_logs", ["workspace_id"])
        op.create_index("ix_security_audit_logs_status", "security_audit_logs", ["status"])


def downgrade() -> None:
    op.drop_table("security_audit_logs")
    op.drop_column("users", "role")
