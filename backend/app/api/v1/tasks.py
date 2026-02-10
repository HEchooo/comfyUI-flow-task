from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskDeleteResponse,
    TaskListItem,
    TaskListResponse,
    TaskPatch,
    TaskRead,
    TaskStatusPatchRequest,
    TaskStatusPatchResponse,
)
from app.services.task_service import (
    create_task,
    delete_task,
    get_task_or_404,
    list_tasks,
    patch_task,
    patch_task_status,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger("app.tasks")


@router.post("", response_model=TaskRead)
async def create_task_api(payload: TaskCreate, session: AsyncSession = Depends(get_db)) -> TaskRead:
    task = await create_task(session, payload)
    return TaskRead.model_validate(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks_api(
    task_id: UUID | None = Query(default=None),
    status: TaskStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    items, total = await list_tasks(
        session,
        task_id=task_id,
        status_filter=status,
        page=page,
        page_size=page_size,
    )
    logger.info(
        "list_tasks filters: task_id=%s status=%s page=%s page_size=%s -> items=%s total=%s",
        task_id,
        status,
        page,
        page_size,
        len(items),
        total,
    )
    return TaskListResponse(
        items=[TaskListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task_api(task_id: UUID, session: AsyncSession = Depends(get_db)) -> TaskRead:
    task = await get_task_or_404(session, task_id)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def patch_task_api(
    task_id: UUID,
    payload: TaskPatch,
    session: AsyncSession = Depends(get_db),
) -> TaskRead:
    task = await get_task_or_404(session, task_id)
    updated = await patch_task(session, task, payload)
    return TaskRead.model_validate(updated)


@router.patch("/{task_id}/status", response_model=TaskStatusPatchResponse)
async def patch_task_status_api(
    task_id: UUID,
    payload: TaskStatusPatchRequest,
    session: AsyncSession = Depends(get_db),
) -> TaskStatusPatchResponse:
    task = await get_task_or_404(session, task_id)
    updated = await patch_task_status(session, task=task, target=payload.status, message=payload.message)
    return TaskStatusPatchResponse(
        id=updated.id,
        status=updated.status,
        message=updated.comfy_message,
    )


@router.delete("/{task_id}", response_model=TaskDeleteResponse)
async def delete_task_api(task_id: UUID, session: AsyncSession = Depends(get_db)) -> TaskDeleteResponse:
    deleted_subtask_count = await delete_task(session, task_id)
    return TaskDeleteResponse(id=task_id, deleted_subtask_count=deleted_subtask_count)
