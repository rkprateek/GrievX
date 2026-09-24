import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-tests-only")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import Settings
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.auth import Department, Role, User
from app.models.base import Base
from app.models.complaint import AuditLog, Complaint, ComplaintStatus, StaffAssignment


@pytest.fixture
def settings():
    return Settings(
        database_url="sqlite+aiosqlite://",
        redis_url="redis://localhost:6379/0",
        s3_endpoint_url="http://localhost:9000",
        s3_access_key_id="test",
        s3_secret_access_key="test",
        jwt_secret_key="test-secret-for-tests-only",
    )


@pytest.fixture
async def admin_client(settings):
    engine = create_async_engine(settings.database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        roles = {name: Role(name=name) for name in ("student", "staff", "department_head", "admin")}
        departments = {
            "maintenance": Department(name="Maintenance", code="MNT"),
            "it": Department(name="IT Services", code="IT"),
        }
        session.add_all(roles.values())
        session.add_all(departments.values())
        await session.flush()
        admin = User(email="admin@example.com", full_name="Admin User", password_hash=hash_password("adminpass123"), role=roles["admin"])
        staff = User(email="staff@example.com", full_name="Staff One", password_hash=hash_password("staffpass123"), role=roles["staff"], department=departments["maintenance"])
        other_staff = User(email="other@example.com", full_name="Other Staff", password_hash=hash_password("otherpass123"), role=roles["staff"], department=departments["it"])
        student = User(email="student@example.com", full_name="Student One", password_hash=hash_password("studentpass123"), role=roles["student"])
        session.add_all([admin, staff, other_staff, student])
        await session.flush()
        complaint_a = Complaint(
            complaint_id="GRV-ADMIN001",
            student_id=student.id,
            description="Broken light in the main library entrance",
            latitude=12.9716,
            longitude=77.5946,
            location_label="Main Library",
            department_id=departments["maintenance"].id,
            status=ComplaintStatus.SUBMITTED.value,
        )
        complaint_b = Complaint(
            complaint_id="GRV-ADMIN002",
            student_id=student.id,
            description="Wi-Fi outage in the computer laboratory",
            latitude=12.9720,
            longitude=77.5950,
            location_label="Computer Lab",
            department_id=departments["it"].id,
            status=ComplaintStatus.SUBMITTED.value,
        )
        session.add_all([complaint_a, complaint_b])
        await session.commit()
        ids = {
            "admin": admin.id,
            "staff": staff.id,
            "other_staff": other_staff.id,
            "student": student.id,
            "maintenance": departments["maintenance"].id,
            "it": departments["it"].id,
        }

    async def override_db():
        async with session_factory() as session:
            yield session

    app = create_app(settings)
    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory, ids
    await engine.dispose()


def role_header(user_id: str, role: str, settings: Settings) -> dict[str, str]:
    token = create_access_token(user_id, role, settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_access_and_dashboard_overview(admin_client, settings):
    client, _, ids = admin_client
    headers = role_header(ids["admin"], "admin", settings)
    overview = await client.get("/api/v1/admin/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["total"] == 2
    queue = await client.get("/api/v1/admin/complaints", headers=headers)
    assert queue.status_code == 200
    assert {item["id"] for item in queue.json()} == {"GRV-ADMIN001", "GRV-ADMIN002"}
    assert queue.json()[0]["student"]["email"] == "student@example.com"


@pytest.mark.asyncio
async def test_staff_is_limited_to_department_scope(admin_client, settings):
    client, _, ids = admin_client
    headers = role_header(ids["staff"], "staff", settings)
    queue = await client.get("/api/v1/admin/complaints", headers=headers)
    assert queue.status_code == 200
    assert {item["id"] for item in queue.json()} == {"GRV-ADMIN001"}
    forbidden = await client.get("/api/v1/admin/complaints/GRV-ADMIN002", headers=headers)
    assert forbidden.status_code == 404
    admin_only = await client.patch(
        "/api/v1/admin/complaints/GRV-ADMIN001/assignment",
        headers=headers,
        json={"department_id": ids["maintenance"], "staff_id": ids["staff"]},
    )
    assert admin_only.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_assign_department_and_staff(admin_client, settings):
    client, session_factory, ids = admin_client
    response = await client.patch(
        "/api/v1/admin/complaints/GRV-ADMIN001/assignment",
        headers=role_header(ids["admin"], "admin", settings),
        json={"department_id": ids["maintenance"], "staff_id": ids["staff"]},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ASSIGNED"
    assert response.json()["assigned_staff"]["id"] == ids["staff"]
    async with session_factory() as session:
        complaint = await session.scalar(select(Complaint).where(Complaint.complaint_id == "GRV-ADMIN001"))
        assignment = await session.scalar(select(StaffAssignment).where(StaffAssignment.complaint_id == complaint.id))
        logs = (await session.scalars(select(AuditLog).where(AuditLog.action == "ASSIGNMENT_CHANGED"))).all()
        assert assignment is not None
        assert assignment.staff_id == ids["staff"]
        assert logs


@pytest.mark.asyncio
async def test_admin_can_change_priority_and_status(admin_client, settings):
    client, _, ids = admin_client
    headers = role_header(ids["admin"], "admin", settings)
    assignment = await client.patch(
        "/api/v1/admin/complaints/GRV-ADMIN001/assignment",
        headers=headers,
        json={"department_id": ids["maintenance"], "staff_id": ids["staff"]},
    )
    assert assignment.status_code == 200
    priority = await client.patch(
        "/api/v1/admin/complaints/GRV-ADMIN001/priority",
        headers=headers,
        json={"priority": "HIGH"},
    )
    assert priority.status_code == 200
    assert priority.json()["priority"] == "HIGH"
    status_change = await client.patch(
        "/api/v1/admin/complaints/GRV-ADMIN001/status",
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )
    assert status_change.status_code == 200
    assert status_change.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_invalid_status_transition_is_rejected(admin_client, settings):
    client, _, ids = admin_client
    response = await client.patch(
        "/api/v1/admin/complaints/GRV-ADMIN001/status",
        headers=role_header(ids["admin"], "admin", settings),
        json={"status": "RESOLVED"},
    )
    assert response.status_code == 409
    assert "Invalid status transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_student_cannot_access_admin_complaints(admin_client, settings):
    client, _, ids = admin_client
    response = await client.get(
        "/api/v1/admin/complaints",
        headers=role_header(ids["student"], "student", settings),
    )
    assert response.status_code == 403
