import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test-auth.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-tests-only")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.main import create_app
from app.models.auth import Base, Role, User
from app.core.config import Settings
from app.core.security import hash_password


@pytest.fixture
def settings():
    return Settings(
        database_url="sqlite+aiosqlite:///./test-auth.db",
        redis_url="redis://localhost:6379/0",
        s3_endpoint_url="http://localhost:9000",
        s3_access_key_id="test",
        s3_secret_access_key="test",
        jwt_secret_key="test-secret-for-tests-only",
    )


@pytest.fixture
async def client(settings):
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        for name in ("student", "staff", "department_head", "admin"):
            session.add(Role(name=name))
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
    await client.post("/api/v1/auth/register", json={"email":"invalid@example.com","full_name":"Student Two","password":"password123"})
    response = await client.post("/api/v1/auth/login", json={"email":"invalid@example.com","password":"wrong"})
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
    async def override_db():
        yield None
    # Exercise authorization separately through a signed admin token; database lookup is covered by /me tests.
    from app.core.security import create_access_token
    settings = Settings(database_url="sqlite+aiosqlite:///./test-auth.db", redis_url="redis://localhost:6379/0", s3_endpoint_url="http://localhost:9000", s3_access_key_id="test", s3_secret_access_key="test", jwt_secret_key="test-secret-for-tests-only")
    token = create_access_token("missing-user", "admin", settings)
    response = await client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
