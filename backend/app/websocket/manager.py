
import asyncio
import json
from collections import defaultdict
from typing import Any

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with org-level isolation."""

    def __init__(self) -> None:
        # org_id -> set of WebSocket connections
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, org_id: str) -> None:
        await websocket.accept()
        self._connections[org_id].add(websocket)
        logger.info("ws_connected", org_id=org_id, total=len(self._connections[org_id]))

    def disconnect(self, websocket: WebSocket, org_id: str) -> None:
        self._connections[org_id].discard(websocket)
        if not self._connections[org_id]:
            del self._connections[org_id]
        logger.info("ws_disconnected", org_id=org_id)

    async def broadcast_to_org(self, org_id: str, message: dict[str, Any]) -> None:
        """Send a message to all WebSocket connections in an org."""
        connections = self._connections.get(org_id, set()).copy()
        if not connections:
            return

        dead_connections: set[WebSocket] = set()
        payload = json.dumps(message, default=str)

        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_connections.add(ws)

        # Clean up dead connections
        for ws in dead_connections:
            self._connections[org_id].discard(ws)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        payload = json.dumps(message, default=str)
        await websocket.send_text(payload)

    def get_connection_count(self, org_id: str) -> int:
        return len(self._connections.get(org_id, set()))


manager = ConnectionManager()


async def redis_subscriber(org_id: str) -> None:
    """Subscribe to Redis pub/sub channels and forward to WebSocket clients."""
    import redis.asyncio as aioredis
    from app.config import settings

    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis.pubsub()

    channels = [
        f"org:{org_id}:events",
        f"org:{org_id}:alerts",
    ]
    await pubsub.subscribe(*channels)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast_to_org(org_id, data)
                except json.JSONDecodeError:
                    pass
    finally:
        await pubsub.unsubscribe(*channels)
        await redis.aclose()
