from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.schemas.upload import UploadImageBase64Request, UploadImageResponse
from app.services.upload_service import UpstreamImageUploadService, decode_base64_image

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/image", response_model=UploadImageResponse)
async def upload_image_api(request: Request, file: UploadFile | None = File(default=None)) -> UploadImageResponse:
    service = UpstreamImageUploadService()

    if file is not None:
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        result = await service.upload_image(content=content, content_type=content_type, filename=file.filename)
        return UploadImageResponse(
            url=result.url,
            object_key=result.object_key,
            content_type=result.content_type,
            size=result.size,
        )

    if request.headers.get("content-type", "").startswith("application/json"):
        payload = UploadImageBase64Request.model_validate(await request.json())
        content, content_type = decode_base64_image(payload.base64_data)
        result = await service.upload_image(
            content=content,
            content_type=payload.content_type or content_type,
            filename=payload.filename,
        )
        return UploadImageResponse(
            url=result.url,
            object_key=result.object_key,
            content_type=result.content_type,
            size=result.size,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Send either multipart file or application/json with base64_data",
    )
