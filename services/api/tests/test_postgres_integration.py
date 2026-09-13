import os

import pytest

from app.infrastructure.database import check_database_connection, create_database_engine


@pytest.mark.asyncio
@pytest.mark.integration
async def test_postgres_connection_when_configured() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run against PostgreSQL")

    engine = create_database_engine(database_url)
    try:
        await check_database_connection(engine)
    finally:
        await engine.dispose()
