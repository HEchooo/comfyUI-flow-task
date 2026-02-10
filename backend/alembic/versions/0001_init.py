from __future__ import annotations

"""initial task management tables

Revision ID: 0001_init
Revises:
Create Date: 2026-02-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    task_status = sa.Enum("pending", "running", "success", "fail", name="task_status")
    photo_source_type = sa.Enum("img_url", "upload", "paste", name="photo_source_type")

    task_status.create(op.get_bind(), checkfirst=True)
    photo_source_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", task_status, nullable=False),
        sa.Column("comfy_message", sa.Text(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "subtasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("account_no", sa.String(length=100), nullable=False),
        sa.Column("publish_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", task_status, nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("extra", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subtasks_task_id"), "subtasks", ["task_id"], unique=False)

    op.create_table(
        "subtask_photos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("subtask_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", photo_source_type, nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subtask_id"], ["subtasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subtask_photos_subtask_id"), "subtask_photos", ["subtask_id"], unique=False)

    op.create_table(
        "task_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=False),
        sa.Column("subtasks", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("task_templates")
    op.drop_index(op.f("ix_subtask_photos_subtask_id"), table_name="subtask_photos")
    op.drop_table("subtask_photos")
    op.drop_index(op.f("ix_subtasks_task_id"), table_name="subtasks")
    op.drop_table("subtasks")
    op.drop_table("tasks")

    sa.Enum(name="photo_source_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="task_status").drop(op.get_bind(), checkfirst=True)
