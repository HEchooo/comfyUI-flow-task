from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import SessionLocal, get_db
from app.models.enums import TaskStatus
from app.models.task import Task
from app.services.comfyui_service import (
    ComfyEvent,
    build_ws_base_url,
    delete_prompt_from_queue,
    fetch_queue_status,
    fetch_queue_prompt_ids,
    interrupt_execution,
    listen_comfyui_ws,
    submit_prompt,
)
from app.services.comfyui_settings_service import ensure_allowed_endpoint, parse_endpoint_from_execution_state
from app.services.task_service import bind_task_id_to_workflow, get_task_or_404

router = APIRouter(prefix="/execution", tags=["execution"])
logger = logging.getLogger("app.execution")

# In-memory registry of active execution sessions
# Maps task_id -> set of WebSocket connections for broadcasting
_ws_connections: dict[str, set[WebSocket]] = {}
_execution_states: dict[str, dict] = {}
_MAX_EVENT_LOG = 300
_PERSIST_FLUSH_INTERVAL_SECONDS = 2.0
_STATE_CLEANUP_INTERVAL_SECONDS = 3600.0
_STATE_RETENTION_SECONDS = 3600.0
_dirty_execution_task_ids: set[str] = set()
_persist_worker_task: asyncio.Task | None = None
_cleanup_worker_task: asyncio.Task | None = None
_listener_stop_events: dict[str, asyncio.Event] = {}
_listener_tasks: dict[str, asyncio.Task] = {}


# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────


class ExecuteTaskRequest(BaseModel):
    server_ip: str
    port: int


class ExecuteEndpoint(BaseModel):
    server_ip: str
    port: int
    base_url: str


class ExecuteTaskResponse(BaseModel):
    task_id: UUID
    prompt_id: str
    endpoint: ExecuteEndpoint


class CancelTaskResponse(BaseModel):
    task_id: UUID
    status: str
    message: str


def _new_execution_state(task_id: str, *, status_value: str) -> dict:
    return {
        "task_id": task_id,
        "status": status_value,
        "prompt_id": "",
        "prompt_ids": [],
        "completed_prompt_ids": [],
        "current_node_id": "",
        "current_node_title": "",
        "current_node_class_type": "",
        "target_endpoint": {"server_ip": "", "port": 0, "base_url": ""},
        "progress": {"node_id": "", "node_title": "", "node_class_type": "", "value": 0, "max": 0},
        "error_message": "",
        "event_log": [],
        "updated_at": _now_iso(),
    }


def _now_log_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _append_event_log(task_id: str, message: str, level: str = "info") -> None:
    state = _execution_states.get(task_id)
    if state is None:
        return
    entries = state.setdefault("event_log", [])
    entries.append(
        {
            "time": _now_log_time(),
            "message": message,
            "type": level,
        }
    )
    if len(entries) > _MAX_EVENT_LOG:
        state["event_log"] = entries[-_MAX_EVENT_LOG:]
    state["updated_at"] = _now_iso()
    _mark_execution_state_dirty(task_id)


def _build_workflow_node_map(workflow_json: dict | None) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    if not isinstance(workflow_json, dict):
        return result
    for raw_node_id, raw_node in workflow_json.items():
        node_id = str(raw_node_id)
        if not isinstance(raw_node, dict):
            result[node_id] = {"title": "", "class_type": ""}
            continue
        meta = raw_node.get("_meta") or {}
        title = meta.get("title", "") if isinstance(meta, dict) else ""
        class_type = raw_node.get("class_type", "")
        result[node_id] = {
            "title": str(title or ""),
            "class_type": str(class_type or ""),
        }
    return result


def _resolve_node_meta(task_id: str, node_id: str | None) -> tuple[str, str]:
    if not node_id:
        return "", ""
    state = _execution_states.get(task_id) or {}
    node_map = state.get("_node_map") or {}
    if not isinstance(node_map, dict):
        return "", ""
    info = node_map.get(str(node_id)) or {}
    if not isinstance(info, dict):
        return "", ""
    return str(info.get("title", "") or ""), str(info.get("class_type", "") or "")


