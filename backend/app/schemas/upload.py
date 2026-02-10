from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import PhotoSourceType


class UploadImageBase64Request(BaseModel):
    base64_data: str = Field(min_length=1)
    source_type: PhotoSourceType = PhotoSourceType.paste
    filename: str | None = None
    content_type: str | None = None


class UploadImageResponse(BaseModel):
    url: str
    object_key: str
    content_type: str
    size: int
