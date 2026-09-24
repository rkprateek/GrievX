"""add complaints and evidence tables

Revision ID: 0002_complaints
Revises: 0001_auth_roles
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_complaints"
down_revision = "0001_auth_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("complaint_id", sa.String(length=32), nullable=False, unique=True),
        sa.Column("student_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location_label", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="SUBMITTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_complaints_complaint_id", "complaints", ["complaint_id"], unique=False)
    op.create_index("ix_complaints_student_id", "complaints", ["student_id"], unique=False)

    op.create_table(
        "complaint_images",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("complaint_id", sa.String(length=36), sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_complaint_images_complaint_id", "complaint_images", ["complaint_id"], unique=False)

    op.create_table(
        "complaint_status_history",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("complaint_id", sa.String(length=36), sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("changed_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_complaint_status_history_complaint_id", "complaint_status_history", ["complaint_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_complaint_status_history_complaint_id", table_name="complaint_status_history")
    op.drop_table("complaint_status_history")
    op.drop_index("ix_complaint_images_complaint_id", table_name="complaint_images")
    op.drop_table("complaint_images")
    op.drop_index("ix_complaints_student_id", table_name="complaints")
    op.drop_index("ix_complaints_complaint_id", table_name="complaints")
    op.drop_table("complaints")
