"""add complaint notifications

Revision ID: 0004_notifications
Revises: 0003_admin_complaint_management
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_notifications"
down_revision = "0003_admin_complaint_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "recipient_user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "complaint_id",
            sa.String(length=36),
            sa.ForeignKey("complaints.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"], unique=False)
    op.create_index("ix_notifications_complaint_id", "notifications", ["complaint_id"], unique=False)
    op.create_index("ix_notifications_type", "notifications", ["type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_complaint_id", table_name="notifications")
    op.drop_index("ix_notifications_recipient_user_id", table_name="notifications")
    op.drop_table("notifications")
