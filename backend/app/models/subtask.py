from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TaskStatus


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubTask(Base):
    __tablename__ = "subtasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_no: Mapped[str] = mapped_column(String(100), nullable=False)
    publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name="task_status"), default=TaskStatus.pending)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    task = relationship("Task", back_populates="subtasks")
    photos = relationship("SubTaskPhoto", back_populates="subtask", cascade="all, delete-orphan")
