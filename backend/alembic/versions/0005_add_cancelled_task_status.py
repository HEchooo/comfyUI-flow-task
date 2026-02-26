from __future__ import annotations

"""add cancelled status to task_status enum

Revision ID: 0005_cancelled_status
Revises: 0004_exec_state
Create Date: 2026-02-26 00:00:02.000000
"""

from alembic import op


revision = "0005_cancelled_status"
down_revision = "0004_exec_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE task_status ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
