from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Awaitable, Callable
from urllib.parse import urlparse, urlunparse

import httpx
import websockets

logger = logging.getLogger("app.comfyui")


# ──────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────


@dataclass
class PromptSubmitResult:
    prompt_id: str
    error: str | None = None


@dataclass
class ComfyEvent:
    """Normalized event from ComfyUI WebSocket."""
    event_type: str  # e.g., "execution_start", "executing", "progress", "executed", "execution_error"
    prompt_id: str | None = None
    node_id: str | None = None
    node_type: str | None = None
    progress_value: int | None = None
    progress_max: int | None = None
    extra: dict = field(default_factory=dict)


# ──────────────────────────────────────────────
# HTTP Client -- Submit prompt to ComfyUI
# ──────────────────────────────────────────────


async def submit_prompt(workflow_json: dict, *, client_id: str, api_base_url: str) -> PromptSubmitResult:
    """
    POST the workflow to ComfyUI /api/prompt.

    Payload format expected by ComfyUI:
    {
        "prompt": { ... workflow nodes ... },
        "client_id": "unique-id"
    }
    """
    node_count = len(workflow_json) if isinstance(workflow_json, dict) else -1
    api_url = f"{api_base_url.rstrip('/')}/api/prompt"
    logger.info("Submitting prompt to ComfyUI: api_url=%s client_id=%s node_count=%s", api_url, client_id, node_count)

    payload = {
        "prompt": workflow_json,
        "client_id": client_id,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=payload)
    except httpx.HTTPError as exc:
        logger.exception("ComfyUI /api/prompt request failed: %s", exc)
        return PromptSubmitResult(
            prompt_id="",
            error=f"HTTP request error: {exc}",
        )

    if response.status_code != 200:
        logger.error(
            "ComfyUI /api/prompt returned %s: %s",
            response.status_code,
            response.text[:500],
        )
        return PromptSubmitResult(
            prompt_id="",
            error=f"ComfyUI returned HTTP {response.status_code}: {response.text[:200]}",
        )

    try:
        data = response.json()
    except json.JSONDecodeError:
        logger.error("ComfyUI /api/prompt response is not valid JSON: %s", response.text[:500])
        return PromptSubmitResult(
            prompt_id="",
            error="ComfyUI returned non-JSON response",
        )

    prompt_id = data.get("prompt_id", "")
    node_errors = data.get("node_errors", {})
    logger.info(
        "ComfyUI /api/prompt accepted: prompt_id=%s has_node_errors=%s response_keys=%s",
        prompt_id,
        bool(node_errors),
        sorted(data.keys()),
    )

    if node_errors:
        logger.warning("ComfyUI node errors for prompt %s: %s", prompt_id, node_errors)

    return PromptSubmitResult(prompt_id=prompt_id)


async def interrupt_execution(*, api_base_url: str, prompt_id: str | None = None) -> str | None:
    """
    Best-effort interrupt for current ComfyUI execution.
    Returns None on success, otherwise an error message.
    """
    interrupt_url = f"{api_base_url.rstrip('/')}/interrupt"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if prompt_id:
                response = await client.post(interrupt_url, json={"prompt_id": prompt_id})
            else:
                response = await client.post(interrupt_url)
    except httpx.HTTPError as exc:
        logger.exception("ComfyUI /interrupt request failed: %s", exc)
        return f"HTTP request error: {exc}"

    if response.status_code not in {200, 204}:
        logger.error(
            "ComfyUI /interrupt returned %s: %s",
            response.status_code,
            response.text[:500],
        )
        return f"ComfyUI interrupt returned HTTP {response.status_code}"

    logger.info("ComfyUI interrupt requested successfully")
    return None


# ──────────────────────────────────────────────
# WebSocket Client -- Listen to ComfyUI events
# ──────────────────────────────────────────────


async def listen_comfyui_ws(
    client_id: str,
    *,
    ws_base_url: str,
    on_event: Callable[[ComfyEvent], Awaitable[None]],
    stop_event: asyncio.Event,
    prompt_ids: set[str] | None = None,
    connected_event: asyncio.Event | None = None,
) -> None:
    """
    Connect to ComfyUI WebSocket and relay events.

    Args:
        client_id: The client_id used when submitting prompts.
        on_event: Async callback invoked for each relevant event.
        stop_event: Set this to gracefully terminate the listener.
        prompt_ids: If provided, only emit events for these prompt IDs.
    """
    ws_url = f"{ws_base_url.rstrip('/')}/ws?clientId={client_id}"
    logger.info("Connecting to ComfyUI WS: %s", ws_url)

    try:
        async with websockets.connect(ws_url) as ws:
            logger.info("Connected to ComfyUI WS: client_id=%s", client_id)
            if connected_event is not None:
                connected_event.set()
            while not stop_event.is_set():
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except websockets.ConnectionClosed:
                    logger.warning("ComfyUI WS connection closed")
                    break

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                event = _parse_comfy_message(msg)
                if event is None:
                    continue

                # Filter to relevant prompt IDs if specified
                if prompt_ids and event.prompt_id and event.prompt_id not in prompt_ids:
                    continue

                if event.event_type in {
                    "execution_start",
                    "executing",
                    "executed",
                    "execution_error",
                    "execution_cached",
                }:
                    logger.info(
                        "ComfyUI event: type=%s prompt_id=%s node_id=%s",
                        event.event_type,
                        event.prompt_id,
                        event.node_id,
                    )

                try:
                    await on_event(event)
                except Exception:
                    logger.exception("Error in on_event callback")

    except Exception:
        logger.exception("ComfyUI WS listener error")


