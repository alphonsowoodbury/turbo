"""SSE and polling endpoints for real-time event streaming."""

import asyncio
import logging
import time

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from turbo.core.services.event_bus import event_bus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stream")
async def stream_events(
    since: float = Query(default=0, description="Unix timestamp — replay events after this time"),
):
    """
    SSE endpoint for real-time event streaming.

    The web UI connects here and receives push events as they happen.
    Optionally pass `since` to replay missed events on reconnect.
    """

    async def event_generator():
        queue = await event_bus.subscribe()
        try:
            # Replay missed events if client reconnects with `since`
            if since > 0:
                missed = event_bus.get_events_since(since)
                for event_dict in missed:
                    import json

                    data = json.dumps(event_dict)
                    yield f"id: {event_dict['id']}\nevent: {event_dict['type']}\ndata: {data}\n\n"

            # Stream live events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event.to_sse()
                except asyncio.TimeoutError:
                    # Send keepalive comment every 30s to prevent connection timeout
                    yield ": keepalive\n\n"

        except asyncio.CancelledError:
            pass
        finally:
            await event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/poll")
async def poll_events(
    since: float = Query(
        default=0, description="Unix timestamp — return events after this time"
    ),
    limit: int = Query(default=50, le=200, description="Max events to return"),
):
    """
    Polling endpoint for Claude Code MCP tool.

    Claude Code calls this periodically to pick up new events
    (approvals, assignments, status changes).
    """
    if since > 0:
        events = event_bus.get_events_since(since)
    else:
        events = event_bus.get_recent_events(limit=limit)

    return {
        "events": events[:limit],
        "count": len(events[:limit]),
        "server_time": time.time(),
    }


@router.get("/stats")
async def event_stats():
    """Event bus diagnostics."""
    return {
        "subscriber_count": event_bus.subscriber_count,
        "buffer_size": event_bus.buffer_size,
        "server_time": time.time(),
    }
