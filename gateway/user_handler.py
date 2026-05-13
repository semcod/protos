"""
user_handler.py – command and query handlers for the User aggregate.

Bridges the HTTP gateway layer with the EventStore + ReplayEngine defined
in scripts/event_store.py.  This module is intentionally kept thin:
all domain logic lives in the event handlers registered on the
ReplayEngine; this file is only responsible for marshalling HTTP request
data into commands/events.

Supported operations
--------------------
Commands (write):
  POST /commands/user/create       →  UserCreated event
  POST /commands/user/change-email →  EmailChanged event
  POST /commands/user/deactivate   →  UserDeactivated event

Queries (read):
  GET  /queries/user/{id}          →  ReplayEngine.replay(id)
"""

from __future__ import annotations

import os
import sys
import uuid
from typing import Any

# Allow importing scripts/ regardless of working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from event_store import EventStore, make_user_replay_engine  # noqa: E402
from dual_writer import DualWriter, LegacyDB  # noqa: E402
from idempotency_store import IdempotencyStore  # noqa: E402

# ---------------------------------------------------------------------------
# Shared EventStore instance (module-level singleton)
# ---------------------------------------------------------------------------

_store = EventStore(db_path="event_store.db")
_engine = make_user_replay_engine(_store)
_legacy_db = LegacyDB(db_path="legacy.db")
_idem_store = IdempotencyStore(db_path="idempotency.db")
_dual_writer = DualWriter(_store, _legacy_db, _idem_store)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def handle_create_user(email: str, first_name: str, last_name: str) -> dict[str, Any]:
    """Append a UserCreated event and return the new aggregate state.

    Corresponds to user.v2.CreateUserCommand.
    """
    aggregate_id = str(uuid.uuid4())
    event = _store.append(
        aggregate_id=aggregate_id,
        event_type="UserCreated",
        payload={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        },
        expected_version=0,
    )
    state = _engine.replay(aggregate_id)
    return {
        "id": aggregate_id,
        "event_id": event.id,
        "version": event.version,
        "state": state,
    }


def handle_dual_write_user(
    command_id: str, email: str, first_name: str, last_name: str, age: int
) -> dict[str, Any]:
    """Execute a dual-write (EventStore + LegacyDB) with idempotency."""
    aggregate_id = str(uuid.uuid4())
    payload = {
        "id": aggregate_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "is_active": True,
    }
    result = _dual_writer.execute_create_user(command_id, payload)

    # Replay state for consistent return format
    state = _engine.replay(result["aggregate_id"])
    return {**result, "state": state}


def handle_change_email(user_id: str, new_email: str) -> dict[str, Any]:
    """Append an EmailChanged event."""
    event = _store.append(
        aggregate_id=user_id,
        event_type="EmailChanged",
        payload={"email": new_email},
    )
    state = _engine.replay(user_id)
    return {
        "id": user_id,
        "event_id": event.id,
        "version": event.version,
        "state": state,
    }


def handle_deactivate_user(user_id: str) -> dict[str, Any]:
    """Append a UserDeactivated event."""
    event = _store.append(
        aggregate_id=user_id,
        event_type="UserDeactivated",
        payload={},
    )
    state = _engine.replay(user_id)
    return {
        "id": user_id,
        "event_id": event.id,
        "version": event.version,
        "state": state,
    }


# ---------------------------------------------------------------------------
# Query handlers
# ---------------------------------------------------------------------------


def handle_get_user(user_id: str) -> dict[str, Any] | None:
    """Replay all events for *user_id* and return the projected state.

    Returns None when no events exist for the given ID.
    """
    events = _store.get_stream(user_id)
    if not events:
        return None
    return _engine.replay(user_id)


def handle_list_events(aggregate_id: str | None = None) -> list[dict[str, Any]]:
    """Return raw event records, optionally filtered by aggregate_id."""
    if aggregate_id:
        events = _store.get_stream(aggregate_id)
    else:
        events = list(_store.iter_all())
    return [
        {
            "id": e.id,
            "aggregate_id": e.aggregate_id,
            "event_type": e.event_type,
            "payload": e.payload,
            "version": e.version,
            "timestamp": e.timestamp,
        }
        for e in events
    ]
