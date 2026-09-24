from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.realtime import manager


def notification_payload(notification: Notification) -> dict[str, Any]:
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "complaint_id": notification.complaint_id,
        "read_at": notification.read_at,
        "created_at": notification.created_at,
    }


def add_notification(
    db: AsyncSession,
    *,
    recipient_user_id: str,
    complaint_id: str | None,
    notification_type: str,
    title: str,
    message: str,
) -> Notification:
    notification = Notification(
        recipient_user_id=recipient_user_id,
        complaint_id=complaint_id,
        type=notification_type,
        title=title,
        message=message,
    )
    db.add(notification)
    return notification


async def publish_notifications(notifications: list[Notification]) -> None:
    for notification in notifications:
        await manager.send_user(notification.recipient_user_id, {
            "event": "notification",
            "notification": notification_payload(notification),
        })


async def publish_complaint_update(
    complaint_id: str,
    status: str,
    recipient_user_ids: list[str],
) -> None:
    payload = {
        "event": "complaint.updated",
        "complaint_id": complaint_id,
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await manager.send_users(list(dict.fromkeys(recipient_user_ids)), payload)
