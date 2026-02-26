from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskStatus
from app.models.subtask import SubTask
from app.models.task import Task
from app.models.task_template import TaskTemplate
from app.schemas.task import TaskTemplateCreate, TaskTemplateCreateTaskRequest, TaskTemplatePatch
from app.services.status import aggregate_parent_status
from app.services.task_service import bind_task_id_to_workflow, get_task_or_404


def _parse_publish_at(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


async def get_template_or_404(session: AsyncSession, template_id: UUID) -> TaskTemplate:
    template = await session.scalar(select(TaskTemplate).where(TaskTemplate.id == template_id))
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task template not found")
    return template


async def list_templates(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    stmt = (
        select(
            TaskTemplate.id,
            TaskTemplate.title,
            TaskTemplate.description,
            TaskTemplate.subtasks,
            TaskTemplate.created_at,
            TaskTemplate.updated_at,
        )
        .order_by(TaskTemplate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    total_stmt = select(func.count(TaskTemplate.id))

    rows = (await session.execute(stmt)).all()
    total = int(await session.scalar(total_stmt) or 0)
    items = [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "subtask_count": len(row.subtasks or []),
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]
    return items, total


async def create_template(session: AsyncSession, payload: TaskTemplateCreate) -> TaskTemplate:
    template = TaskTemplate(
        title=payload.title,
        description=payload.description,
        extra=payload.extra,
        subtasks=[item.model_dump(mode="json") for item in payload.subtasks],
        workflow_json=payload.workflow_json,
    )
    session.add(template)
    await session.commit()
    return await get_template_or_404(session, template.id)


async def patch_template(
    session: AsyncSession,
    *,
    template: TaskTemplate,
    payload: TaskTemplatePatch,
) -> TaskTemplate:
    if payload.title is not None:
        template.title = payload.title
    if payload.description is not None:
        template.description = payload.description
    if payload.extra is not None:
        template.extra = payload.extra
    if payload.subtasks is not None:
        template.subtasks = [item.model_dump(mode="json") for item in payload.subtasks]
    if payload.workflow_json is not None:
        template.workflow_json = payload.workflow_json

    await session.commit()
    return await get_template_or_404(session, template.id)


async def delete_template(session: AsyncSession, template_id: UUID) -> None:
    exists = await session.scalar(select(TaskTemplate.id).where(TaskTemplate.id == template_id))
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task template not found")
    await session.execute(delete(TaskTemplate).where(TaskTemplate.id == template_id))
    await session.commit()


async def create_task_from_template(
    session: AsyncSession,
    *,
    template: TaskTemplate,
    payload: TaskTemplateCreateTaskRequest,
) -> Task:
    task = Task(
        title=payload.title if payload.title is not None else template.title,
        description=payload.description if payload.description is not None else template.description,
        status=TaskStatus.pending,
        extra=payload.extra if payload.extra is not None else (template.extra or {}),
        workflow_json=template.workflow_json,
    )
    session.add(task)
    await session.flush()
    task.workflow_json, _, _ = bind_task_id_to_workflow(task.workflow_json, task.id)

    for item in template.subtasks or []:
        subtask = SubTask(
            task_id=task.id,
            platform=item.get("platform") or "",
            account_name=item.get("account_name") or "",
            account_no=item.get("account_no") or "",
            publish_at=_parse_publish_at(item.get("publish_at")),
            status=TaskStatus.pending,
            result={},
            extra=item.get("extra") or {},
        )
        session.add(subtask)

    await session.flush()
    statuses = (await session.execute(select(SubTask.status).where(SubTask.task_id == task.id))).scalars().all()
    task.status = aggregate_parent_status(list(statuses))

    await session.commit()
    return await get_task_or_404(session, task.id)
