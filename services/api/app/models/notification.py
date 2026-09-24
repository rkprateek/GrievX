from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.auth import User
from app.models.base import Base


class NotificationType(str, Enum):
    COMPLAINT_SUBMITTED = "COMPLAINT_SUBMITTED"
    DEPARTMENT_ASSIGNED = "DEPARTMENT_ASSIGNED"
    STAFF_ASSIGNED = "STAFF_ASSIGNED"
    STATUS_CHANGED = "STATUS_CHANGED"
    COMPLAINT_RESOLVED = "COMPLAINT_RESOLVED"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recipient_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    complaint_id: Mapped[str | None] = mapped_column(
        ForeignKey("complaints.id", ondelete="CASCADE"), index=True, nullable=True
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    recipient: Mapped[User] = relationship()
