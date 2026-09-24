from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


class ConnectionManager:
    """Per-user WebSocket connections for single-process real-time delivery.

    The interface is intentionally small so the transport can later be backed by
    Redis pub/sub when the API is horizontally scaled.
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def send_user(self, user_id: str, payload: dict[str, Any]) -> None:
        connections = list(self._connections.get(user_id, set()))
        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(user_id, websocket)

    async def send_users(self, user_ids: list[str], payload: dict[str, Any]) -> None:
        for user_id in user_ids:
            await self.send_user(user_id, payload)

    def connection_count(self, user_id: str | None = None) -> int:
        if user_id is not None:
            return len(self._connections.get(user_id, set()))
        return sum(len(items) for items in self._connections.values())


manager = ConnectionManager()


async def wait_for_disconnect(websocket: WebSocket) -> None:
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
