from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1 import auth, callbacks, subtasks, task_templates, tasks, uploads
from app.core.security import require_current_user

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)

protected_router = APIRouter(dependencies=[Depends(require_current_user)])
protected_router.include_router(tasks.router)
protected_router.include_router(subtasks.router)
protected_router.include_router(callbacks.router)
protected_router.include_router(task_templates.router)
protected_router.include_router(uploads.router)

api_router.include_router(protected_router)
