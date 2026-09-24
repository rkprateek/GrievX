"""add admin complaint lifecycle and assignment management

Revision ID: 0003_admin_complaint_management
Revises: 0002_complaints
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_admin_complaint_management"
down_revision = "0002_complaints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "complaints",
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="MEDIUM"),
    )
    op.add_column(
        "complaints",
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
    )
    op.add_column(
        "complaints",
        sa.Column("assigned_staff_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_complaints_department_id", "complaints", ["department_id"], unique=False)
    op.create_index("ix_complaints_assigned_staff_id", "complaints", ["assigned_staff_id"], unique=False)

    op.create_table(
        "staff_assignments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("complaint_id", sa.String(length=36), sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("staff_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_staff_assignments_complaint_id", "staff_assignments", ["complaint_id"], unique=False)
    op.create_index("ix_staff_assignments_staff_id", "staff_assignments", ["staff_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_staff_assignments_staff_id", table_name="staff_assignments")
    op.drop_index("ix_staff_assignments_complaint_id", table_name="staff_assignments")
    op.drop_table("staff_assignments")
    op.drop_index("ix_complaints_assigned_staff_id", table_name="complaints")
    op.drop_index("ix_complaints_department_id", table_name="complaints")
    op.drop_column("complaints", "assigned_staff_id")
    op.drop_column("complaints", "department_id")
    op.drop_column("complaints", "priority")
