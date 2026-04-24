"""
main.py – FastAPI gateway for the semcod/protos platform.

Entry point for the HTTP / WebSocket / SSE gateway that bridges
external clients (web, mobile, desktop) with the CQRS back-end
(EventStore + ReplayEngine defined in scripts/).

Architecture
------------

  Client (TS/Dart/Python SDK)
       │
       │  HTTP POST   ──►  /commands/user/*  ──►  user_handler  ──►  EventStore
       │                                                                  │
       │                                                          broadcast │
       │  WebSocket   ◄──  /ws               ◄──  ws.manager  ◄──────────┘
       │  SSE         ◄──  /events/stream    ◄──  sse.push_to_subscribers
       │
       │  HTTP GET    ──►  /queries/user/{id}  ──►  ReplayEngine.replay()
       │  HTTP GET    ──►  /events             ──►  EventStore.iter_all()

Run locally
-----------
    uvicorn gateway.main:app --reload --port 8080

Or via Makefile:
    make gateway
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sse_starlette.sse import EventSourceResponse

from .ws import WebSocketDisconnect, manager
from .sse import event_generator, push_to_subscribers, subscribe, unsubscribe
from .user_handler import (
    handle_change_email,
    handle_create_user,
    handle_deactivate_user,
    handle_get_user,
    handle_list_events,
    handle_dual_write_user,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown hooks)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: RUF029
    log.info("Gateway starting up…")
    yield
    log.info("Gateway shutting down…")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="semcod platform gateway",
    version="0.1.0",
    description=(
        "HTTP / WebSocket / SSE gateway — bridges external clients with the "
        "CQRS event store defined in scripts/event_store.py."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """Real-time event feed for all connected clients."""
    await manager.connect(ws)
    try:
        while True:
            # Accept keep-alive pings from clients; ignore payload
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ---------------------------------------------------------------------------
# SSE
# ---------------------------------------------------------------------------


@app.get("/events/stream", tags=["events"])
async def sse_stream(request: Request) -> EventSourceResponse:
    """Server-Sent Events stream.

    Replays all historical events first, then streams live events.
    Compatible with the EventSource browser API and curl.

    Example::

        curl -N http://localhost:8080/events/stream
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=256)
    subscribe(queue)
    return EventSourceResponse(event_generator(request, queue))


# ---------------------------------------------------------------------------
# Commands – User
# ---------------------------------------------------------------------------


class CreateUserRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class DualCreateUserRequest(CreateUserRequest):
    command_id: str
    age: int


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr


@app.post("/commands/user/create", tags=["user", "commands"], status_code=201)
async def cmd_create_user(body: CreateUserRequest) -> dict[str, Any]:
    """Issue a CreateUser command (user.v2.CreateUserCommand).

    Appends a ``UserCreated`` event to the event store and broadcasts
    it to all WebSocket and SSE subscribers.
    """
    result = handle_create_user(
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    # Broadcast to WS + SSE
    await manager.broadcast("UserCreated", result["state"])
    await push_to_subscribers("UserCreated", result["state"])
    log.info("UserCreated  id=%s  email=%s", result["id"], body.email)
    return result


@app.post("/commands/user/dual-create", tags=["user", "commands"], status_code=201)
async def cmd_dual_create_user(body: DualCreateUserRequest) -> dict[str, Any]:
    """Issue a Dual-Write CreateUser command with idempotency.
    
    Writes to both EventStore and LegacyDB parallelly.
    """
    result = handle_dual_write_user(
        command_id=body.command_id,
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        age=body.age,
    )
    # Broadcast to WS + SSE
    await manager.broadcast("UserCreated", result["state"])
    await push_to_subscribers("UserCreated", result["state"])
    log.info("DualWrite: UserCreated id=%s  email=%s  cid=%s", 
             result["aggregate_id"], body.email, body.command_id)
    return result


@app.post("/commands/user/{user_id}/change-email", tags=["user", "commands"])
async def cmd_change_email(user_id: str, body: ChangeEmailRequest) -> dict[str, Any]:
    """Change a user's email address (appends EmailChanged event)."""
    result = handle_change_email(user_id, body.new_email)
    await manager.broadcast("EmailChanged", result["state"])
    await push_to_subscribers("EmailChanged", result["state"])
    return result


@app.post("/commands/user/{user_id}/deactivate", tags=["user", "commands"])
async def cmd_deactivate_user(user_id: str) -> dict[str, Any]:
    """Deactivate a user (appends UserDeactivated event)."""
    result = handle_deactivate_user(user_id)
    await manager.broadcast("UserDeactivated", result["state"])
    await push_to_subscribers("UserDeactivated", result["state"])
    return result


# ---------------------------------------------------------------------------
# Queries – User
# ---------------------------------------------------------------------------


@app.get("/queries/user/{user_id}", tags=["user", "queries"])
async def query_get_user(user_id: str) -> dict[str, Any]:
    """Return the current projected state of a user aggregate."""
    state = handle_get_user(user_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"User {user_id!r} not found")
    return state


# ---------------------------------------------------------------------------
# Events – raw log
# ---------------------------------------------------------------------------


@app.get("/events", tags=["events"])
async def list_events(aggregate_id: str | None = None) -> list[dict[str, Any]]:
    """Return raw events from the event store.

    Optional query param: ``?aggregate_id=<uuid>``
    """
    return handle_list_events(aggregate_id)
