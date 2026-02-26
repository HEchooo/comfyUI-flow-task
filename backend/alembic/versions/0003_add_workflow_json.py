from __future__ import annotations

"""add workflow_json column to tasks and task_templates

Revision ID: 0003_add_workflow_json
Revises: 0002_add_subtask_generated_images
Create Date: 2026-02-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_workflow_json"
down_revision = "0002_add_subtask_generated_images"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    task_columns = {c["name"] for c in inspector.get_columns("tasks")}
    if "workflow_json" not in task_columns:
        op.add_column("tasks", sa.Column("workflow_json", sa.JSON(), nullable=True))

    template_columns = {c["name"] for c in inspector.get_columns("task_templates")}
    if "workflow_json" not in template_columns:
        op.add_column("task_templates", sa.Column("workflow_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    template_columns = {c["name"] for c in inspector.get_columns("task_templates")}
    if "workflow_json" in template_columns:
        op.drop_column("task_templates", "workflow_json")

    task_columns = {c["name"] for c in inspector.get_columns("tasks")}
    if "workflow_json" in task_columns:
        op.drop_column("tasks", "workflow_json")
