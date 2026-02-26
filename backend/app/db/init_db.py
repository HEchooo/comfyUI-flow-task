from __future__ import annotations

from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import generated_image, photo, subtask, task, task_template  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Local schema cleanup for pre-release development.
        await conn.execute(text("ALTER TABLE subtasks ADD COLUMN IF NOT EXISTS result JSONB NOT NULL DEFAULT '{}'"))
        await conn.execute(text("ALTER TABLE tasks DROP COLUMN IF EXISTS execution_count"))
        await conn.execute(text("ALTER TABLE tasks DROP COLUMN IF EXISTS version"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS workflow_json JSONB"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS workflow_filename TEXT"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS execution_state TEXT"))
        await conn.execute(text("ALTER TABLE task_templates ADD COLUMN IF NOT EXISTS workflow_json JSONB"))
