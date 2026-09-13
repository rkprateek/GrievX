import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database import check_database_connection


@pytest.mark.asyncio
async def test_database_connectivity_with_async_engine() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        await check_database_connection(engine)
    finally:
        await engine.dispose()
