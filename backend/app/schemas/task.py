from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PhotoSourceType, TaskStatus


class PhotoBase(BaseModel):
    source_type: PhotoSourceType
    url: str
    object_key: str | None = None
    sort_order: int = 0


class PhotoRead(PhotoBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GeneratedImageBase(BaseModel):
    url: str
    object_key: str | None = None
    sort_order: int = 0
    extra: dict = Field(default_factory=dict)


class GeneratedImageRead(GeneratedImageBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SubTaskBase(BaseModel):
    platform: str = Field(min_length=1, max_length=50)
    account_name: str = Field(min_length=1, max_length=100)
    account_no: str = Field(min_length=1, max_length=100)
    publish_at: datetime | None = None
    extra: dict = Field(default_factory=dict)


class SubTaskCreate(SubTaskBase):
    photos: list[PhotoBase] = Field(default_factory=list)


class SubTaskUpdate(BaseModel):
    platform: str | None = None
    account_name: str | None = None
    account_no: str | None = None
    publish_at: datetime | None = None
    extra: dict | None = None
    photos: list[PhotoBase] | None = None


class SubTaskRead(SubTaskBase):
    id: UUID
    task_id: UUID
    status: TaskStatus
    result: dict
    created_at: datetime
    updated_at: datetime
    photos: list[PhotoRead] = Field(default_factory=list)
    generated_images: list[GeneratedImageRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    extra: dict = Field(default_factory=dict)
    subtasks: list[SubTaskCreate] = Field(default_factory=list)


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    extra: dict | None = None
    subtasks: list[SubTaskCreate] | None = None


class TaskRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    comfy_message: str | None
    extra: dict
    created_at: datetime
    updated_at: datetime
    subtasks: list[SubTaskRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class TaskListItem(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    subtask_count: int


class TaskListResponse(BaseModel):
    items: list[TaskListItem]
    total: int
    page: int
    page_size: int


class TaskDeleteResponse(BaseModel):
    id: UUID
    deleted_subtask_count: int


class TaskStatusPatchRequest(BaseModel):
    status: TaskStatus
    message: str | None = Field(default=None, max_length=2000)


class TaskStatusPatchResponse(BaseModel):
    id: UUID
    status: TaskStatus
    message: str | None = None


class SubTaskStatusPatchRequest(BaseModel):
    status: TaskStatus
    message: str | None = Field(default=None, max_length=2000)
    result: dict | None = None


class SubTaskStatusPatchResponse(BaseModel):
    id: UUID
    task_id: UUID
    status: TaskStatus
    result: dict


class CallbackSubTaskStatusRequest(BaseModel):
    subtask_id: UUID
    status: TaskStatus
    message: str | None = Field(default=None, max_length=2000)
    result: dict | None = None


class CallbackSubTaskStatusResponse(BaseModel):
    subtask_id: UUID
    subtask_status: TaskStatus
    task_id: UUID
    task_status: TaskStatus
    result: dict


class CallbackGeneratedImageItem(BaseModel):
    url: str = Field(min_length=1)
    object_key: str | None = None
    sort_order: int = Field(default=0, ge=0)
    extra: dict = Field(default_factory=dict)


class CallbackSubTaskGeneratedImagesRequest(BaseModel):
    subtask_id: UUID
    images: list[CallbackGeneratedImageItem] = Field(default_factory=list)


class CallbackSubTaskGeneratedImagesResponse(BaseModel):
    subtask_id: UUID
    task_id: UUID
    saved_count: int
    images: list[GeneratedImageRead] = Field(default_factory=list)


class TemplateSubTaskBase(BaseModel):
    platform: str = Field(min_length=1, max_length=50)
    account_name: str = Field(min_length=1, max_length=100)
    account_no: str = Field(min_length=1, max_length=100)
    publish_at: datetime | None = None
    extra: dict = Field(default_factory=dict)


class TaskTemplateCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    extra: dict = Field(default_factory=dict)
    subtasks: list[TemplateSubTaskBase] = Field(default_factory=list)


class TaskTemplatePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    extra: dict | None = None
    subtasks: list[TemplateSubTaskBase] | None = None


class TaskTemplateRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    extra: dict
    subtasks: list[TemplateSubTaskBase]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TaskTemplateListItem(BaseModel):
    id: UUID
    title: str
    description: str | None
    subtask_count: int
    created_at: datetime
    updated_at: datetime


class TaskTemplateListResponse(BaseModel):
    items: list[TaskTemplateListItem]
    total: int
    page: int
    page_size: int


class TaskTemplateDeleteResponse(BaseModel):
    id: UUID


class TaskTemplateCreateTaskRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    extra: dict | None = None
