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
from app.models.complaint import Complaint, ComplaintStatusHistory
from app.models.notification import Notification
from app.realtime import ConnectionManager


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
async def lifecycle_client(settings):
    engine = create_async_engine(settings.database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        roles = {name: Role(name=name) for name in ("student", "staff", "department_head", "admin")}
        department = Department(name="Maintenance", code="MNT")
        session.add_all([*roles.values(), department])
        await session.flush()
        student = User(email="student@example.com", full_name="Student", password_hash=hash_password("password123"), role=roles["student"])
        admin = User(email="admin@example.com", full_name="Admin", password_hash=hash_password("password123"), role=roles["admin"])
        head = User(email="head@example.com", full_name="Head", password_hash=hash_password("password123"), role=roles["department_head"], department=department)
        staff = User(email="staff@example.com", full_name="Staff", password_hash=hash_password("password123"), role=roles["staff"], department=department)
        session.add_all([student, admin, head, staff])
        await session.flush()
        complaint = Complaint(
            complaint_id="GRV-LIFE001",
            student_id=student.id,
            description="Broken light near the library entrance",
            latitude=12.97,
            longitude=77.59,
            department_id=department.id,
        )
        session.add(complaint)
        await session.commit()
        ids = {"student": student.id, "admin": admin.id, "head": head.id, "staff": staff.id, "department": department.id}

    async def override_db():
        async with session_factory() as session:
            yield session

    app = create_app(settings)
    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory, ids
    await engine.dispose()


def headers(user_id: str, role: str, settings: Settings):
    return {"Authorization": f"Bearer {create_access_token(user_id, role, settings)}"}


@pytest.mark.asyncio
async def test_status_transition_history_and_notifications(lifecycle_client, settings):
    client, session_factory, ids = lifecycle_client
    admin_headers = headers(ids["admin"], "admin", settings)

    assignment = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/assignment",
        headers=admin_headers,
        json={"department_id": ids["department"], "staff_id": ids["staff"]},
    )
    assert assignment.status_code == 200
    assert assignment.json()["status"] == "ASSIGNED"

    progress = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/status",
        headers=admin_headers,
        json={"status": "IN_PROGRESS"},
    )
    assert progress.status_code == 200

    resolved = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/status",
        headers=admin_headers,
        json={"status": "RESOLVED"},
    )
    assert resolved.status_code == 200

    async with session_factory() as session:
        complaint = await session.scalar(select(Complaint).where(Complaint.complaint_id == "GRV-LIFE001"))
        history = (await session.scalars(
            select(ComplaintStatusHistory).where(ComplaintStatusHistory.complaint_id == complaint.id)
        )).all()
        notifications = (await session.scalars(
            select(Notification).where(Notification.complaint_id == complaint.id)
        )).all()

        assert [item.to_status for item in history] == ["ASSIGNED", "IN_PROGRESS", "RESOLVED"]
        event_types = {item.event_type for item in notifications}
        assert "DEPARTMENT_ASSIGNED" in event_types
        assert "STAFF_ASSIGNED" in event_types
        assert "STATUS_CHANGED" in event_types
        assert "COMPLAINT_RESOLVED" in event_types
        assert {item.user_id for item in notifications} >= {ids["student"], ids["admin"], ids["head"], ids["staff"]}


@pytest.mark.asyncio
async def test_invalid_transition_and_notification_authorization(lifecycle_client, settings):
    client, _, ids = lifecycle_client
    student_headers = headers(ids["student"], "student", settings)

    forbidden = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/status",
        headers=student_headers,
        json={"status": "ASSIGNED"},
    )
    assert forbidden.status_code == 403

    admin_headers = headers(ids["admin"], "admin", settings)
    invalid = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/status",
        headers=admin_headers,
        json={"status": "RESOLVED"},
    )
    assert invalid.status_code == 409

    notifications = await client.get("/api/v1/notifications", headers=student_headers)
    assert notifications.status_code == 200
    assert "items" in notifications.json()


@pytest.mark.asyncio
async def test_notification_read_is_scoped_to_owner(lifecycle_client, settings):
    client, session_factory, ids = lifecycle_client
    async with session_factory() as session:
        notification = Notification(
            user_id=ids["student"],
            complaint_id=None,
            event_type="TEST",
            title="Test",
            body="Test notification",
        )
        session.add(notification)
        await session.commit()
        notification_id = notification.id

    other_headers = headers(ids["admin"], "admin", settings)
    response = await client.patch(f"/api/v1/notifications/{notification_id}/read", headers=other_headers)
    assert response.status_code == 404

    student_headers = headers(ids["student"], "student", settings)
    response = await client.patch(f"/api/v1/notifications/{notification_id}/read", headers=student_headers)
    assert response.status_code == 200
    assert response.json()["is_read"] is True


@pytest.mark.asyncio
async def test_realtime_manager_broadcast_is_testable():
    class FakeWebSocket:
        def __init__(self):
            self.messages = []
            self.accepted = False

        async def accept(self):
            self.accepted = True

        async def send_json(self, message):
            self.messages.append(message)

    manager = ConnectionManager()
    socket = FakeWebSocket()
    await manager.connect("user-1", socket)
    await manager.broadcast_to_users({"user-1"}, {"type": "notification", "event_type": "TEST"})
    assert socket.accepted is True
    assert socket.messages == [{"type": "notification", "event_type": "TEST"}]
    manager.disconnect("user-1", socket)
