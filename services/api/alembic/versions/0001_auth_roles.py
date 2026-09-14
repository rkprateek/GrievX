"""add authentication roles and users

Revision ID: 0001_auth_roles
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_auth_roles"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=32), nullable=False, unique=True),
    )
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_role_id", "users", ["role_id"], unique=False)
    op.create_index("ix_users_department_id", "users", ["department_id"], unique=False)
    roles = sa.table("roles", sa.column("name", sa.String))
    op.bulk_insert(roles, [{"name": role} for role in ("student", "staff", "department_head", "admin")])


def downgrade() -> None:
    op.drop_index("ix_users_department_id", table_name="users")
    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("roles")
