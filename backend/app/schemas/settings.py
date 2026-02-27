from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ComfyUISettingsPayload(BaseModel):
    server_ip: str = Field(min_length=1, max_length=255)
    ports: list[int] = Field(default_factory=list)


class ComfyUIPortStatusItem(BaseModel):
    port: int
    base_url: str
    reachable: bool
    level: str
    running_count: int = 0
    pending_count: int = 0
    error: str | None = None


class ComfyUIPortsStatusResponse(BaseModel):
    server_ip: str
    refreshed_at: datetime
    items: list[ComfyUIPortStatusItem] = Field(default_factory=list)
