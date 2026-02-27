from __future__ import annotations

"""ensure task_status enum contains fail/cancelled

Revision ID: 0007_task_status_values
Revises: 0006_workflow_filename
Create Date: 2026-02-27 00:00:04.000000
"""

from alembic import op


revision = "0007_task_status_values"
down_revision = "0006_workflow_filename"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE task_status ADD VALUE IF NOT EXISTS 'fail'")
        op.execute("ALTER TYPE task_status ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass

