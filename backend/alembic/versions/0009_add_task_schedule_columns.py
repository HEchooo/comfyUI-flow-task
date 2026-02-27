from __future__ import annotations

"""add task schedule columns

Revision ID: 0009_task_schedule
Revises: 0008_comfyui_settings
Create Date: 2026-02-27 00:00:06.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_task_schedule"
down_revision = "0008_comfyui_settings"
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

    if not _has_column(inspector, "tasks", "schedule_enabled"):
        op.add_column(
            "tasks",
            sa.Column("schedule_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.alter_column("tasks", "schedule_enabled", server_default=None)

    if not _has_column(inspector, "tasks", "schedule_time"):
        op.add_column("tasks", sa.Column("schedule_time", sa.String(length=5), nullable=True))

    if not _has_column(inspector, "tasks", "schedule_port"):
        op.add_column("tasks", sa.Column("schedule_port", sa.Integer(), nullable=True))

    if not _has_column(inspector, "tasks", "schedule_auto_dispatch"):
        op.add_column(
            "tasks",
            sa.Column("schedule_auto_dispatch", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
        op.alter_column("tasks", "schedule_auto_dispatch", server_default=None)

    if not _has_column(inspector, "tasks", "schedule_last_triggered_at"):
        op.add_column("tasks", sa.Column("schedule_last_triggered_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "tasks" not in existing_tables:
        return

    if _has_column(inspector, "tasks", "schedule_last_triggered_at"):
        op.drop_column("tasks", "schedule_last_triggered_at")
    if _has_column(inspector, "tasks", "schedule_auto_dispatch"):
        op.drop_column("tasks", "schedule_auto_dispatch")
    if _has_column(inspector, "tasks", "schedule_port"):
        op.drop_column("tasks", "schedule_port")
    if _has_column(inspector, "tasks", "schedule_time"):
        op.drop_column("tasks", "schedule_time")
    if _has_column(inspector, "tasks", "schedule_enabled"):
        op.drop_column("tasks", "schedule_enabled")