def build_ws_base_url(api_base_url: str) -> str:
    parsed = urlparse(api_base_url.rstrip("/"))
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse((scheme, parsed.netloc, "", "", "", "")).rstrip("/")


async def fetch_queue_status(*, api_base_url: str) -> tuple[int, int, str | None]:
    queue_url = f"{api_base_url.rstrip('/')}/queue"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(queue_url)
    except httpx.HTTPError as exc:
        return 0, 0, f"HTTP request error: {exc}"

    if response.status_code != 200:
        return 0, 0, f"ComfyUI returned HTTP {response.status_code}"

    try:
        data = response.json()
    except json.JSONDecodeError:
        return 0, 0, "ComfyUI returned non-JSON queue response"

    queue_running = data.get("queue_running")
    queue_pending = data.get("queue_pending")
    running_count = len(queue_running) if isinstance(queue_running, list) else 0
    pending_count = len(queue_pending) if isinstance(queue_pending, list) else 0
    return running_count, pending_count, None


def _extract_prompt_ids_from_queue_entries(entries: list) -> set[str]:
    prompt_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, (list, tuple)):
            continue
        if len(entry) < 2:
            continue
        prompt_id = str(entry[1] or "").strip()
        if prompt_id:
            prompt_ids.add(prompt_id)
    return prompt_ids


async def fetch_queue_prompt_ids(*, api_base_url: str) -> tuple[set[str], set[str], str | None]:
    queue_url = f"{api_base_url.rstrip('/')}/queue"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(queue_url)
    except httpx.HTTPError as exc:
        return set(), set(), f"HTTP request error: {exc}"

    if response.status_code != 200:
        return set(), set(), f"ComfyUI returned HTTP {response.status_code}"

    try:
        data = response.json()
    except json.JSONDecodeError:
        return set(), set(), "ComfyUI returned non-JSON queue response"

    queue_running = data.get("queue_running")
    queue_pending = data.get("queue_pending")
    running_ids = _extract_prompt_ids_from_queue_entries(queue_running if isinstance(queue_running, list) else [])
    pending_ids = _extract_prompt_ids_from_queue_entries(queue_pending if isinstance(queue_pending, list) else [])
    return running_ids, pending_ids, None


async def delete_prompt_from_queue(*, api_base_url: str, prompt_id: str) -> str | None:
    queue_url = f"{api_base_url.rstrip('/')}/queue"
    normalized_prompt_id = str(prompt_id or "").strip()
    if not normalized_prompt_id:
        return "prompt_id is required"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(queue_url, json={"delete": [normalized_prompt_id]})
    except httpx.HTTPError as exc:
        logger.exception("ComfyUI /queue delete request failed: %s", exc)
        return f"HTTP request error: {exc}"

    if response.status_code not in {200, 204}:
        logger.error(
            "ComfyUI /queue delete returned %s: %s",
            response.status_code,
            response.text[:500],
        )
        return f"ComfyUI queue delete returned HTTP {response.status_code}"

    return None


def _parse_comfy_message(msg: dict) -> ComfyEvent | None:
    """Parse a raw ComfyUI WebSocket message into a ComfyEvent."""
    msg_type = msg.get("type")
    data = msg.get("data", {})

    if msg_type == "status":
        # Queue status updates
        return ComfyEvent(
            event_type="status",
            extra=data,
        )

    elif msg_type == "execution_start":
        return ComfyEvent(
            event_type="execution_start",
            prompt_id=data.get("prompt_id"),
        )

    elif msg_type == "executing":
        # node_id is None when execution is complete
        node_id = data.get("node")
        return ComfyEvent(
            event_type="executing",
            prompt_id=data.get("prompt_id"),
            node_id=node_id,
        )

    elif msg_type == "progress":
        return ComfyEvent(
            event_type="progress",
            prompt_id=data.get("prompt_id"),
            node_id=data.get("node"),
            progress_value=data.get("value"),
            progress_max=data.get("max"),
        )

    elif msg_type == "executed":
        return ComfyEvent(
            event_type="executed",
            prompt_id=data.get("prompt_id"),
            node_id=data.get("node"),
            extra={"output": data.get("output", {})},
        )

    elif msg_type == "execution_error":
        return ComfyEvent(
            event_type="execution_error",
            prompt_id=data.get("prompt_id"),
            node_id=data.get("node"),
            node_type=data.get("node_type"),
            extra={
                "exception_message": data.get("exception_message"),
                "exception_type": data.get("exception_type"),
            },
        )

    elif msg_type == "execution_cached":
        return ComfyEvent(
            event_type="execution_cached",
            prompt_id=data.get("prompt_id"),
            extra={"nodes": data.get("nodes", [])},
        )

    return None
