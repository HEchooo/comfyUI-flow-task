from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from app.api.v1.execution import ExecuteTaskRequest, execute_task
from app.db.session import SessionLocal
from app.models.enums import TaskStatus
from app.models.task import Task
from app.services.comfyui_settings_service import (
    ensure_allowed_endpoint,
    fetch_ports_runtime_status,
    get_or_create_comfyui_settings,
    normalize_server_ip,
)

logger = logging.getLogger("app.scheduler")

_SCHEDULE_POLL_INTERVAL_SECONDS = 15.0
_scheduler_task: asyncio.Task | None = None
_scheduler_stop_event: asyncio.Event | None = None
_inflight_task_ids: set[str] = set()


@dataclass
class ScheduledEndpoint:
    server_ip: str
    port: int


def start_task_scheduler() -> None:
    global _scheduler_task, _scheduler_stop_event
    if _scheduler_task is not None and not _scheduler_task.done():
        return
    loop = asyncio.get_running_loop()
    _scheduler_stop_event = asyncio.Event()
    _scheduler_task = loop.create_task(_scheduler_loop(_scheduler_stop_event))
    logger.info("Task scheduler started")


async def stop_task_scheduler() -> None:
    global _scheduler_task, _scheduler_stop_event
    stop_event = _scheduler_stop_event
    worker = _scheduler_task
    _scheduler_stop_event = None
    _scheduler_task = None

    if stop_event is not None:
        stop_event.set()
    if worker is None:
        return
    worker.cancel()
    try:
        await worker
    except asyncio.CancelledError:
        pass
    logger.info("Task scheduler stopped")


async def _scheduler_loop(stop_event: asyncio.Event) -> None:
    try:
        while not stop_event.is_set():
            try:
                await _run_schedule_once()
            except Exception:
                logger.exception("Scheduled trigger loop failed")

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=_SCHEDULE_POLL_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                continue
    except asyncio.CancelledError:
        raise


async def _run_schedule_once() -> None:
    now_local = datetime.now().astimezone()
    due_task_ids = await _collect_due_task_ids(now_local)
    if not due_task_ids:
        return

    for task_id in due_task_ids:
        task_id_str = str(task_id)
        if task_id_str in _inflight_task_ids:
            continue
        _inflight_task_ids.add(task_id_str)
        try:
            await _trigger_scheduled_task(task_id)
        finally:
            _inflight_task_ids.discard(task_id_str)


def _parse_schedule_time(value: str | None) -> tuple[int, int] | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None
    try:
        parsed = datetime.strptime(normalized, "%H:%M")
    except ValueError:
        return None
    return parsed.hour, parsed.minute


def _is_due_today(*, schedule_time: str | None, last_triggered_at: datetime | None, now_local: datetime) -> bool:
    parsed = _parse_schedule_time(schedule_time)
    if parsed is None:
        return False
    target_hour, target_minute = parsed
    if now_local.hour != target_hour or now_local.minute != target_minute:
        return False

    if last_triggered_at is None:
        return True
    last_local = (
        last_triggered_at.replace(tzinfo=timezone.utc).astimezone(now_local.tzinfo)
        if last_triggered_at.tzinfo is None
        else last_triggered_at.astimezone(now_local.tzinfo)
    )
    return last_local.date() != now_local.date()


def _is_due_once(*, schedule_at: datetime | None, last_triggered_at: datetime | None, now_utc: datetime) -> bool:
    if schedule_at is None:
        return False
    target = schedule_at.replace(tzinfo=timezone.utc) if schedule_at.tzinfo is None else schedule_at.astimezone(timezone.utc)
    if now_utc < target:
        return False
    if last_triggered_at is None:
        return True
    last = (
        last_triggered_at.replace(tzinfo=timezone.utc)
        if last_triggered_at.tzinfo is None
        else last_triggered_at.astimezone(timezone.utc)
    )
    return last < target


