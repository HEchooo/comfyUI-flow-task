from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.settings import ComfyUIPortStatusItem, ComfyUIPortsStatusResponse, ComfyUISettingsPayload
from app.services.comfyui_settings_service import (
    fetch_ports_runtime_status,
    get_or_create_comfyui_settings,
    normalize_ports,
    normalize_server_ip,
    update_comfyui_settings,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/comfyui", response_model=ComfyUISettingsPayload)
async def get_comfyui_settings(session: AsyncSession = Depends(get_db)) -> ComfyUISettingsPayload:
    config = await get_or_create_comfyui_settings(session)
    return ComfyUISettingsPayload(
        server_ip=normalize_server_ip(config.server_ip),
        ports=normalize_ports([int(item) for item in (config.ports or [])]),
    )


@router.put("/comfyui", response_model=ComfyUISettingsPayload)
async def put_comfyui_settings(
    payload: ComfyUISettingsPayload,
    session: AsyncSession = Depends(get_db),
) -> ComfyUISettingsPayload:
    try:
        updated = await update_comfyui_settings(
            session,
            server_ip=payload.server_ip,
            ports=payload.ports,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ComfyUISettingsPayload(
        server_ip=normalize_server_ip(updated.server_ip),
        ports=normalize_ports([int(item) for item in (updated.ports or [])]),
    )


@router.get("/comfyui/ports/status", response_model=ComfyUIPortsStatusResponse)
async def get_comfyui_port_status(session: AsyncSession = Depends(get_db)) -> ComfyUIPortsStatusResponse:
    server_ip, refreshed_at, items = await fetch_ports_runtime_status(session)
    return ComfyUIPortsStatusResponse(
        server_ip=server_ip,
        refreshed_at=refreshed_at,
        items=[
            ComfyUIPortStatusItem(
                port=item.port,
                base_url=item.base_url,
                reachable=item.reachable,
                level=item.level,
                running_count=item.running_count,
                pending_count=item.pending_count,
                error=item.error,
            )
            for item in items
        ],
    )
