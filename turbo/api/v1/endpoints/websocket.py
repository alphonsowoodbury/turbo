"""WebSocket endpoints for real-time updates."""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from turbo.api.middleware import validate_api_key_for_websocket
from turbo.core.services.agent_activity import tracker
from turbo.core.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/comments/{entity_type}/{entity_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    entity_type: str,
    entity_id: str,
    token: str = Query(default=""),
):
    """
    WebSocket endpoint for real-time comment updates.

    Clients connect to this endpoint to receive real-time notifications when:
    - New comments are created
    - Comments are updated
    - Comments are deleted

    Args:
        websocket: WebSocket connection
        entity_type: Type of entity (issue, project, milestone, etc.)
        entity_id: UUID of the entity
    """
    if not validate_api_key_for_websocket(token):
        await websocket.close(code=4001, reason="Invalid or missing token")
        return

    await manager.connect(websocket, entity_type, entity_id)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, entity_type, entity_id)
        logger.info("Client disconnected from %s:%s", entity_type, entity_id)
    except Exception:
        logger.exception("WebSocket error for %s:%s", entity_type, entity_id)
        manager.disconnect(websocket, entity_type, entity_id)


@router.websocket("/ws/agents/activity")
async def agent_activity_websocket(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """
    WebSocket endpoint for real-time agent activity updates.

    Clients connect to this endpoint to receive real-time notifications about:
    - Agent sessions starting
    - Agent status updates (processing, typing, etc.)
    - Agent sessions completing
    - Agent sessions failing

    This provides a global view of all AI agent activity across the platform.
    """
    if not validate_api_key_for_websocket(token):
        await websocket.close(code=4001, reason="Invalid or missing token")
        return

    await manager.connect_agent_activity(websocket)

    try:
        # Send initial data
        active_sessions = [s.to_dict() for s in tracker.get_all_active()]
        recent_sessions = [s.to_dict() for s in tracker.get_recent(limit=20)]
        stats = tracker.get_stats()

        await websocket.send_json({
            "type": "initial_state",
            "data": {
                "active_sessions": active_sessions,
                "recent_sessions": recent_sessions,
                "stats": stats
            }
        })

        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()

            # Echo back ping messages for keepalive
            if data == "ping":
                await websocket.send_text("pong")

            # Handle refresh request
            elif data == "refresh":
                active_sessions = [s.to_dict() for s in tracker.get_all_active()]
                stats = tracker.get_stats()
                await websocket.send_json({
                    "type": "refresh",
                    "data": {
                        "active_sessions": active_sessions,
                        "stats": stats
                    }
                })

    except WebSocketDisconnect:
        manager.disconnect_agent_activity(websocket)
        logger.info("Client disconnected from agent activity stream")
    except Exception:
        logger.exception("Agent activity WebSocket error")
        manager.disconnect_agent_activity(websocket)
