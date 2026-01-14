"""WebSocket endpoints for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from turbo.core.services.websocket_manager import manager
from turbo.core.services.agent_activity import tracker
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/comments/{entity_type}/{entity_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    entity_type: str,
    entity_id: str
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
    await manager.connect(websocket, entity_type, entity_id)

    try:
        # Keep connection alive and listen for client messages
        while True:
            # Wait for any client messages (keepalive pings, etc.)
            data = await websocket.receive_text()

            # Echo back ping messages for keepalive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, entity_type, entity_id)
        logger.info(f"Client disconnected from {entity_type}:{entity_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, entity_type, entity_id)


@router.websocket("/ws/agents/activity")
async def agent_activity_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent activity updates.

    Clients connect to this endpoint to receive real-time notifications about:
    - Agent sessions starting
    - Agent status updates (processing, typing, etc.)
    - Agent sessions completing
    - Agent sessions failing

    This provides a global view of all AI agent activity across the platform.
    """
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
    except Exception as e:
        logger.error(f"Agent activity WebSocket error: {e}")
        manager.disconnect_agent_activity(websocket)
