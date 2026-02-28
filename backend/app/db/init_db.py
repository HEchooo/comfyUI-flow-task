from __future__ import annotations

from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import comfyui_setting, generated_image, generated_video, photo, subtask, task, task_template  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        dialect = conn.dialect.name
        await conn.run_sync(Base.metadata.create_all)
        # Local schema cleanup for pre-release development.
        await conn.execute(text("ALTER TABLE subtasks ADD COLUMN IF NOT EXISTS result JSONB NOT NULL DEFAULT '{}'"))
        await conn.execute(text("ALTER TABLE tasks DROP COLUMN IF EXISTS execution_count"))
        await conn.execute(text("ALTER TABLE tasks DROP COLUMN IF EXISTS version"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS workflow_json JSONB"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS workflow_filename TEXT"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS execution_state TEXT"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS schedule_enabled BOOLEAN NOT NULL DEFAULT FALSE"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS schedule_at TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS schedule_time VARCHAR(5)"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS schedule_port INTEGER"))
        await conn.execute(
            text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS schedule_auto_dispatch BOOLEAN NOT NULL DEFAULT TRUE")
        )
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS schedule_last_triggered_at TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE task_templates ADD COLUMN IF NOT EXISTS workflow_json JSONB"))
        if dialect == "postgresql":
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS comfyui_settings (
                        key VARCHAR(32) PRIMARY KEY,
                        server_ip VARCHAR(255) NOT NULL,
                        ports JSONB NOT NULL DEFAULT '[]'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
            )
        else:
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS comfyui_settings (
                        key VARCHAR(32) PRIMARY KEY,
                        server_ip VARCHAR(255) NOT NULL,
                        ports JSON NOT NULL DEFAULT '[]',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