def _format_node_display(node_id: str | None, node_title: str, node_class_type: str) -> str:
    if not node_id:
        return "-"
    if node_title:
        return f"{node_id} ({node_title})"
    if node_class_type:
        return f"{node_id} ({node_class_type})"
    return str(node_id)


def _public_execution_state(state_snapshot: dict | None) -> dict | None:
    if not isinstance(state_snapshot, dict):
        return None
    return {k: v for k, v in state_snapshot.items() if not str(k).startswith("_")}


def _mark_execution_state_dirty(task_id: str) -> None:
    if not task_id:
        return
    _dirty_execution_task_ids.add(task_id)
    _ensure_persist_worker()
    _ensure_cleanup_worker()


def _ensure_persist_worker() -> None:
    global _persist_worker_task
    if _persist_worker_task is not None and not _persist_worker_task.done():
        return
    loop = asyncio.get_running_loop()
    _persist_worker_task = loop.create_task(_persist_worker_loop())


def _ensure_cleanup_worker() -> None:
    global _cleanup_worker_task
    if _cleanup_worker_task is not None and not _cleanup_worker_task.done():
        return
    loop = asyncio.get_running_loop()
    _cleanup_worker_task = loop.create_task(_cleanup_worker_loop())


async def _persist_worker_loop() -> None:
    try:
        while True:
            await asyncio.sleep(_PERSIST_FLUSH_INTERVAL_SECONDS)
            task_ids = list(_dirty_execution_task_ids)
            if not task_ids:
                continue
            _dirty_execution_task_ids.difference_update(task_ids)
            await _persist_execution_states(task_ids)
    except asyncio.CancelledError:
        # Best-effort final flush when worker is cancelled.
        task_ids = list(_dirty_execution_task_ids)
        if task_ids:
            _dirty_execution_task_ids.difference_update(task_ids)
            await _persist_execution_states(task_ids)
        raise
    except Exception:
        logger.exception("Execution state persist worker crashed")


def _parse_iso_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw))
    except Exception:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _should_cleanup_execution_state(task_id: str, state: dict, now_utc: datetime) -> bool:
    if task_id in _listener_stop_events:
        return False
    task_ws_clients = _ws_connections.get(task_id, set())
    if task_ws_clients:
        return False
    status_value = str(state.get("status") or "")
    if status_value == TaskStatus.running.value:
        return False
    updated_at = _parse_iso_datetime(state.get("updated_at"))
    if updated_at is None:
        return True
    return (now_utc - updated_at).total_seconds() >= _STATE_RETENTION_SECONDS


def _cleanup_execution_states_once() -> None:
    if not _execution_states:
        return
    now_utc = datetime.now(timezone.utc)
    removable_task_ids = [
        task_id
        for task_id, state in list(_execution_states.items())
        if isinstance(state, dict) and _should_cleanup_execution_state(task_id, state, now_utc)
    ]
    if not removable_task_ids:
        return
    for task_id in removable_task_ids:
        _execution_states.pop(task_id, None)
        _dirty_execution_task_ids.discard(task_id)
    logger.info("Execution state cleanup completed: removed=%s", len(removable_task_ids))


async def _cleanup_worker_loop() -> None:
    try:
        while True:
            await asyncio.sleep(_STATE_CLEANUP_INTERVAL_SECONDS)
            _cleanup_execution_states_once()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Execution state cleanup worker crashed")


# ──────────────────────────────────────────────
# Execute Task
# ──────────────────────────────────────────────


