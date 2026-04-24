"""
event_store.py – minimal Event Store + Replay Engine for CQRS / Event Sourcing.

This module provides:
  * EventStore – append-only SQLite-backed event log
  * ReplayEngine – rebuilds aggregate state by replaying events
  * Snapshot helpers – snapshot-based optimisation

The implementation uses the standard-library ``sqlite3`` module so that it works
with zero extra dependencies.  In production you would swap the backend for
PostgreSQL / EventStoreDB / Kafka etc.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator


# ---------------------------------------------------------------------------
# Low-level DB helpers
# ---------------------------------------------------------------------------

DDL_EVENTS = """
CREATE TABLE IF NOT EXISTS events (
    id            TEXT PRIMARY KEY,
    aggregate_id  TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    payload       TEXT NOT NULL,          -- JSON-encoded protobuf fields
    version       INTEGER NOT NULL,
    timestamp     REAL NOT NULL,
    UNIQUE (aggregate_id, version)
);
"""

DDL_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS snapshots (
    aggregate_id  TEXT PRIMARY KEY,
    state         TEXT NOT NULL,          -- JSON-encoded state
    version       INTEGER NOT NULL,
    timestamp     REAL NOT NULL
);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(DDL_EVENTS)
    conn.execute(DDL_SNAPSHOTS)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class StoredEvent:
    id: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any]
    version: int
    timestamp: float


@dataclass
class Snapshot:
    aggregate_id: str
    state: dict[str, Any]
    version: int
    timestamp: float


# ---------------------------------------------------------------------------
# Event Store
# ---------------------------------------------------------------------------


class EventStore:
    """Append-only event store backed by SQLite."""

    def __init__(self, db_path: str = "event_store.db") -> None:
        self._conn = _connect(db_path)

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def append(
        self,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any],
        expected_version: int | None = None,
    ) -> StoredEvent:
        """Append an event to the stream for *aggregate_id*.

        Parameters
        ----------
        aggregate_id:
            Identifier of the aggregate (e.g. user UUID).
        event_type:
            String name of the event (e.g. ``"UserCreated"``).
        payload:
            JSON-serialisable dict of event fields.
        expected_version:
            If provided, raises ``ValueError`` when the current version does
            not match (optimistic concurrency control).
        """
        with self._conn:
            current_version = self._current_version(aggregate_id)

            if expected_version is not None and current_version != expected_version:
                raise ValueError(
                    f"Optimistic concurrency conflict for aggregate {aggregate_id!r}: "
                    f"expected version {expected_version}, got {current_version}."
                )

            new_version = current_version + 1
            event_id = str(uuid.uuid4())
            ts = time.time()

            self._conn.execute(
                """
                INSERT INTO events (id, aggregate_id, event_type, payload, version, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, aggregate_id, event_type, json.dumps(payload), new_version, ts),
            )

        return StoredEvent(
            id=event_id,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            version=new_version,
            timestamp=ts,
        )

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def get_stream(
        self,
        aggregate_id: str,
        from_version: int = 0,
    ) -> list[StoredEvent]:
        """Return all events for *aggregate_id* ordered by version."""
        rows = self._conn.execute(
            """
            SELECT * FROM events
            WHERE aggregate_id = ? AND version > ?
            ORDER BY version ASC
            """,
            (aggregate_id, from_version),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def iter_all(self) -> Iterator[StoredEvent]:
        """Iterate over every event in the store (for projections)."""
        cursor = self._conn.execute("SELECT * FROM events ORDER BY timestamp ASC")
        for row in cursor:
            yield self._row_to_event(row)

    # ------------------------------------------------------------------
    # Snapshot helpers
    # ------------------------------------------------------------------

    def save_snapshot(self, aggregate_id: str, state: dict[str, Any], version: int) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO snapshots (aggregate_id, state, version, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(aggregate_id) DO UPDATE SET
                    state = excluded.state,
                    version = excluded.version,
                    timestamp = excluded.timestamp
                """,
                (aggregate_id, json.dumps(state), version, time.time()),
            )

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        row = self._conn.execute(
            "SELECT * FROM snapshots WHERE aggregate_id = ?", (aggregate_id,)
        ).fetchone()
        if row is None:
            return None
        return Snapshot(
            aggregate_id=row["aggregate_id"],
            state=json.loads(row["state"]),
            version=row["version"],
            timestamp=row["timestamp"],
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _current_version(self, aggregate_id: str) -> int:
        row = self._conn.execute(
            "SELECT MAX(version) AS v FROM events WHERE aggregate_id = ?",
            (aggregate_id,),
        ).fetchone()
        return row["v"] or 0

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> StoredEvent:
        return StoredEvent(
            id=row["id"],
            aggregate_id=row["aggregate_id"],
            event_type=row["event_type"],
            payload=json.loads(row["payload"]),
            version=row["version"],
            timestamp=row["timestamp"],
        )


# ---------------------------------------------------------------------------
# Replay Engine
# ---------------------------------------------------------------------------

#: Type alias for an event handler: (state, event) -> state
EventHandler = Callable[[dict[str, Any], StoredEvent], dict[str, Any]]


@dataclass
class ReplayEngine:
    """Rebuild aggregate state by replaying events from the event store.

    Parameters
    ----------
    event_store:
        The ``EventStore`` instance to read events from.
    handlers:
        Mapping of ``event_type`` → handler function.  Each handler receives
        the current state dict and the ``StoredEvent``, and must return the
        updated state dict.
    snapshot_interval:
        Automatically save a snapshot every N events processed during replay.
        Set to 0 (default) to disable automatic snapshotting.
    """

    event_store: EventStore
    handlers: dict[str, EventHandler] = field(default_factory=dict)
    snapshot_interval: int = 0

    def register(self, event_type: str) -> Callable[[EventHandler], EventHandler]:
        """Decorator to register an event handler."""

        def decorator(fn: EventHandler) -> EventHandler:
            self.handlers[event_type] = fn
            return fn

        return decorator

    def replay(
        self,
        aggregate_id: str,
        initial_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Replay events for *aggregate_id* and return the final state.

        If a snapshot exists it is used as the starting point and only
        events newer than the snapshot version are replayed.
        """
        snapshot = self.event_store.load_snapshot(aggregate_id)
        if snapshot:
            state: dict[str, Any] = dict(snapshot.state)
            from_version = snapshot.version
        else:
            state = dict(initial_state or {})
            from_version = 0

        events = self.event_store.get_stream(aggregate_id, from_version=from_version)
        events_since_snapshot = 0

        for event in events:
            handler = self.handlers.get(event.event_type)
            if handler:
                state = handler(state, event)
            events_since_snapshot += 1

            if self.snapshot_interval and events_since_snapshot % self.snapshot_interval == 0:
                self.event_store.save_snapshot(aggregate_id, state, event.version)

        return state


# ---------------------------------------------------------------------------
# Example: User aggregate handlers
# ---------------------------------------------------------------------------


def make_user_replay_engine(store: EventStore) -> ReplayEngine:
    """Return a pre-configured ``ReplayEngine`` for the User aggregate."""

    engine = ReplayEngine(event_store=store, snapshot_interval=50)

    @engine.register("UserCreated")
    def on_user_created(state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        return {
            "id": event.aggregate_id,
            "email": event.payload.get("email", ""),
            "active": True,
            "version": event.version,
        }

    @engine.register("EmailChanged")
    def on_email_changed(state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        return {**state, "email": event.payload["email"], "version": event.version}

    @engine.register("UserDeactivated")
    def on_user_deactivated(state: dict[str, Any], event: StoredEvent) -> dict[str, Any]:
        return {**state, "active": False, "version": event.version}

    return engine
