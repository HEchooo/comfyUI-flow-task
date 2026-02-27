from __future__ import annotations

"""add comfyui_settings table

Revision ID: 0008_comfyui_settings
Revises: 0007_task_status_values
Create Date: 2026-02-27 00:00:05.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_comfyui_settings"
down_revision = "0007_task_status_values"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "comfyui_settings" in existing_tables:
        return
    op.create_table(
        "comfyui_settings",
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("server_ip", sa.String(length=255), nullable=False),
        sa.Column("ports", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "comfyui_settings" in existing_tables:
        op.drop_table("comfyui_settings")
