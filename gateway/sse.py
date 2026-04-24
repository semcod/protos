"""
sse.py – Server-Sent Events helper.

Provides an async generator that replays all historical events from the
EventStore and then streams new events pushed via an asyncio.Queue.

Usage (inside a FastAPI route):
    from gateway.sse import event_generator, subscribe, unsubscribe
    from sse_starlette.sse import EventSourceResponse

    @app.get("/events/stream")
    async def stream(request: Request):
        queue: asyncio.Queue = asyncio.Queue()
        subscribe(queue)
        return EventSourceResponse(event_generator(request, queue))
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import AsyncIterator

from starlette.requests import Request

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Subscriber registry
# ---------------------------------------------------------------------------

_subscribers: list[asyncio.Queue] = []


def subscribe(q: asyncio.Queue) -> None:
    _subscribers.append(q)
    log.debug("SSE subscriber added (total=%d)", len(_subscribers))


def unsubscribe(q: asyncio.Queue) -> None:
    try:
        _subscribers.remove(q)
    except ValueError:
        pass
    log.debug("SSE subscriber removed (total=%d)", len(_subscribers))


async def push_to_subscribers(event_type: str, payload: dict) -> None:
    """Called by command handlers after a successful append."""
    message = json.dumps({"event": event_type, "data": payload})
    dead = []
    for q in list(_subscribers):
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        unsubscribe(q)


# ---------------------------------------------------------------------------
# Async generator for EventSourceResponse
# ---------------------------------------------------------------------------


async def event_generator(
    request: Request,
    queue: asyncio.Queue,
    *,
    ping_interval: float = 15.0,
) -> AsyncIterator[dict]:
    """Yield SSE-formatted dicts for sse-starlette.

    1. First yields all historical events from the EventStore as a replay.
    2. Then streams live events from *queue*.
    3. Sends a ``ping`` comment every *ping_interval* seconds to keep the
       connection alive through proxies.
    """
    # Replay historical events from EventStore
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    from event_store import EventStore  # noqa: PLC0415

    store = EventStore()
    for ev in store.iter_all():
        if await request.is_disconnected():
            return
        yield {
            "event": ev.event_type,
            "data": json.dumps({"aggregate_id": ev.aggregate_id, **ev.payload}),
            "id": ev.id,
        }

    # Stream live events
    while True:
        if await request.is_disconnected():
            unsubscribe(queue)
            return
        try:
            message = await asyncio.wait_for(queue.get(), timeout=ping_interval)
            yield {"data": message}
        except asyncio.TimeoutError:
            yield {"comment": "ping"}