async def _collect_due_task_ids(now_local: datetime) -> list[UUID]:
    now_utc = now_local.astimezone(timezone.utc)
    async with SessionLocal() as session:
        stmt = select(
            Task.id,
            Task.schedule_at,
            Task.schedule_time,
            Task.schedule_last_triggered_at,
            Task.status,
        ).where(Task.schedule_enabled.is_(True))
        rows = (await session.execute(stmt)).all()

    due: list[UUID] = []
    for row in rows:
        if row.status == TaskStatus.running:
            continue
        if _is_due_once(
            schedule_at=row.schedule_at,
            last_triggered_at=row.schedule_last_triggered_at,
            now_utc=now_utc,
        ):
            due.append(row.id)
            continue
        if not _is_due_today(
            schedule_time=row.schedule_time,
            last_triggered_at=row.schedule_last_triggered_at,
            now_local=now_local,
        ):
            continue
        due.append(row.id)
    return due


async def _select_auto_endpoint() -> ScheduledEndpoint | None:
    async with SessionLocal() as session:
        server_ip, _, status_items = await fetch_ports_runtime_status(session)

    reachable = [item for item in status_items if item.reachable]
    if not reachable:
        return None
    reachable.sort(key=lambda item: (int(item.pending_count), int(item.running_count), int(item.port)))
    selected = reachable[0]
    return ScheduledEndpoint(server_ip=server_ip, port=int(selected.port))


async def _select_manual_endpoint(schedule_port: int | None) -> ScheduledEndpoint | None:
    if schedule_port is None:
        return None

    async with SessionLocal() as session:
        config = await get_or_create_comfyui_settings(session)
        server_ip = normalize_server_ip(config.server_ip)
        try:
            endpoint = await ensure_allowed_endpoint(
                session,
                server_ip=server_ip,
                port=int(schedule_port),
            )
        except ValueError:
            return None

    return ScheduledEndpoint(server_ip=endpoint.server_ip, port=endpoint.port)


async def _mark_triggered(task_id: UUID) -> None:
    async with SessionLocal() as session:
        task = await session.get(Task, task_id)
        if not task:
            return
        task.schedule_last_triggered_at = datetime.now(timezone.utc)
        await session.commit()


async def _trigger_scheduled_task(task_id: UUID) -> None:
    schedule_auto_dispatch = False
    schedule_port: int | None = None
    async with SessionLocal() as session:
        task = await session.get(Task, task_id)
        if not task or not task.schedule_enabled:
            return
        if task.status == TaskStatus.running:
            return
        schedule_auto_dispatch = bool(task.schedule_auto_dispatch)
        schedule_port = int(task.schedule_port) if task.schedule_port is not None else None

    if schedule_auto_dispatch:
        endpoint = await _select_auto_endpoint()
        if endpoint is None:
            logger.warning("Scheduled trigger skipped: no reachable port task_id=%s", task_id)
            await _mark_triggered(task_id)
            return
    else:
        endpoint = await _select_manual_endpoint(schedule_port)
        if endpoint is None:
            logger.warning(
                "Scheduled trigger skipped: invalid manual schedule port task_id=%s port=%s",
                task_id,
                schedule_port,
            )
            await _mark_triggered(task_id)
            return

    await _mark_triggered(task_id)

    async with SessionLocal() as session:
        request = ExecuteTaskRequest(server_ip=endpoint.server_ip, port=endpoint.port)
        try:
            await execute_task(task_id=task_id, payload=request, session=session)
            logger.info(
                "Scheduled trigger dispatched: task_id=%s endpoint=%s:%s",
                task_id,
                endpoint.server_ip,
                endpoint.port,
            )
        except HTTPException as exc:
            logger.warning(
                "Scheduled trigger failed: task_id=%s endpoint=%s:%s status=%s detail=%s",
                task_id,
                endpoint.server_ip,
                endpoint.port,
                exc.status_code,
                exc.detail,
            )
        except Exception:
            logger.exception(
                "Scheduled trigger crashed: task_id=%s endpoint=%s:%s",
                task_id,
                endpoint.server_ip,
                endpoint.port,
            )
