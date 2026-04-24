"""
dual_writer.py – implementation of dual-write pattern with idempotency.
Writes to both the modern EventStore and a legacy database (simulated).
"""

from __future__ import annotations
import json
import logging
import sqlite3
import os
import sys
from typing import Any, Callable

sys.path.insert(0, os.path.dirname(__file__))

from event_store import EventStore
from idempotency_store import IdempotencyStore

log = logging.getLogger(__name__)


class LegacyDB:
    """Simulated legacy database."""
    def __init__(self, db_path: str = "legacy.db") -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    age INTEGER,
                    is_active BOOLEAN
                )
                """
            )

    def upsert_user(self, user_data: dict[str, Any]) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO users (id, email, first_name, last_name, age, is_active)
                VALUES (:id, :email, :first_name, :last_name, :age, :is_active)
                ON CONFLICT(id) DO UPDATE SET
                    email = excluded.email,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    age = excluded.age,
                    is_active = excluded.is_active
                """,
                user_data
            )

    def get_all_users(self) -> list[dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM users")
        return [dict(row) for row in cursor.fetchall()]


class DualWriter:
    def __init__(
        self, 
        event_store: EventStore, 
        legacy_db: LegacyDB, 
        idempotency_store: IdempotencyStore
    ) -> None:
        self.event_store = event_store
        self.legacy_db = legacy_db
        self.idem_store = idempotency_store

    def execute_create_user(self, command_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Dual-write: EventStore + LegacyDB.
        Uses command_id for idempotency.
        """
        if self.idem_store.is_processed(command_id):
            log.info("Command %s already processed. Returning cached response.", command_id)
            cached = self.idem_store.get_response(command_id)
            return json.loads(cached) if cached else {"status": "already_processed"}

        # 1. Write to Event Store (Source of Truth)
        aggregate_id = payload.get("id") or str(json.dumps(payload)) # simplified hash
        event = self.event_store.append(
            aggregate_id=payload["id"],
            event_type="UserCreated",
            payload=payload
        )

        # 2. Write to Legacy DB (Read Model / Legacy Storage)
        # Note: In a real system, this might be done asynchronously or 
        # inside a distributed transaction if absolute consistency is required.
        try:
            self.legacy_db.upsert_user(payload)
        except Exception as e:
            log.error("Failed to write to Legacy DB for command %s: %s", command_id, e)
            # Strategy: We could retry, or leave it for an out-of-sync checker.
            # Since EventStore (SOT) succeeded, we don't necessarily fail the whole thing.

        response = {
            "status": "success",
            "event_id": event.id,
            "aggregate_id": event.aggregate_id,
            "version": event.version
        }

        # 3. Mark as processed
        self.idem_store.mark_processed(command_id, json.dumps(response))
        
        return response