@router.post("/task/{task_id}", response_model=ExecuteTaskResponse)
async def execute_task(
    task_id: UUID,
    payload: ExecuteTaskRequest,
    session: AsyncSession = Depends(get_db),
) -> ExecuteTaskResponse:
    task = await get_task_or_404(session, task_id)
    workflow_json, workflow_changed, matched_node_count = bind_task_id_to_workflow(task.workflow_json, task.id)
    if workflow_changed:
        task.workflow_json = workflow_json
        logger.info(
            "GetTaskInfoNode task_id bound before execute: task_id=%s matched_nodes=%s",
            task_id,
            matched_node_count,
        )
    if task.status == TaskStatus.running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already running",
        )

    node_count = len(workflow_json) if isinstance(workflow_json, dict) else 0
    logger.info(
        "Execute task requested: task_id=%s status=%s has_workflow=%s node_count=%s",
        task_id,
        task.status.value if task.status else None,
        bool(workflow_json),
        node_count,
    )

    if not workflow_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task has no workflow JSON. Upload a workflow before executing.",
        )

    try:
        endpoint = await ensure_allowed_endpoint(
            session,
            server_ip=payload.server_ip,
            port=payload.port,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    probe_running_count, probe_pending_count, probe_error = await fetch_queue_status(api_base_url=endpoint.base_url)
    if probe_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Selected ComfyUI endpoint is unreachable: {probe_error}",
        )

    # Generate a unique client_id for this execution
    client_id = uuid.uuid4().hex
    ws_base_url = build_ws_base_url(endpoint.base_url)
    task_id_str = str(task_id)
    prompt_ids: set[str] = set()
    listener_stop_event = asyncio.Event()
    listener_connected_event = asyncio.Event()
    old_stop_event = _listener_stop_events.pop(task_id_str, None)
    _listener_tasks.pop(task_id_str, None)
    if old_stop_event is not None:
        old_stop_event.set()

    # Mark task as running immediately once execution is requested.
    task.status = TaskStatus.running
    task.comfy_message = "Execution requested"
    await session.commit()
    logger.info(
        "Task marked running on execute request: task_id=%s endpoint=%s queue_running=%s queue_pending=%s",
        task_id,
        endpoint.base_url,
        probe_running_count,
        probe_pending_count,
    )

    initial_state = _new_execution_state(task_id_str, status_value=TaskStatus.running.value)
    initial_state["_node_map"] = _build_workflow_node_map(workflow_json)
    initial_state["target_endpoint"] = {
        "server_ip": endpoint.server_ip,
        "port": endpoint.port,
        "base_url": endpoint.base_url,
    }
    _execution_states[task_id_str] = initial_state
    _append_event_log(task_id_str, "执行请求已提交，等待 ComfyUI 响应…", "info")
    _append_event_log(task_id_str, f"目标端口: {endpoint.server_ip}:{endpoint.port}", "info")
    _mark_execution_state_dirty(task_id_str)

    # Start ComfyUI listener first to avoid missing fast execution events.
    listener_task = asyncio.create_task(
        _run_comfyui_listener(
            client_id=client_id,
            task_id=task_id_str,
            ws_base_url=ws_base_url,
            prompt_ids=prompt_ids,
            stop_event=listener_stop_event,
            connected_event=listener_connected_event,
        )
    )
    _listener_stop_events[task_id_str] = listener_stop_event
    _listener_tasks[task_id_str] = listener_task
    try:
        await asyncio.wait_for(listener_connected_event.wait(), timeout=3.0)
        logger.info("ComfyUI listener connected before submit: task_id=%s client_id=%s", task_id, client_id)
    except asyncio.TimeoutError:
        logger.warning(
            "ComfyUI listener did not connect within timeout, will still submit: task_id=%s client_id=%s",
            task_id,
            client_id,
        )

    # Submit to ComfyUI
    result = await submit_prompt(workflow_json, client_id=client_id, api_base_url=endpoint.base_url)
    logger.info(
        "ComfyUI submit result: task_id=%s prompt_id=%s error=%s",
        task_id,
        result.prompt_id or "",
        result.error or "",
    )

    if result.error:
        listener_stop_event.set()
        await _set_task_status(task_id=str(task_id), status_value=TaskStatus.fail, message=result.error)
        state = _execution_states.get(task_id_str)
        if state is None:
            fail_state = _new_execution_state(task_id_str, status_value=TaskStatus.fail.value)
            fail_state["_node_map"] = _build_workflow_node_map(workflow_json)
            fail_state["target_endpoint"] = {
                "server_ip": endpoint.server_ip,
                "port": endpoint.port,
                "base_url": endpoint.base_url,
            }
            _execution_states[task_id_str] = fail_state
            state = _execution_states[task_id_str]
        state["status"] = TaskStatus.fail.value
        state["error_message"] = result.error
        state["updated_at"] = _now_iso()
        _append_event_log(task_id_str, f"提交 ComfyUI 失败: {result.error}", "error")
        await _broadcast_to_task(
            str(task_id),
            {
                "type": "listener_error",
                "data": {"message": f"ComfyUI submission failed: {result.error}"},
            },
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ComfyUI submission failed: {result.error}",
        )
    if not result.prompt_id:
        listener_stop_event.set()
        message = "ComfyUI returned empty prompt_id"
        await _set_task_status(task_id=str(task_id), status_value=TaskStatus.fail, message=message)
        state = _execution_states.get(task_id_str)
        if state is None:
            fail_state = _new_execution_state(task_id_str, status_value=TaskStatus.fail.value)
            fail_state["_node_map"] = _build_workflow_node_map(workflow_json)
            fail_state["target_endpoint"] = {
                "server_ip": endpoint.server_ip,
                "port": endpoint.port,
                "base_url": endpoint.base_url,
            }
            _execution_states[task_id_str] = fail_state
            state = _execution_states[task_id_str]
        state["status"] = TaskStatus.fail.value
        state["error_message"] = message
        state["updated_at"] = _now_iso()
        _append_event_log(task_id_str, message, "error")
        await _broadcast_to_task(
            str(task_id),
            {"type": "listener_error", "data": {"message": message}},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=message,
        )

    # Refresh running message now that submit succeeded.
    task.comfy_message = None
    await session.commit()
    prompt_ids.add(result.prompt_id)
    logger.info("Prompt id attached to listener: task_id=%s prompt_id=%s", task_id, result.prompt_id)
    state = _execution_states.get(task_id_str)
    if state is None:
        running_state = _new_execution_state(task_id_str, status_value=TaskStatus.running.value)
        running_state["_node_map"] = _build_workflow_node_map(workflow_json)
        running_state["target_endpoint"] = {
            "server_ip": endpoint.server_ip,
            "port": endpoint.port,
            "base_url": endpoint.base_url,
        }
        _execution_states[task_id_str] = running_state
        state = _execution_states[task_id_str]
    state["status"] = TaskStatus.running.value
    state["prompt_id"] = result.prompt_id
    state["prompt_ids"] = sorted(prompt_ids)
    state["target_endpoint"] = {
        "server_ip": endpoint.server_ip,
        "port": endpoint.port,
        "base_url": endpoint.base_url,
    }
    state["error_message"] = ""
    state["updated_at"] = _now_iso()
    _append_event_log(task_id_str, "执行开始", "info")
    _mark_execution_state_dirty(task_id_str)
    await _broadcast_to_task(
        task_id_str,
        {
            "type": "execution_start",
            "prompt_id": result.prompt_id,
            "data": {"prompt_id": result.prompt_id},
        },
    )
    logger.info("Execution start broadcasted: task_id=%s prompt_id=%s", task_id_str, result.prompt_id)

    return ExecuteTaskResponse(
        task_id=task.id,
        prompt_id=result.prompt_id,
        endpoint=ExecuteEndpoint(
            server_ip=endpoint.server_ip,
            port=endpoint.port,
            base_url=endpoint.base_url,
        ),
    )


