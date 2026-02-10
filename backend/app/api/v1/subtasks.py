from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.task import SubTaskRead, SubTaskStatusPatchRequest, SubTaskStatusPatchResponse, SubTaskUpdate
from app.services.task_service import get_subtask_or_404, patch_subtask, patch_subtask_status

router = APIRouter(prefix="/subtasks", tags=["subtasks"])


@router.patch("/{subtask_id}", response_model=SubTaskRead)
async def patch_subtask_api(
    subtask_id: UUID,
    payload: SubTaskUpdate,
    session: AsyncSession = Depends(get_db),
) -> SubTaskRead:
    subtask = await get_subtask_or_404(session, subtask_id)
    updated = await patch_subtask(session, subtask, payload)
    return SubTaskRead.model_validate(updated)


@router.patch("/{subtask_id}/status", response_model=SubTaskStatusPatchResponse)
async def patch_subtask_status_api(
    subtask_id: UUID,
    payload: SubTaskStatusPatchRequest,
    session: AsyncSession = Depends(get_db),
) -> SubTaskStatusPatchResponse:
    subtask = await get_subtask_or_404(session, subtask_id)
    updated = await patch_subtask_status(
        session,
        subtask=subtask,
        target=payload.status,
        message=payload.message,
        result=payload.result,
    )
    return SubTaskStatusPatchResponse(id=updated.id, task_id=updated.task_id, status=updated.status, result=updated.result)
