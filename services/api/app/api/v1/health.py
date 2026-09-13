import asyncio
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


async def _probe(name: str, check: Callable[[], Awaitable[None]]) -> tuple[str, str]:
    try:
        await check()
    except Exception:
        return name, "unavailable"
    return name, "ok"


@router.get("/ready")
async def readiness(request: Request) -> JSONResponse:
    checks = request.app.state.health_checks
    results = await asyncio.gather(*(_probe(name, check) for name, check in checks.items()))
    dependencies = dict(results)
    healthy = all(value == "ok" for value in dependencies.values())
    body = {"status": "ok" if healthy else "degraded", "dependencies": dependencies}
    return JSONResponse(status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE, content=body)
