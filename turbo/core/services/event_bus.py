"""In-memory event bus for real-time updates via SSE and polling."""

import asyncio
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Maximum events kept in memory for polling (Claude Code catches up via this buffer)
MAX_BUFFER_SIZE = 1000

# Maximum subscribers before we start rejecting (prevents memory runaway)
MAX_SUBSCRIBERS = 100


@dataclass
class Event:
    """A single event emitted by the system."""

    type: str  # e.g. "issue.created", "agent.session_started"
    payload: dict  # Serializable event data
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        """Format as Server-Sent Event."""
        import json

        data = json.dumps(
            {
                "id": self.id,
                "type": self.type,
                "payload": self.payload,
                "timestamp": self.timestamp,
            }
        )
        return f"id: {self.id}\nevent: {self.type}\ndata: {data}\n\n"

    def to_dict(self) -> dict:
        """Serialize for JSON response (polling)."""
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class EventBus:
    """
    In-memory event bus with SSE streaming and polling support.

    - Web UI subscribes via SSE (long-lived connection, push events)
    - Claude Code polls via REST (GET /events?since=<timestamp>)
    - Events buffered in a deque for catch-up polling
    """

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[Event]] = []
        self._buffer: deque[Event] = deque(maxlen=MAX_BUFFER_SIZE)
        self._lock = asyncio.Lock()

    async def publish(self, event_type: str, payload: dict) -> Event:
        """
        Publish an event to all subscribers and the polling buffer.

        Called by service layer after any write operation.
        """
        event = Event(type=event_type, payload=payload)

        async with self._lock:
            self._buffer.append(event)

            # Fan out to all SSE subscribers
            dead: list[asyncio.Queue] = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Subscriber can't keep up — drop them
                    dead.append(queue)
                    logger.warning("Dropping slow SSE subscriber")

            for q in dead:
                self._subscribers.remove(q)

        logger.debug("Published event %s (id=%s)", event_type, event.id)
        return event

    async def subscribe(self) -> asyncio.Queue[Event]:
        """
        Create a new subscriber queue for SSE streaming.

        Returns an asyncio.Queue that receives events as they're published.
        Caller must call unsubscribe() when done.
        """
        async with self._lock:
            if len(self._subscribers) >= MAX_SUBSCRIBERS:
                raise RuntimeError("Too many SSE subscribers")
            queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=256)
            self._subscribers.append(queue)
            logger.info(
                "New SSE subscriber (total: %d)", len(self._subscribers)
            )
            return queue

    async def unsubscribe(self, queue: asyncio.Queue[Event]) -> None:
        """Remove a subscriber queue."""
        async with self._lock:
            try:
                self._subscribers.remove(queue)
                logger.info(
                    "SSE subscriber removed (total: %d)",
                    len(self._subscribers),
                )
            except ValueError:
                pass  # Already removed (e.g., by publish() due to QueueFull)

    def get_events_since(self, since: float) -> list[dict]:
        """
        Get buffered events after a timestamp. Used by Claude Code polling.

        Returns events as dicts, newest last.
        """
        return [e.to_dict() for e in self._buffer if e.timestamp > since]

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        """Get the most recent N events. Used for initial page load."""
        events = list(self._buffer)[-limit:]
        return [e.to_dict() for e in events]

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    @property
    def buffer_size(self) -> int:
        return len(self._buffer)


# Global singleton — same pattern as websocket_manager.py
event_bus = EventBus()