@router.post("/task/{task_id}/cancel", response_model=CancelTaskResponse)
async def cancel_task_execution(
    task_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CancelTaskResponse:
    task = await get_task_or_404(session, task_id)
    task_id_str = str(task_id)
    stop_event = _listener_stop_events.get(task_id_str)

    if task.status != TaskStatus.running and stop_event is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not running",
        )

    if stop_event is not None:
        stop_event.set()
    state = _execution_states.get(task_id_str)
    if state is None:
        state = await _load_persisted_execution_state(task_id_str)
        if state is not None:
            _execution_states[task_id_str] = state

    endpoint = parse_endpoint_from_execution_state(state)
    target_base_url = endpoint.base_url if endpoint is not None else settings.comfyui_api_base_url
    prompt_ids_from_state: set[str] = set()
    if isinstance(state, dict):
        raw_prompt_id = str(state.get("prompt_id") or "").strip()
        if raw_prompt_id:
            prompt_ids_from_state.add(raw_prompt_id)
        raw_prompt_ids = state.get("prompt_ids")
        if isinstance(raw_prompt_ids, list):
            for raw in raw_prompt_ids:
                prompt_id = str(raw or "").strip()
                if prompt_id:
                    prompt_ids_from_state.add(prompt_id)

    interrupt_error: str | None = None
    queue_running_ids, queue_pending_ids, queue_error = await fetch_queue_prompt_ids(api_base_url=target_base_url)
    if queue_error:
        interrupt_error = queue_error
    else:
        operation_errors: list[str] = []
        matched_any = False
        for prompt_id in sorted(prompt_ids_from_state):
            if prompt_id in queue_pending_ids:
                matched_any = True
                delete_error = await delete_prompt_from_queue(api_base_url=target_base_url, prompt_id=prompt_id)
                if delete_error:
                    operation_errors.append(f"{prompt_id}: {delete_error}")
            elif prompt_id in queue_running_ids:
                matched_any = True
                target_interrupt_error = await interrupt_execution(api_base_url=target_base_url, prompt_id=prompt_id)
                if target_interrupt_error:
                    operation_errors.append(f"{prompt_id}: {target_interrupt_error}")

        if not matched_any and not prompt_ids_from_state:
            logger.info("Cancel requested without prompt_id yet: task_id=%s", task_id_str)

        if operation_errors:
            interrupt_error = "; ".join(operation_errors)

    message = "Execution cancelled by user"
    state = _execution_states.get(task_id_str)
    if state is None:
        state = _new_execution_state(task_id_str, status_value=TaskStatus.cancelled.value)
        state["_node_map"] = _build_workflow_node_map(task.workflow_json)
        _execution_states[task_id_str] = state

    state["status"] = TaskStatus.cancelled.value
    state["current_node_id"] = ""
    state["current_node_title"] = ""
    state["current_node_class_type"] = ""
    state["error_message"] = ""
    state["updated_at"] = _now_iso()
    _append_event_log(task_id_str, "执行已取消", "warning")
    if interrupt_error:
        _append_event_log(task_id_str, f"ComfyUI 中断请求失败: {interrupt_error}", "warning")
    _mark_execution_state_dirty(task_id_str)

    await _set_task_status(task_id=task_id_str, status_value=TaskStatus.cancelled, message=message)
    await _broadcast_to_task(
        task_id_str,
        {"type": "all_completed", "data": {"status": TaskStatus.cancelled.value}},
    )

    return CancelTaskResponse(
        task_id=task_id,
        status=TaskStatus.cancelled.value,
        message=message,
    )


