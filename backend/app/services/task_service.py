from __future__ import annotations

import copy
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.enums import TaskStatus
from app.models.generated_image import SubTaskGeneratedImage
from app.models.photo import SubTaskPhoto
from app.models.subtask import SubTask
from app.models.task import Task
from app.schemas.task import CallbackGeneratedImageItem, SubTaskCreate, SubTaskUpdate, TaskCreate, TaskPatch
from app.services.status import aggregate_parent_status, ensure_transition


def bind_task_id_to_workflow(workflow_json: dict | None, task_id: UUID) -> tuple[dict | None, bool, int]:
    """
    Inject task_id into every GetTaskInfoNode in workflow JSON.

    Returns:
        (workflow_after_bind, changed, matched_node_count)
    """
    if workflow_json is None:
        return None, False, 0
    if not isinstance(workflow_json, dict):
        return workflow_json, False, 0

    updated = copy.deepcopy(workflow_json)
    changed = False
    matched_node_count = 0
    task_id_str = str(task_id)

    for node in updated.values():
        if not isinstance(node, dict):
            continue
        if str(node.get("class_type") or "") != "GetTaskInfoNode":
            continue
        matched_node_count += 1
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            inputs = {}
            node["inputs"] = inputs
        if str(inputs.get("task_id") or "") != task_id_str:
            inputs["task_id"] = task_id_str
            changed = True

    return updated, changed, matched_node_count


def _task_detail_query(task_id: UUID) -> Select[tuple[Task]]:
    return (
        select(Task)
        .where(Task.id == task_id)
        .options(
            selectinload(Task.subtasks).selectinload(SubTask.photos),
            selectinload(Task.subtasks).selectinload(SubTask.generated_images),
        )
    )


def _ensure_photo_count(photo_count: int) -> None:
    if photo_count > settings.max_images_per_subtask:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Each subtask can contain at most {settings.max_images_per_subtask} photos",
        )


async def get_task_or_404(session: AsyncSession, task_id: UUID) -> Task:
    task = await session.scalar(_task_detail_query(task_id))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


async def get_subtask_or_404(session: AsyncSession, subtask_id: UUID) -> SubTask:
    stmt = (
        select(SubTask)
        .where(SubTask.id == subtask_id)
        .options(selectinload(SubTask.photos), selectinload(SubTask.generated_images))
    )
    subtask = await session.scalar(stmt)
    if not subtask:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtask not found")
    return subtask


async def _sync_parent_status(session: AsyncSession, task_id: UUID) -> TaskStatus:
    task = await session.scalar(select(Task).where(Task.id == task_id).options(selectinload(Task.subtasks)))
    if not task:
        return TaskStatus.pending

    next_status = aggregate_parent_status([item.status for item in task.subtasks])
    if next_status != task.status:
        task.status = next_status
    return task.status


def _build_subtask_model(task_id: UUID, item: SubTaskCreate) -> SubTask:
    _ensure_photo_count(len(item.photos))
    return SubTask(
        task_id=task_id,
        platform=item.platform,
        account_name=item.account_name,
        account_no=item.account_no,
        publish_at=item.publish_at,
        status=TaskStatus.pending,
        result={},
        extra=item.extra,
    )


async def _insert_subtasks(
    session: AsyncSession,
    *,
    task_id: UUID,
    payload_subtasks: list[SubTaskCreate],
) -> None:
    for item in payload_subtasks:
        subtask = _build_subtask_model(task_id, item)
        session.add(subtask)
        await session.flush()

        if item.photos:
            session.add_all(
                [
                    SubTaskPhoto(
                        subtask_id=subtask.id,
                        source_type=photo.source_type,
                        url=photo.url,
                        object_key=photo.object_key,
                        sort_order=photo.sort_order,
                    )
                    for photo in item.photos
                ]
            )


async def create_task(session: AsyncSession, payload: TaskCreate) -> Task:
    task = Task(
        title=payload.title,
        description=payload.description,
        status=TaskStatus.pending,
        extra=payload.extra,
        workflow_json=payload.workflow_json,
        workflow_filename=payload.workflow_filename,
    )
    session.add(task)
    await session.flush()
    task.workflow_json, _, _ = bind_task_id_to_workflow(task.workflow_json, task.id)

    await _insert_subtasks(session, task_id=task.id, payload_subtasks=payload.subtasks)
    await _sync_parent_status(session, task.id)

    await session.commit()
    return await get_task_or_404(session, task.id)


