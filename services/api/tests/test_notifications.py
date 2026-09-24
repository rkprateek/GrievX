import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-tests-only")

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.auth import Department, Role, User
from app.models.base import Base
from app.models.complaint import Complaint, ComplaintStatus, ComplaintStatusHistory
from app.models.notification import Notification, NotificationType
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
        maintenance = Department(name="Maintenance", code="MNT")
        session.add_all([*roles.values(), maintenance])
        await session.flush()
        student = User(
            email="student@example.com",
            full_name="Student One",
            password_hash=hash_password("studentpass123"),
            role=roles["student"],
        )
        staff = User(
            email="staff@example.com",
            full_name="Staff One",
            password_hash=hash_password("staffpass123"),
            role=roles["staff"],
            department=maintenance,
        )
        head = User(
            email="head@example.com",
            full_name="Maintenance Head",
            password_hash=hash_password("headpass123"),
            role=roles["department_head"],
            department=maintenance,
        )
        admin = User(
            email="admin@example.com",
            full_name="Admin User",
            password_hash=hash_password("adminpass123"),
            role=roles["admin"],
        )
        session.add_all([student, staff, head, admin])
        await session.flush()
        complaint = Complaint(
            complaint_id="GRV-LIFE001",
            student_id=student.id,
            description="Broken light in the main library entrance",
            latitude=12.9716,
            longitude=77.5946,
            location_label="Main Library",
            status=ComplaintStatus.SUBMITTED.value,
        )
        session.add(complaint)
        await session.flush()
        session.add(
            ComplaintStatusHistory(
                complaint_id=complaint.id,
                from_status=None,
                to_status=ComplaintStatus.SUBMITTED.value,
                changed_by=student.id,
            )
        )
        await session.commit()
        ids = {"student": student.id, "staff": staff.id, "head": head.id, "admin": admin.id, "department": maintenance.id}

    async def override_db():
        async with session_factory() as session:
            yield session

    app = create_app(settings)
    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory, ids, app
    await engine.dispose()


def role_header(user_id: str, role: str, settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id, role, settings)}"}


@pytest.mark.asyncio
async def test_complaint_submission_creates_notification(lifecycle_client, settings):
    client, _, ids, _ = lifecycle_client
    response = await client.post(
        "/api/v1/complaints",
        headers=role_header(ids["student"], "student", settings),
        data={
            "description": "Broken water tap near the student block",
            "latitude": "12.9716",
            "longitude": "77.5946",
            "location_label": "Student Block",
        },
    )
    assert response.status_code == 201
    complaint_id = response.json()["id"]

    notifications = await client.get(
        "/api/v1/notifications",
        headers=role_header(ids["student"], "student", settings),
    )
    assert any(
        item["type"] == NotificationType.COMPLAINT_SUBMITTED.value
        and item["complaint_id"] == response.json()["id"]
        for item in notifications.json()
    )
    assert complaint_id.startswith("GRV-")


