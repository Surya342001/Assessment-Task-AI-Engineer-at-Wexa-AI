
import asyncio
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.security import verify_access_token
from app.websocket.manager import manager, redis_subscriber

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/{org_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    org_id: uuid.UUID,
    token: str | None = None,
):
    """
    WebSocket endpoint for real-time updates.
    Connect with: ws://localhost:8000/api/ws/{org_id}?token=<access_token>
    """
    # Authenticate via query param token
    token_param = websocket.query_params.get("token") or token
    if token_param is None:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    token_data = verify_access_token(token_param)
    if token_data is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    org_id_str = str(org_id)
    await manager.connect(websocket, org_id_str)

    # Start Redis subscription in background
    subscriber_task = asyncio.create_task(redis_subscriber(org_id_str))

    try:
        # Send connection confirmation
        await manager.send_personal(websocket, {
            "type": "connected",
            "org_id": org_id_str,
            "message": "Connected to real-time updates",
        })

        # Keep connection alive and handle ping/pong
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
            except asyncio.TimeoutError:
                # Send heartbeat
                await manager.send_personal(websocket, {"type": "heartbeat"})
    except WebSocketDisconnect:
        logger.info("ws_client_disconnected", org_id=org_id_str)
    except Exception as e:
        logger.error("ws_error", org_id=org_id_str, error=str(e))
    finally:
        subscriber_task.cancel()
        manager.disconnect(websocket, org_id_str)