# ──────────────────────────────────────────────
# WebSocket Endpoint for Frontend Progress
# ──────────────────────────────────────────────


@router.websocket("/ws/{task_id}")
async def execution_ws(websocket: WebSocket, task_id: str):
    """
    Frontend connects here to receive real-time execution progress.
    Messages are JSON objects with:
    {
        "type": "...",
        "data": { ... }
    }
    """
    await websocket.accept()

    if task_id not in _ws_connections:
        _ws_connections[task_id] = set()
    _ws_connections[task_id].add(websocket)

    logger.info("WS client connected for task %s (total: %d)", task_id, len(_ws_connections[task_id]))
    await _send_state_sync(websocket, task_id)

    try:
        while True:
            # Keep connection alive, handle pings from client
            data = await websocket.receive_text()
            # Client can send {"type": "ping"}, we respond with pong
            if data:
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections.get(task_id, set()).discard(websocket)
        if task_id in _ws_connections and not _ws_connections[task_id]:
            del _ws_connections[task_id]
        logger.info("WS client disconnected for task %s", task_id)


# ──────────────────────────────────────────────
# Background ComfyUI WS Listener
# ──────────────────────────────────────────────


async def _broadcast_to_task(task_id: str, message: dict) -> None:
    """Send a message to all connected WebSocket clients for a task."""
    clients = _ws_connections.get(task_id, set()).copy()
    for ws in clients:
        try:
            await ws.send_json(message)
        except Exception:
            _ws_connections.get(task_id, set()).discard(ws)