@pytest.mark.asyncio
async def test_lifecycle_status_transition_and_history(lifecycle_client, settings):
    client, session_factory, ids, _ = lifecycle_client
    headers = role_header(ids["admin"], "admin", settings)

    assignment = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/assignment",
        headers=headers,
        json={"department_id": ids["department"], "staff_id": ids["staff"]},
    )
    assert assignment.status_code == 200
    assert assignment.json()["status"] == "ASSIGNED"

    in_progress = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/status",
        headers=headers,
        json={"status": "IN_PROGRESS"},
    )
    assert in_progress.status_code == 200

    resolved = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/status",
        headers=headers,
        json={"status": "RESOLVED"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"

    async with session_factory() as session:
        history = (
            await session.scalars(
                select(ComplaintStatusHistory)
                .join(Complaint)
                .where(Complaint.complaint_id == "GRV-LIFE001")
                .order_by(ComplaintStatusHistory.created_at)
            )
        ).all()
        assert [item.to_status for item in history] == ["SUBMITTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]


@pytest.mark.asyncio
async def test_notification_creation_and_authorization(lifecycle_client, settings):
    client, session_factory, ids, _ = lifecycle_client
    admin_headers = role_header(ids["admin"], "admin", settings)
    student_headers = role_header(ids["student"], "student", settings)

    response = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/status",
        headers=admin_headers,
        json={"status": "ASSIGNED"},
    )
    assert response.status_code == 200

    student_notifications = await client.get("/api/v1/notifications", headers=student_headers)
    assert student_notifications.status_code == 200
    types = {item["type"] for item in student_notifications.json()}
    assert NotificationType.STATUS_CHANGED.value in types

    forbidden = await client.patch(
        f"/api/v1/notifications/{student_notifications.json()[0]['id']}/read",
        headers=role_header(ids["staff"], "staff", settings),
    )
    assert forbidden.status_code == 404

    async with session_factory() as session:
        rows = (await session.scalars(
            select(Notification).where(Notification.recipient_user_id == ids["student"])
        )).all()
        assert rows


@pytest.mark.asyncio
async def test_assignment_creates_department_and_staff_notifications(lifecycle_client, settings):
    client, _, ids, _ = lifecycle_client
    response = await client.patch(
        "/api/v1/admin/complaints/GRV-LIFE001/assignment",
        headers=role_header(ids["admin"], "admin", settings),
        json={"department_id": ids["department"], "staff_id": ids["staff"]},
    )
    assert response.status_code == 200

    head_notifications = await client.get(
        "/api/v1/notifications",
        headers=role_header(ids["head"], "department_head", settings),
    )
    staff_notifications = await client.get(
        "/api/v1/notifications",
        headers=role_header(ids["staff"], "staff", settings),
    )
    assert head_notifications.status_code == 200
    assert staff_notifications.status_code == 200
    assert any(item["type"] == NotificationType.DEPARTMENT_ASSIGNED.value for item in head_notifications.json())
    assert any(item["type"] == NotificationType.STAFF_ASSIGNED.value for item in staff_notifications.json())
    

@pytest.mark.asyncio
async def test_resolved_creates_dedicated_resolved_notification(lifecycle_client, settings):
    client, _, ids, _ = lifecycle_client
    headers = role_header(ids["admin"], "admin", settings)
    for next_status in ("ASSIGNED", "IN_PROGRESS", "RESOLVED"):
        response = await client.patch(
            "/api/v1/admin/complaints/GRV-LIFE001/status",
            headers=headers,
            json={"status": next_status},
        )
        assert response.status_code == 200

    notifications = await client.get(
        "/api/v1/notifications?unread_only=true",
        headers=role_header(ids["student"], "student", settings),
    )
    assert notifications.status_code == 200
    assert any(item["type"] == NotificationType.COMPLAINT_RESOLVED.value for item in notifications.json())


@pytest.mark.asyncio
async def test_websocket_manager_delivers_realtime_event():
    manager = ConnectionManager()

    class FakeWebSocket:
        def __init__(self):
            self.messages = []

        async def accept(self):
            return None

        async def send_json(self, payload):
            self.messages.append(payload)

    socket = FakeWebSocket()
    await manager.connect("user-1", socket)
    await manager.send_user("user-1", {"event": "complaint.updated", "complaint_id": "GRV-LIFE001", "status": "RESOLVED"})
    assert socket.messages == [{"event": "complaint.updated", "complaint_id": "GRV-LIFE001", "status": "RESOLVED"}]
    assert manager.connection_count("user-1") == 1
    manager.disconnect("user-1", socket)
    assert manager.connection_count("user-1") == 0


def test_websocket_endpoint_accepts_valid_token(settings):
    get_settings.cache_clear()
    app = create_app(settings)
    token = create_access_token("user-1", "student", settings)
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/ws/notifications?token={token}") as websocket:
            assert websocket.receive_json() == {"event": "connected"}
            websocket.close()
