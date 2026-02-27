from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, callbacks, execution, settings, subtasks, task_templates, tasks, uploads

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(callbacks.router)
api_router.include_router(tasks.router)
api_router.include_router(subtasks.router)
api_router.include_router(task_templates.router)
api_router.include_router(uploads.router)
api_router.include_router(execution.router)
api_router.include_router(settings.router)
