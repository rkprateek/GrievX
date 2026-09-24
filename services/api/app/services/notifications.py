import json
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import RoleName, User
from app.models.complaint import Complaint
from app.models.notification import Notification
from app.realtime import realtime_manager

EVENT_COMPLAINT_SUBMITTED = "COMPLAINT_SUBMITTED"
EVENT_DEPARTMENT_ASSIGNED = "DEPARTMENT_ASSIGNED"
EVENT_STAFF_ASSIGNED = "STAFF_ASSIGNED"
EVENT_STATUS_CHANGED = "STATUS_CHANGED"
EVENT_COMPLAINT_RESOLVED = "COMPLAINT_RESOLVED"


def _notification_message(event_type: str, complaint: Complaint, old_status: str | None = None) -> tuple[str, str]:
    if event_type == EVENT_COMPLAINT_SUBMITTED:
        return "Complaint submitted", f"{complaint.complaint_id} was submitted successfully."
    if event_type == EVENT_DEPARTMENT_ASSIGNED:
        return "Department assigned", f"{complaint.complaint_id} has been assigned to a department."
    if event_type == EVENT_STAFF_ASSIGNED:
        return "Staff assigned", f"{complaint.complaint_id} has been assigned to a staff member."
    if event_type == EVENT_COMPLAINT_RESOLVED:
        return "Complaint resolved", f"{complaint.complaint_id} has been marked as resolved."
    return "Complaint status updated", f"{complaint.complaint_id} changed from {old_status or 'UNKNOWN'} to {complaint.status}."


def add_notifications(
    db: AsyncSession,
    *,
    user_ids: Iterable[str],
    complaint: Complaint,
    event_type: str,
    old_status: str | None = None,
    extra: dict[str, Any] | None = None,
) -> list[Notification]:
    title, body = _notification_message(event_type, complaint, old_status)
    payload = {
        "event_type": event_type,
        "complaint_id": complaint.complaint_id,
        "status": complaint.status,
        **(extra or {}),
    }
    notifications: list[Notification] = []
    for user_id in dict.fromkeys(user_ids):
        notification = Notification(
            id=str(uuid4()),
            user_id=user_id,
            complaint_id=complaint.id,
            event_type=event_type,
            title=title,
            body=body,
            payload=json.dumps(payload, sort_keys=True),
        )
        db.add(notification)
        notifications.append(notification)
    return notifications


async def publish_notifications(notifications: Iterable[Notification]) -> None:
    for notification in notifications:
        message = {
            "type": "notification",
            "id": notification.id,
            "event_type": notification.event_type,
            "complaint_id": notification.complaint_id,
            "title": notification.title,
            "body": notification.body,
            "payload": json.loads(notification.payload) if notification.payload else {},
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat()
            if isinstance(notification.created_at, datetime)
            else datetime.now(timezone.utc).isoformat(),
        }
        await realtime_manager.send_to_user(notification.user_id, message)


async def stakeholder_user_ids(
    db: AsyncSession,
    complaint: Complaint,
    *,
    include_admins: bool = True,
    include_student: bool = True,
    include_staff: bool = True,
    include_department_heads: bool = True,
) -> set[str]:
    user_ids: set[str] = set()
    if include_student:
        user_ids.add(complaint.student_id)
    if include_staff and complaint.assigned_staff_id:
        user_ids.add(complaint.assigned_staff_id)
    if complaint.department_id and include_department_heads:
        rows = await db.scalars(
            select(User.id)
            .join(User.role)
            .where(
                User.department_id == complaint.department_id,
                User.is_active.is_(True),
                User.role.has(name=RoleName.DEPARTMENT_HEAD.value),
            )
        )
        user_ids.update(rows.all())
    if include_admins:
        rows = await db.scalars(
            select(User.id)
            .join(User.role)
            .where(User.is_active.is_(True), User.role.has(name=RoleName.ADMIN.value))
        )
        user_ids.update(rows.all())
    return user_ids