async def list_tasks(
    session: AsyncSession,
    *,
    task_id: UUID | None,
    status_filter: TaskStatus | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    count_subtasks = (
        select(func.count(SubTask.id))
        .where(SubTask.task_id == Task.id)
        .correlate(Task)
        .scalar_subquery()
    )

    stmt = select(
        Task.id,
        Task.title,
        Task.description,
        Task.status,
        Task.created_at,
        Task.updated_at,
        count_subtasks.label("subtask_count"),
        Task.workflow_json.isnot(None).label("has_workflow"),
    )
    total_stmt = select(func.count(Task.id))

    if task_id:
        stmt = stmt.where(Task.id == task_id)
        total_stmt = total_stmt.where(Task.id == task_id)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)
        total_stmt = total_stmt.where(Task.status == status_filter)

    stmt = stmt.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    rows = (await session.execute(stmt)).all()
    total = int(await session.scalar(total_stmt) or 0)

    items = [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "status": row.status,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "subtask_count": int(row.subtask_count or 0),
            "has_workflow": bool(row.has_workflow),
        }
        for row in rows
    ]
    return items, total


async def delete_task(session: AsyncSession, task_id: UUID) -> int:
    exists = await session.scalar(select(Task.id).where(Task.id == task_id))
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    deleted_subtask_count = int(
        await session.scalar(select(func.count(SubTask.id)).where(SubTask.task_id == task_id)) or 0
    )

    await session.execute(delete(Task).where(Task.id == task_id))
    await session.commit()
    return deleted_subtask_count


async def patch_task(session: AsyncSession, task: Task, payload: TaskPatch) -> Task:
    changed = False

    if payload.title is not None:
        task.title = payload.title
        changed = True
    if payload.description is not None:
        task.description = payload.description
        changed = True
    if payload.extra is not None:
        task.extra = payload.extra
        changed = True
    if payload.workflow_json is not None:
        bound_workflow_json, _, _ = bind_task_id_to_workflow(payload.workflow_json, task.id)
        task.workflow_json = bound_workflow_json
        changed = True
    if payload.workflow_filename is not None:
        task.workflow_filename = payload.workflow_filename
        changed = True

    if payload.subtasks is not None:
        await session.execute(delete(SubTask).where(SubTask.task_id == task.id))
        await _insert_subtasks(session, task_id=task.id, payload_subtasks=payload.subtasks)
        await _sync_parent_status(session, task.id)
        changed = True

    if changed:
        await session.commit()

    return await get_task_or_404(session, task.id)


async def patch_task_status(
    session: AsyncSession,
    *,
    task: Task,
    target: TaskStatus,
    message: str | None = None,
) -> Task:
    ensure_transition(task.status, target)
    task.status = target
    task.comfy_message = message
    await session.commit()
    return await get_task_or_404(session, task.id)


async def patch_subtask(session: AsyncSession, subtask: SubTask, payload: SubTaskUpdate) -> SubTask:
    if payload.platform is not None:
        subtask.platform = payload.platform
    if payload.account_name is not None:
        subtask.account_name = payload.account_name
    if payload.account_no is not None:
        subtask.account_no = payload.account_no
    if payload.publish_at is not None:
        subtask.publish_at = payload.publish_at
    if payload.extra is not None:
        subtask.extra = payload.extra

    if payload.photos is not None:
        _ensure_photo_count(len(payload.photos))
        await session.execute(delete(SubTaskPhoto).where(SubTaskPhoto.subtask_id == subtask.id))
        if payload.photos:
            session.add_all(
                [
                    SubTaskPhoto(
                        subtask_id=subtask.id,
                        source_type=photo.source_type,
                        url=photo.url,
                        object_key=photo.object_key,
                        sort_order=photo.sort_order,
                    )
                    for photo in payload.photos
                ]
            )

    await session.commit()
    return await get_subtask_or_404(session, subtask.id)


async def patch_subtask_status(
    session: AsyncSession,
    *,
    subtask: SubTask,
    target: TaskStatus,
    message: str | None = None,
    result: dict | None = None,
) -> SubTask:
    ensure_transition(subtask.status, target)
    subtask.status = target
    if result is not None:
        subtask.result = result
    if message:
        extra = dict(subtask.extra or {})
        extra["last_status_message"] = message
        subtask.extra = extra

    await _sync_parent_status(session, subtask.task_id)
    await session.commit()
    return await get_subtask_or_404(session, subtask.id)


async def replace_subtask_generated_images(
    session: AsyncSession,
    *,
    subtask: SubTask,
    images: list[CallbackGeneratedImageItem],
) -> SubTask:
    await session.execute(delete(SubTaskGeneratedImage).where(SubTaskGeneratedImage.subtask_id == subtask.id))

    if images:
        ordered = sorted(images, key=lambda item: item.sort_order)
        session.add_all(
            [
                SubTaskGeneratedImage(
                    subtask_id=subtask.id,
                    url=item.url,
                    object_key=item.object_key,
                    sort_order=item.sort_order,
                    extra=item.extra,
                )
                for item in ordered
            ]
        )

    await session.commit()
    return await get_subtask_or_404(session, subtask.id)
