from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """In-process realtime hub.

    The API is intentionally WebSocket-first. A future multi-instance deployment can
    fan events through Redis without changing the client protocol or notification API.
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

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        connections = list(self._connections.get(user_id, set()))
        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(user_id, websocket)

    async def broadcast_to_users(self, user_ids: set[str], message: dict[str, Any]) -> None:
        for user_id in user_ids:
            await self.send_to_user(user_id, message)


realtime_manager = ConnectionManager()
