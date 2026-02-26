from __future__ import annotations

from fastapi import HTTPException, status

from app.models.enums import TaskStatus

ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.pending: {TaskStatus.running, TaskStatus.fail, TaskStatus.success, TaskStatus.cancelled},
    TaskStatus.running: {TaskStatus.fail, TaskStatus.success, TaskStatus.cancelled},
    TaskStatus.success: set(),
    TaskStatus.fail: {TaskStatus.pending, TaskStatus.running, TaskStatus.cancelled},
    TaskStatus.cancelled: {TaskStatus.pending, TaskStatus.running},
}


def can_transition(current: TaskStatus, target: TaskStatus) -> bool:
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS[current]


def ensure_transition(current: TaskStatus, target: TaskStatus) -> None:
    if not can_transition(current, target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition: {current} -> {target}",
        )


def aggregate_parent_status(statuses: list[TaskStatus]) -> TaskStatus:
    if not statuses:
        return TaskStatus.pending
    if any(item == TaskStatus.fail for item in statuses):
        return TaskStatus.fail
    if any(item == TaskStatus.running for item in statuses):
        return TaskStatus.running
    if all(item == TaskStatus.cancelled for item in statuses):
        return TaskStatus.cancelled
    if all(item == TaskStatus.success for item in statuses):
        return TaskStatus.success
    return TaskStatus.pending