async def _send_state_sync(websocket: WebSocket, task_id: str) -> None:
    _ensure_cleanup_worker()
    state_snapshot = _execution_states.get(task_id)
    if state_snapshot is None:
        state_snapshot = await _load_persisted_execution_state(task_id)
        if state_snapshot is not None:
            _execution_states[task_id] = state_snapshot
    if not state_snapshot:
        return
    public_state = _public_execution_state(state_snapshot)
    if not public_state:
        return
    try:
        await websocket.send_json({"type": "state_sync", "data": public_state})
    except Exception:
        logger.debug("Failed to send state sync for task %s", task_id)


async def _load_persisted_execution_state(task_id: str) -> dict | None:
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        return None

    async with SessionLocal() as session:
        task = await session.get(Task, task_uuid)
        if not task:
            return None
        persisted = _deserialize_execution_state(task.execution_state or "")
        if persisted is None:
            # Backward compatibility for old records.
            extra = task.extra or {}
            legacy = extra.get("execution_state")
            if isinstance(legacy, dict):
                persisted = legacy
        if not isinstance(persisted, dict):
            return None
        # Defensive normalization for old records.
        persisted.setdefault("task_id", task_id)
        persisted.setdefault("status", task.status.value if task.status else TaskStatus.pending.value)
        persisted.setdefault("prompt_id", "")
        persisted.setdefault("prompt_ids", [])
        persisted.setdefault("completed_prompt_ids", [])
        persisted.setdefault("current_node_id", "")
        persisted.setdefault("current_node_title", "")
        persisted.setdefault("current_node_class_type", "")
        target_endpoint = persisted.get("target_endpoint")
        if not isinstance(target_endpoint, dict):
            target_endpoint = {}
        target_endpoint.setdefault("server_ip", "")
        target_endpoint.setdefault("port", 0)
        target_endpoint.setdefault("base_url", "")
        persisted["target_endpoint"] = target_endpoint
        progress = persisted.get("progress")
        if not isinstance(progress, dict):
            progress = {}
        progress.setdefault("node_id", "")
        progress.setdefault("node_title", "")
        progress.setdefault("node_class_type", "")
        progress.setdefault("value", 0)
        progress.setdefault("max", 0)
        persisted["progress"] = progress
        persisted.setdefault("error_message", "")
        persisted.setdefault("event_log", [])
        persisted.setdefault("updated_at", _now_iso())
        persisted["_node_map"] = _build_workflow_node_map(task.workflow_json)
        return persisted


async def _set_task_status(*, task_id: str, status_value: TaskStatus, message: str | None = None) -> None:
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        return

    async with SessionLocal() as session:
        task = await session.get(Task, task_uuid)
        if not task:
            return
        task.status = status_value
        task.comfy_message = message
        state_snapshot = _execution_states.get(task_id)
        if state_snapshot is not None:
            task.execution_state = _serialize_execution_state(state_snapshot)
        await session.commit()


async def _persist_execution_states(task_ids: list[str]) -> None:
    if not task_ids:
        return

    async with SessionLocal() as session:
        for task_id in task_ids:
            state_snapshot = _execution_states.get(task_id)
            if state_snapshot is None:
                continue
            try:
                task_uuid = UUID(task_id)
            except ValueError:
                continue
            task = await session.get(Task, task_uuid)
            if not task:
                continue
            task.execution_state = _serialize_execution_state(state_snapshot)
        await session.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_execution_state(state_snapshot: dict) -> str:
    public_state = _public_execution_state(state_snapshot) or {}
    return json.dumps(public_state, ensure_ascii=False)


def _deserialize_execution_state(raw: str) -> dict | None:
    try:
        value = json.loads(raw)
    except Exception:
        return None
    return value if isinstance(value, dict) else None


