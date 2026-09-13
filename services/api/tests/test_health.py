from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_returns_ok() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_dependency_failure_without_services() -> None:
    with TestClient(create_app()) as client:
        async def available() -> None:
            return None

        async def unavailable() -> None:
            raise ConnectionError("dependency unavailable")

        client.app.state.health_checks = {
            "database": available,
            "redis": unavailable,
            "object_storage": available,
        }
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"] == {
        "database": "ok",
        "redis": "unavailable",
        "object_storage": "ok",
    }
