from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.infrastructure.db_session import get_db
from app.models.auth import User
from app.realtime import realtime_manager

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/notifications")
async def notifications_socket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        payload = decode_access_token(token, get_settings())
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError
    except (JWTError, ValueError):
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    db_gen = get_db()
    db: AsyncSession = await anext(db_gen)
    try:
        user = await db.scalar(
            select(User).options(selectinload(User.role)).where(User.id == user_id, User.is_active.is_(True))
        )
        if user is None:
            await websocket.close(code=1008, reason="Invalid user")
            return

        await realtime_manager.connect(user.id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            realtime_manager.disconnect(user.id, websocket)
    finally:
        await db_gen.aclose()
