from __future__ import annotations

"""add subtask generated images table

Revision ID: 0002_add_subtask_generated_images
Revises: 0001_init
Create Date: 2026-02-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_subtask_generated_images"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("subtask_generated_images"):
        op.create_table(
            "subtask_generated_images",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("subtask_id", sa.Uuid(), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.Column("object_key", sa.Text(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("extra", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["subtask_id"], ["subtasks.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = {item["name"] for item in inspector.get_indexes("subtask_generated_images")}
    index_name = op.f("ix_subtask_generated_images_subtask_id")
    if index_name not in indexes:
        op.create_index(
            index_name,
            "subtask_generated_images",
            ["subtask_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("subtask_generated_images"):
        indexes = {item["name"] for item in inspector.get_indexes("subtask_generated_images")}
        index_name = op.f("ix_subtask_generated_images_subtask_id")
        if index_name in indexes:
            op.drop_index(index_name, table_name="subtask_generated_images")
        op.drop_table("subtask_generated_images")
