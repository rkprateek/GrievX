import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-tests-only")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.models.auth import Base, Role, User


@pytest.fixture
def settings():
    return Settings(database_url="sqlite+aiosqlite://", redis_url="redis://localhost:6379/0", s3_endpoint_url="http://localhost:9000", s3_access_key_id="test", s3_secret_access_key="test", jwt_secret_key="test-secret-for-tests-only")


@pytest.fixture
async def client(settings):
    engine = create_async_engine(settings.database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        roles = {name: Role(name=name) for name in ("student", "staff", "department_head", "admin")}
        session.add_all(roles.values())
        session.add(User(email="admin@example.com", full_name="Admin", password_hash=hash_password("adminpass123"), role=roles["admin"]))
        session.add(User(email="staff@example.com", full_name="Staff", password_hash=hash_password("staffpass123"), role=roles["staff"]))
        await session.commit()

    async def override_db():
        async with session_factory() as session:
            yield session

    app = create_app(settings)
    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await engine.dispose()


@pytest.mark.asyncio
async def test_valid_login_and_me(client):
    response = await client.post("/api/v1/auth/register", json={"email":"student@example.com","full_name":"Student One","password":"password123"})
    assert response.status_code == 201
    token = response.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "student"
    assert "password" not in me.text.lower()


@pytest.mark.asyncio
async def test_invalid_login(client):
    response = await client.post("/api/v1/auth/login", json={"email":"admin@example.com","password":"wrong-password"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_request(client):
    response = await client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_student_cannot_access_admin(client):
    login = await client.post("/api/v1/auth/register", json={"email":"student2@example.com","full_name":"Student Three","password":"password123"})
    token = login.json()["access_token"]
    response = await client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_admin(client):
    login = await client.post("/api/v1/auth/login", json={"email":"admin@example.com","password":"adminpass123"})
    token = login.json()["access_token"]
    response = await client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_staff_permissions(client):
    login = await client.post("/api/v1/auth/login", json={"email":"staff@example.com","password":"staffpass123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert (await client.get("/api/v1/staff/queue", headers=headers)).status_code == 200
    assert (await client.get("/api/v1/admin/dashboard", headers=headers)).status_code == 403
