"""Phase 7 Visualization Intelligence migration

Revision ID: 20261004_0005
Revises: 20261004_0004
Create Date: 2026-10-05 00:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261004_0005"
down_revision: Union[str, None] = "20261004_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add visualization_json column to ai_messages table
    op.add_column("ai_messages", sa.Column("visualization_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_messages", "visualization_json")
