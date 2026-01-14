"""WebSocket connection manager for real-time updates."""

from typing import Dict, List, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # Dict mapping entity keys to sets of active connections
        # Key format: "entity_type:entity_id"
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Global agent activity connections
        self.agent_activity_connections: Set[WebSocket] = set()

    def _get_room_key(self, entity_type: str, entity_id: str) -> str:
        """Generate room key for entity."""
        return f"{entity_type}:{entity_id}"

    async def connect(self, websocket: WebSocket, entity_type: str, entity_id: str):
        """Accept new WebSocket connection and add to room."""
        await websocket.accept()
        room_key = self._get_room_key(entity_type, entity_id)

        if room_key not in self.active_connections:
            self.active_connections[room_key] = set()

        self.active_connections[room_key].add(websocket)
        logger.info(f"Client connected to {room_key}. Total connections: {len(self.active_connections[room_key])}")

    def disconnect(self, websocket: WebSocket, entity_type: str, entity_id: str):
        """Remove WebSocket connection from room."""
        room_key = self._get_room_key(entity_type, entity_id)

        if room_key in self.active_connections:
            self.active_connections[room_key].discard(websocket)
            logger.info(f"Client disconnected from {room_key}. Total connections: {len(self.active_connections[room_key])}")

            # Clean up empty rooms
            if not self.active_connections[room_key]:
                del self.active_connections[room_key]

    async def broadcast(self, entity_type: str, entity_id: str, message: dict):
        """Broadcast message to all clients in room."""
        room_key = self._get_room_key(entity_type, entity_id)

        if room_key not in self.active_connections:
            return

        # Get snapshot of connections to avoid modification during iteration
        connections = list(self.active_connections[room_key])
        disconnected = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.active_connections[room_key].discard(connection)

    async def send_comment_created(self, entity_type: str, entity_id: str, comment_data: dict):
        """Send comment created event to all clients in room."""
        await self.broadcast(entity_type, entity_id, {
            "type": "comment_created",
            "data": comment_data
        })

    async def send_comment_updated(self, entity_type: str, entity_id: str, comment_data: dict):
        """Send comment updated event to all clients in room."""
        await self.broadcast(entity_type, entity_id, {
            "type": "comment_updated",
            "data": comment_data
        })

    async def send_comment_deleted(self, entity_type: str, entity_id: str, comment_id: str):
        """Send comment deleted event to all clients in room."""
        await self.broadcast(entity_type, entity_id, {
            "type": "comment_deleted",
            "data": {"id": comment_id}
        })

    async def send_ai_typing_start(self, entity_type: str, entity_id: str, author_name: str = "Claude"):
        """Send AI typing start event to all clients in room."""
        await self.broadcast(entity_type, entity_id, {
            "type": "ai_typing_start",
            "data": {"author_name": author_name}
        })

    async def send_ai_typing_stop(self, entity_type: str, entity_id: str, author_name: str = "Claude"):
        """Send AI typing stop event to all clients in room."""
        await self.broadcast(entity_type, entity_id, {
            "type": "ai_typing_stop",
            "data": {"author_name": author_name}
        })

    # Global Agent Activity Methods

    async def connect_agent_activity(self, websocket: WebSocket):
        """Connect client to global agent activity stream."""
        await websocket.accept()
        self.agent_activity_connections.add(websocket)
        logger.info(f"Client connected to agent activity. Total: {len(self.agent_activity_connections)}")

    def disconnect_agent_activity(self, websocket: WebSocket):
        """Disconnect client from global agent activity stream."""
        self.agent_activity_connections.discard(websocket)
        logger.info(f"Client disconnected from agent activity. Total: {len(self.agent_activity_connections)}")

    async def broadcast_agent_activity(self, message: dict):
        """Broadcast message to all agent activity subscribers."""
        if not self.agent_activity_connections:
            return

        connections = list(self.agent_activity_connections)
        disconnected = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending agent activity to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.agent_activity_connections.discard(connection)

    async def send_agent_started(self, session_data: dict):
        """Broadcast agent session started event."""
        await self.broadcast_agent_activity({
            "type": "agent_started",
            "data": session_data
        })

    async def send_agent_status_update(self, session_data: dict):
        """Broadcast agent status update event."""
        await self.broadcast_agent_activity({
            "type": "agent_status_update",
            "data": session_data
        })

    async def send_agent_completed(self, session_data: dict):
        """Broadcast agent session completed event."""
        await self.broadcast_agent_activity({
            "type": "agent_completed",
            "data": session_data
        })

    async def send_agent_failed(self, session_data: dict):
        """Broadcast agent session failed event."""
        await self.broadcast_agent_activity({
            "type": "agent_failed",
            "data": session_data
        })


# Global singleton instance
manager = ConnectionManager()
