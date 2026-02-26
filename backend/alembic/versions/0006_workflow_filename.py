from __future__ import annotations

"""add workflow_filename column to tasks

Revision ID: 0006_workflow_filename
Revises: 0005_cancelled_status
Create Date: 2026-02-26 00:00:03.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_workflow_filename"
down_revision = "0005_cancelled_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    task_columns = {c["name"] for c in inspector.get_columns("tasks")}
    if "workflow_filename" not in task_columns:
        op.add_column("tasks", sa.Column("workflow_filename", sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    task_columns = {c["name"] for c in inspector.get_columns("tasks")}
    if "workflow_filename" in task_columns:
        op.drop_column("tasks", "workflow_filename")