async def _run_comfyui_listener(
    *,
    client_id: str,
    task_id: str,
    ws_base_url: str,
    prompt_ids: set[str],
    stop_event: asyncio.Event | None = None,
    connected_event: asyncio.Event | None = None,
) -> None:
    """
    Background task that connects to ComfyUI WS, receives events,
    and broadcasts enriched messages to the frontend.
    """
    runtime_stop_event = stop_event or asyncio.Event()
    completed_prompts: set[str] = set()
    has_error = False
    last_error_message = ""
    finalized = False

    async def finalize_if_done() -> None:
        nonlocal finalized
        if finalized:
            return
        if not prompt_ids or completed_prompts < prompt_ids:
            return

        finalized = True
        logger.info("All prompts completed for task %s", task_id)
        final_status = TaskStatus.fail if has_error else TaskStatus.success
        final_message = last_error_message if has_error else "ComfyUI execution completed"
        logger.info(
            "Finalizing task: task_id=%s final_status=%s completed_prompt_ids=%s",
            task_id,
            final_status.value,
            sorted(completed_prompts),
        )
        state = _execution_states.get(task_id)
        if state is not None:
            state["status"] = final_status.value
            state["current_node_id"] = ""
            state["current_node_title"] = ""
            state["current_node_class_type"] = ""
            state["error_message"] = last_error_message if has_error else ""
            state["updated_at"] = _now_iso()
        if has_error:
            _append_event_log(task_id, "执行结束，存在错误", "error")
        else:
            _append_event_log(task_id, "所有节点执行完成 ✓", "success")
        await _set_task_status(task_id=task_id, status_value=final_status, message=final_message)
        await _broadcast_to_task(
            task_id,
            {"type": "all_completed", "data": {"status": final_status.value}},
        )
        runtime_stop_event.set()

    async def on_event(event: ComfyEvent) -> None:
        nonlocal has_error, last_error_message
        if runtime_stop_event.is_set():
            return
        logger.info(
            "Execution event relayed: task_id=%s type=%s prompt_id=%s node_id=%s",
            task_id,
            event.event_type,
            event.prompt_id,
            event.node_id,
        )
        message = {
            "type": event.event_type,
            "prompt_id": event.prompt_id,
            "data": {},
        }
        node_id = str(event.node_id) if event.node_id is not None else None
        node_title, node_class_type = _resolve_node_meta(task_id, node_id)
        node_display = _format_node_display(node_id, node_title, node_class_type)

        if event.event_type == "execution_start":
            # execution_start is already emitted by backend immediately after submit.
            # Avoid duplicate "执行开始" on frontend for the same prompt.
            if event.prompt_id:
                prompt_ids.add(event.prompt_id)
                state = _execution_states.get(task_id)
                if state is not None:
                    state["prompt_id"] = event.prompt_id
                    state["prompt_ids"] = sorted(prompt_ids)
                    state["updated_at"] = _now_iso()
                    _mark_execution_state_dirty(task_id)
            return

        if event.event_type == "executing":
            message["data"]["node_id"] = node_id
            message["data"]["node_title"] = node_title
            message["data"]["node_class_type"] = node_class_type
            state = _execution_states.get(task_id)
            if state is not None:
                state["current_node_id"] = node_id or ""
                state["current_node_title"] = node_title
                state["current_node_class_type"] = node_class_type
                state["updated_at"] = _now_iso()
            if node_id:
                _append_event_log(task_id, f"执行节点: {node_display}", "info")
            # node_id == None means execution of this prompt is done
            if event.node_id is None and event.prompt_id:
                completed_prompts.add(event.prompt_id)

        elif event.event_type == "progress":
            message["data"]["node_id"] = node_id
            message["data"]["node_title"] = node_title
            message["data"]["node_class_type"] = node_class_type
            message["data"]["value"] = event.progress_value
            message["data"]["max"] = event.progress_max
            state = _execution_states.get(task_id)
            if state is not None:
                state["progress"] = {
                    "node_id": node_id or "",
                    "node_title": node_title,
                    "node_class_type": node_class_type,
                    "value": int(event.progress_value or 0),
                    "max": int(event.progress_max or 0),
                }
                state["updated_at"] = _now_iso()

        elif event.event_type == "executed":
            message["data"]["node_id"] = node_id
            message["data"]["node_title"] = node_title
            message["data"]["node_class_type"] = node_class_type
            if node_id:
                _append_event_log(task_id, f"节点 {node_display} 执行完毕", "success")

        elif event.event_type == "execution_error":
            message["data"]["node_id"] = node_id
            message["data"]["node_title"] = node_title
            message["data"]["node_class_type"] = node_class_type
            message["data"]["exception_message"] = event.extra.get("exception_message")
            has_error = True
            last_error_message = event.extra.get("exception_message") or "ComfyUI execution_error"
            _append_event_log(
                task_id,
                f"节点 {node_display} 错误: {last_error_message}",
                "error",
            )
            state = _execution_states.get(task_id)
            if state is not None:
                state["status"] = TaskStatus.fail.value
                state["error_message"] = last_error_message
                state["updated_at"] = _now_iso()
            if event.prompt_id:
                completed_prompts.add(event.prompt_id)

        elif event.event_type == "execution_cached":
            nodes = event.extra.get("nodes", [])
            if not isinstance(nodes, list):
                nodes = []
            node_infos = []
            for raw_node in nodes:
                cached_node_id = str(raw_node)
                cached_title, cached_class_type = _resolve_node_meta(task_id, cached_node_id)
                node_infos.append(
                    {
                        "node_id": cached_node_id,
                        "node_title": cached_title,
                        "node_class_type": cached_class_type,
                    }
                )
            message["data"]["nodes"] = [info["node_id"] for info in node_infos]
            message["data"]["node_infos"] = node_infos
            if node_infos:
                labels = [
                    _format_node_display(info["node_id"], info["node_title"], info["node_class_type"])
                    for info in node_infos
                ]
                _append_event_log(task_id, f"缓存节点: {', '.join(labels)}", "info")

        state = _execution_states.get(task_id)
        if state is not None:
            state["completed_prompt_ids"] = sorted(completed_prompts)
            state["updated_at"] = _now_iso()
            _mark_execution_state_dirty(task_id)

        await _broadcast_to_task(task_id, message)
        await finalize_if_done()

    try:
        await listen_comfyui_ws(
            client_id,
            ws_base_url=ws_base_url,
            on_event=on_event,
            stop_event=runtime_stop_event,
            prompt_ids=prompt_ids,
            connected_event=connected_event,
        )
        # prompt_ids may be populated after early events arrive; re-check once listener returns
        await finalize_if_done()
        if not runtime_stop_event.is_set():
            message = "Lost connection to ComfyUI before completion"
            state = _execution_states.get(task_id)
            if state is not None:
                state["status"] = TaskStatus.fail.value
                state["error_message"] = message
                state["updated_at"] = _now_iso()
            _append_event_log(task_id, message, "error")
            await _set_task_status(task_id=task_id, status_value=TaskStatus.fail, message=message)
            await _broadcast_to_task(
                task_id,
                {
                    "type": "listener_error",
                    "data": {"message": message},
                },
            )
    except Exception:
        logger.exception("ComfyUI listener failed for task %s", task_id)
        state = _execution_states.get(task_id)
        if state is not None:
            state["status"] = TaskStatus.fail.value
            state["error_message"] = "Lost connection to ComfyUI"
            state["updated_at"] = _now_iso()
        _append_event_log(task_id, "Lost connection to ComfyUI", "error")
        await _set_task_status(task_id=task_id, status_value=TaskStatus.fail, message="Lost connection to ComfyUI")
        await _broadcast_to_task(
            task_id,
            {
                "type": "listener_error",
                "data": {"message": "Lost connection to ComfyUI"},
            },
        )
    finally:
        current_stop_event = _listener_stop_events.get(task_id)
        if current_stop_event is runtime_stop_event:
            _listener_stop_events.pop(task_id, None)
        listener_task = _listener_tasks.get(task_id)
        if listener_task is asyncio.current_task():
            _listener_tasks.pop(task_id, None)
