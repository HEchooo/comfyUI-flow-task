from __future__ import annotations

"""add task schedule_at column

Revision ID: 0010_task_schedule_at
Revises: 0009_task_schedule
Create Date: 2026-02-27 00:00:07.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_task_schedule_at"
down_revision = "0009_task_schedule"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    try:
        columns = inspector.get_columns(table_name)
    except Exception:
        return False
    return any(str(col.get("name")) == column_name for col in columns)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "tasks" not in existing_tables:
        return
    if not _has_column(inspector, "tasks", "schedule_at"):
        op.add_column("tasks", sa.Column("schedule_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "tasks" not in existing_tables:
        return
    if _has_column(inspector, "tasks", "schedule_at"):
        op.drop_column("tasks", "schedule_at")
