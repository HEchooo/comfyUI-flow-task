from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.comfyui_setting import ComfyUISetting
from app.services.comfyui_service import fetch_queue_status

DEFAULT_SETTINGS_KEY = "default"


@dataclass
class ComfyUIEndpoint:
    server_ip: str
    port: int

    @property
    def base_url(self) -> str:
        return f"http://{self.server_ip}:{self.port}"


@dataclass
class ComfyUIPortRuntimeStatus:
    port: int
    base_url: str
    reachable: bool
    level: str
    running_count: int
    pending_count: int
    error: str | None = None


def normalize_server_ip(raw_server_ip: str) -> str:
    value = str(raw_server_ip or "").strip()
    if not value:
        raise ValueError("server_ip is required")

    if "://" in value:
        parsed = urlparse(value)
    else:
        parsed = urlparse(f"//{value}")

    host = parsed.hostname or ""
    host = host.strip()
    if not host:
        raise ValueError("server_ip is invalid")
    return host


def normalize_ports(raw_ports: list[int]) -> list[int]:
    ports: list[int] = []
    for raw in raw_ports:
        value = int(raw)
        if value < 1 or value > 65535:
            raise ValueError(f"Invalid port: {value}")
        ports.append(value)
    ports = sorted(set(ports))
    if not ports:
        raise ValueError("At least one port is required")
    return ports


def _parse_default_endpoint_from_env() -> ComfyUIEndpoint:
    parsed = urlparse(settings.comfyui_api_base_url)
    host = parsed.hostname or ""
    host = host.strip() or "127.0.0.1"
    port = int(parsed.port or 8188)
    return ComfyUIEndpoint(server_ip=host, port=port)


async def get_or_create_comfyui_settings(session: AsyncSession) -> ComfyUISetting:
    existing = await session.scalar(select(ComfyUISetting).where(ComfyUISetting.key == DEFAULT_SETTINGS_KEY))
    if existing:
        try:
            normalized_server_ip = normalize_server_ip(existing.server_ip)
            normalized_ports = normalize_ports([int(item) for item in (existing.ports or [])])
        except ValueError:
            default_endpoint = _parse_default_endpoint_from_env()
            normalized_server_ip = default_endpoint.server_ip
            normalized_ports = [default_endpoint.port]
        if existing.server_ip != normalized_server_ip or list(existing.ports or []) != normalized_ports:
            existing.server_ip = normalized_server_ip
            existing.ports = normalized_ports
            await session.commit()
            await session.refresh(existing)
        return existing

    default_endpoint = _parse_default_endpoint_from_env()
    created = ComfyUISetting(
        key=DEFAULT_SETTINGS_KEY,
        server_ip=default_endpoint.server_ip,
        ports=[default_endpoint.port],
    )
    session.add(created)
    await session.commit()
    await session.refresh(created)
    return created


async def update_comfyui_settings(
    session: AsyncSession,
    *,
    server_ip: str,
    ports: list[int],
) -> ComfyUISetting:
    config = await get_or_create_comfyui_settings(session)
    config.server_ip = normalize_server_ip(server_ip)
    config.ports = normalize_ports(ports)
    await session.commit()
    await session.refresh(config)
    return config


def classify_port_level(*, reachable: bool, running_count: int, pending_count: int) -> str:
    if not reachable:
        return "unreachable"
    if pending_count > 5:
        return "overloaded"
    if pending_count >= 1:
        return "queued"
    if running_count > 0:
        return "running"
    return "idle"


async def fetch_ports_runtime_status(session: AsyncSession) -> tuple[str, datetime, list[ComfyUIPortRuntimeStatus]]:
    config = await get_or_create_comfyui_settings(session)
    server_ip = normalize_server_ip(config.server_ip)
    ports = normalize_ports([int(item) for item in (config.ports or [])])
    refreshed_at = datetime.now(timezone.utc)

    async def _fetch_one(port: int) -> ComfyUIPortRuntimeStatus:
        base_url = f"http://{server_ip}:{port}"
        running_count, pending_count, error = await fetch_queue_status(api_base_url=base_url)
        reachable = error is None
        level = classify_port_level(
            reachable=reachable,
            running_count=running_count,
            pending_count=pending_count,
        )
        return ComfyUIPortRuntimeStatus(
            port=port,
            base_url=base_url,
            reachable=reachable,
            level=level,
            running_count=running_count,
            pending_count=pending_count,
            error=error,
        )

    results = await asyncio.gather(*[_fetch_one(port) for port in ports])
    return server_ip, refreshed_at, list(results)


async def ensure_allowed_endpoint(
    session: AsyncSession,
    *,
    server_ip: str,
    port: int,
) -> ComfyUIEndpoint:
    config = await get_or_create_comfyui_settings(session)
    normalized_server_ip = normalize_server_ip(server_ip)
    allowed_server_ip = normalize_server_ip(config.server_ip)
    allowed_ports = normalize_ports([int(item) for item in (config.ports or [])])

    if normalized_server_ip != allowed_server_ip:
        raise ValueError("Selected server_ip is not allowed by current settings")
    if int(port) not in allowed_ports:
        raise ValueError("Selected port is not allowed by current settings")
    if int(port) < 1 or int(port) > 65535:
        raise ValueError("Invalid port")

    return ComfyUIEndpoint(server_ip=normalized_server_ip, port=int(port))


def parse_endpoint_from_execution_state(state_snapshot: dict | None) -> ComfyUIEndpoint | None:
    if not isinstance(state_snapshot, dict):
        return None
    target = state_snapshot.get("target_endpoint")
    if not isinstance(target, dict):
        return None
    server_ip = target.get("server_ip")
    port = target.get("port")
    if server_ip is None or port is None:
        return None
    try:
        normalized_server_ip = normalize_server_ip(str(server_ip))
        normalized_port = int(port)
    except (TypeError, ValueError):
        return None
    if normalized_port < 1 or normalized_port > 65535:
        return None
    return ComfyUIEndpoint(server_ip=normalized_server_ip, port=normalized_port)
