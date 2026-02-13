from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.task import (
    CallbackSubTaskGeneratedImagesRequest,
    CallbackSubTaskGeneratedImagesResponse,
    CallbackSubTaskStatusRequest,
    CallbackSubTaskStatusResponse,
    GeneratedImageRead,
)
from app.services.task_service import (
    get_task_or_404,
    get_subtask_or_404,
    patch_subtask_status,
    replace_subtask_generated_images,
)

router = APIRouter(prefix="/callbacks", tags=["callbacks"])


@router.post("/subtask-status", response_model=CallbackSubTaskStatusResponse)
async def callback_subtask_status_api(
    payload: CallbackSubTaskStatusRequest,
    session: AsyncSession = Depends(get_db),
) -> CallbackSubTaskStatusResponse:
    subtask = await get_subtask_or_404(session, payload.subtask_id)
    updated_subtask = await patch_subtask_status(
        session,
        subtask=subtask,
        target=payload.status,
        message=payload.message,
        result=payload.result,
    )
    task = await get_task_or_404(session, updated_subtask.task_id)
    return CallbackSubTaskStatusResponse(
        subtask_id=updated_subtask.id,
        subtask_status=updated_subtask.status,
        task_id=task.id,
        task_status=task.status,
        result=updated_subtask.result,
    )


@router.post("/subtask-generated-images", response_model=CallbackSubTaskGeneratedImagesResponse)
async def callback_subtask_generated_images_api(
    payload: CallbackSubTaskGeneratedImagesRequest,
    session: AsyncSession = Depends(get_db),
) -> CallbackSubTaskGeneratedImagesResponse:
    subtask = await get_subtask_or_404(session, payload.subtask_id)
    updated_subtask = await replace_subtask_generated_images(
        session,
        subtask=subtask,
        images=payload.images,
    )
    images = sorted(updated_subtask.generated_images, key=lambda item: item.sort_order)
    return CallbackSubTaskGeneratedImagesResponse(
        subtask_id=updated_subtask.id,
        task_id=updated_subtask.task_id,
        saved_count=len(images),
        images=[GeneratedImageRead.model_validate(item) for item in images],
    )
