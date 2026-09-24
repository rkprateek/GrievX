import io

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.config import Settings
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.auth import Role, User
from app.models.base import Base
from app.models.complaint import Complaint, ComplaintImage


class FakeStorage:
    def __init__(self):
        self.objects = {}

    def put_object(self, *, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = (Body, ContentType)

    def delete_object(self, *, Bucket, Key):
        self.objects.pop((Bucket, Key), None)


def png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
async def complaint_client(tmp_path):
    db_path = tmp_path / "complaints.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        roles = {name: Role(name=name) for name in ("student", "staff", "department_head", "admin")}
        session.add_all(roles.values())
        student = User(email="student@example.com", full_name="Student", password_hash=hash_password("password123"), role=roles["student"])
        other = User(email="other@example.com", full_name="Other", password_hash=hash_password("password123"), role=roles["student"])
        session.add_all([student, other])
        await session.commit()
        student_id, other_id = student.id, other.id

    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_path}",
        redis_url="redis://localhost:6379/0",
        s3_endpoint_url="http://localhost:9000",
        s3_access_key_id="test",
        s3_secret_access_key="test",
        jwt_secret_key="test-secret-for-tests-only",
        max_complaint_image_size_bytes=1024 * 1024,
    )
    app = create_app(settings)
    storage = FakeStorage()
    app.state.storage_client = storage
    app.state.s3_bucket = settings.s3_bucket

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, storage, session_factory, student_id, other_id
    await engine.dispose()


def auth_header(user_id: str) -> dict[str, str]:
    settings = Settings(
        database_url="sqlite+aiosqlite://",
        redis_url="redis://localhost:6379/0",
        s3_endpoint_url="http://localhost:9000",
        s3_access_key_id="test",
        s3_secret_access_key="test",
        jwt_secret_key="test-secret-for-tests-only",
    )
    token = create_access_token(user_id, "student", settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_valid_complaint_and_retrieval(complaint_client):
    client, storage, session_factory, student_id, _ = complaint_client
    response = await client.post(
        "/api/v1/complaints",
        headers=auth_header(student_id),
        data={
            "description": "Broken light near the library entrance",
            "latitude": "12.9716",
            "longitude": "77.5946",
            "location_label": "Library",
        },
        files={"image": ("evidence.png", png_bytes(), "image/png")},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "SUBMITTED"
    assert payload["id"].startswith("GRV-")
    assert len(storage.objects) == 1

    detail = await client.get(f"/api/v1/complaints/{payload['id']}", headers=auth_header(student_id))
    assert detail.status_code == 200
    assert detail.json()["history"][0]["to_status"] == "SUBMITTED"

    async with session_factory() as session:
        row = await session.scalar(select(Complaint).where(Complaint.complaint_id == payload["id"]))
        assert row is not None
        image = await session.scalar(select(ComplaintImage).where(ComplaintImage.complaint_id == row.id))
        assert image is not None


@pytest.mark.asyncio
async def test_missing_description(complaint_client):
    client, _, _, student_id, _ = complaint_client
    response = await client.post(
        "/api/v1/complaints",
        headers=auth_header(student_id),
        data={"description": "short", "latitude": "12.9", "longitude": "77.5"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_image(complaint_client):
    client, storage, _, student_id, _ = complaint_client
    response = await client.post(
        "/api/v1/complaints",
        headers=auth_header(student_id),
        data={
            "description": "This is a valid complaint description",
            "latitude": "12.9",
            "longitude": "77.5",
        },
        files={"image": ("bad.svg", b"<svg></svg>", "image/svg+xml")},
    )
    assert response.status_code == 415
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_unauthorized_submission(complaint_client):
    client, _, _, _, _ = complaint_client
    response = await client.post(
        "/api/v1/complaints",
        data={
            "description": "This is a valid complaint description",
            "latitude": "12.9",
            "longitude": "77.5",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_student_only_sees_own_complaints(complaint_client):
    client, _, _, student_id, other_id = complaint_client
    created = await client.post(
        "/api/v1/complaints",
        headers=auth_header(student_id),
        data={
            "description": "Water leakage outside the laboratory",
            "latitude": "12.9",
            "longitude": "77.5",
        },
    )
    assert created.status_code == 201
    complaint_id = created.json()["id"]
    forbidden_lookup = await client.get(f"/api/v1/complaints/{complaint_id}", headers=auth_header(other_id))
    assert forbidden_lookup.status_code == 404
