from __future__ import annotations

from enum import StrEnum


class TaskStatus(StrEnum):
    pending = "pending"
    running = "running"
    success = "success"
    fail = "fail"


class PhotoSourceType(StrEnum):
    img_url = "img_url"
    upload = "upload"
    paste = "paste"
