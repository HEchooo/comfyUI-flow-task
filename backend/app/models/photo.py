from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PhotoSourceType


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubTaskPhoto(Base):
    __tablename__ = "subtask_photos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subtask_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subtasks.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[PhotoSourceType] = mapped_column(Enum(PhotoSourceType, name="photo_source_type"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    subtask = relationship("SubTask", back_populates="photos")
