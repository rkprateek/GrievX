import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.access import router as access_router
from app.api.v1.admin_complaints import router as admin_complaints_router
from app.api.v1.auth import router as auth_router
from app.api.v1.complaints import router as complaints_router
from app.api.v1.health import router as health_router
from app.core.config import Settings, get_settings
from app.infrastructure.database import check_database_connection, create_database_engine
from app.infrastructure.redis import check_redis_connection, create_redis_client
from app.infrastructure.storage import check_storage_connection, create_storage_client


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(app_settings.database_url)
        redis_client = create_redis_client(app_settings.redis_url)
        storage_client = create_storage_client(
            app_settings.s3_endpoint_url,
            app_settings.s3_access_key_id,
            app_settings.s3_secret_access_key,
            app_settings.s3_region,
        )
        app.state.storage_client = storage_client
        app.state.s3_bucket = app_settings.s3_bucket

        async def storage_check() -> None:
            await asyncio.to_thread(check_storage_connection, storage_client, app_settings.s3_bucket)

        app.state.health_checks = {
            "database": lambda: check_database_connection(engine),
            "redis": lambda: check_redis_connection(redis_client),
            "object_storage": storage_check,
        }
        try:
            yield
        finally:
            await redis_client.aclose()
            await engine.dispose()

    app = FastAPI(title="GrievX API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(access_router, prefix="/api/v1")
    app.include_router(complaints_router, prefix="/api/v1")
    app.include_router(admin_complaints_router, prefix="/api/v1")
    return app


app = create_app()
