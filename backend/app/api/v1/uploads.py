from __future__ import annotations

import json

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.schemas.upload import UploadImageBase64Request, UploadImageResponse, WorkflowUploadResponse
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


@router.post("/workflow", response_model=WorkflowUploadResponse)
async def upload_workflow(file: UploadFile = File(...)) -> WorkflowUploadResponse:
    if not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .json files are supported",
        )

    content = await file.read()
    try:
        workflow_json = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON file: {str(e)}",
        )

    if not isinstance(workflow_json, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow JSON must be an object (ComfyUI API format)",
        )

    node_count = len(workflow_json)

    return WorkflowUploadResponse(
        workflow_json=workflow_json,
        node_count=node_count,
        filename=file.filename,
    )
