"""Unit tests for the event bus."""

import asyncio
import time

import pytest

from turbo.core.services.event_bus import Event, EventBus


class TestEvent:
    """Test Event dataclass."""

    def test_create_event(self):
        event = Event(type="issue.created", payload={"id": "123"})
        assert event.type == "issue.created"
        assert event.payload == {"id": "123"}
        assert event.id  # auto-generated
        assert event.timestamp > 0

    def test_to_sse(self):
        event = Event(type="issue.created", payload={"id": "123"}, id="abc123")
        sse = event.to_sse()
        assert "id: abc123\n" in sse
        assert "event: issue.created\n" in sse
        assert "data: " in sse
        assert sse.endswith("\n\n")

    def test_to_dict(self):
        event = Event(type="test.event", payload={"key": "val"}, id="x", timestamp=1000.0)
        d = event.to_dict()
        assert d == {
            "id": "x",
            "type": "test.event",
            "payload": {"key": "val"},
            "timestamp": 1000.0,
        }


class TestEventBus:
    """Test EventBus pub/sub and polling."""

    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.mark.asyncio
    async def test_publish_stores_in_buffer(self, bus):
        await bus.publish("test.event", {"data": 1})
        assert bus.buffer_size == 1

    @pytest.mark.asyncio
    async def test_publish_returns_event(self, bus):
        event = await bus.publish("test.event", {"data": 1})
        assert isinstance(event, Event)
        assert event.type == "test.event"

    @pytest.mark.asyncio
    async def test_subscribe_receives_events(self, bus):
        queue = await bus.subscribe()
        assert bus.subscriber_count == 1

        await bus.publish("test.event", {"n": 1})

        event = queue.get_nowait()
        assert event.type == "test.event"
        assert event.payload == {"n": 1}

        await bus.unsubscribe(queue)
        assert bus.subscriber_count == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus):
        q1 = await bus.subscribe()
        q2 = await bus.subscribe()
        assert bus.subscriber_count == 2

        await bus.publish("test.event", {"n": 1})

        assert q1.get_nowait().type == "test.event"
        assert q2.get_nowait().type == "test.event"

        await bus.unsubscribe(q1)
        await bus.unsubscribe(q2)

    @pytest.mark.asyncio
    async def test_unsubscribe_idempotent(self, bus):
        queue = await bus.subscribe()
        await bus.unsubscribe(queue)
        await bus.unsubscribe(queue)  # Should not raise
        assert bus.subscriber_count == 0

    @pytest.mark.asyncio
    async def test_get_events_since(self, bus):
        t_before = time.time()
        await bus.publish("a", {"n": 1})
        await bus.publish("b", {"n": 2})

        events = bus.get_events_since(t_before - 1)
        assert len(events) == 2

        events = bus.get_events_since(time.time() + 1)
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_get_recent_events(self, bus):
        for i in range(10):
            await bus.publish("test", {"n": i})

        recent = bus.get_recent_events(limit=5)
        assert len(recent) == 5
        assert recent[0]["payload"]["n"] == 5  # offset from end
        assert recent[-1]["payload"]["n"] == 9

    @pytest.mark.asyncio
    async def test_buffer_respects_max_size(self):
        bus = EventBus()
        # Override max size for test
        bus._buffer = __import__("collections").deque(maxlen=5)

        for i in range(10):
            await bus.publish("test", {"n": i})

        assert bus.buffer_size == 5
        events = bus.get_recent_events(limit=10)
        assert len(events) == 5
        assert events[0]["payload"]["n"] == 5  # oldest kept

    @pytest.mark.asyncio
    async def test_slow_subscriber_dropped(self):
        bus = EventBus()
        # Create subscriber with tiny queue
        queue = asyncio.Queue(maxsize=1)
        async with bus._lock:
            bus._subscribers.append(queue)

        # Fill the queue
        await bus.publish("first", {})
        # This should drop the subscriber
        await bus.publish("second", {})

        assert bus.subscriber_count == 0

    @pytest.mark.asyncio
    async def test_publish_without_subscribers(self, bus):
        # Should not raise
        event = await bus.publish("test", {"data": 1})
        assert event.type == "test"
        assert bus.buffer_size == 1
