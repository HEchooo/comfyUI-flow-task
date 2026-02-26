from __future__ import annotations

"""add execution_state column to tasks

Revision ID: 0004_exec_state
Revises: 0003_add_workflow_json
Create Date: 2026-02-26 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_exec_state"
down_revision = "0003_add_workflow_json"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    task_columns = {c["name"] for c in inspector.get_columns("tasks")}

    if "execution_state" not in task_columns:
        op.add_column("tasks", sa.Column("execution_state", sa.Text(), nullable=True))

    # Backfill from legacy extra.execution_state if present.
    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        op.execute(
            sa.text(
                """
                UPDATE tasks
                SET execution_state = (extra -> 'execution_state')::text
                WHERE execution_state IS NULL
                  AND extra ? 'execution_state'
                """
            )
        )
        op.execute(
            sa.text(
                """
                UPDATE tasks
                SET extra = extra - 'execution_state'
                WHERE extra ? 'execution_state'
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    task_columns = {c["name"] for c in inspector.get_columns("tasks")}
    if "execution_state" in task_columns:
        op.drop_column("tasks", "execution_state")
