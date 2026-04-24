"""
idempotency_store.py – simple SQLite-backed idempotency check.
"""

from __future__ import annotations
import sqlite3
import time


class IdempotencyStore:
    def __init__(self, db_path: str = "idempotency.db") -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    key         TEXT PRIMARY KEY,
                    timestamp   REAL NOT NULL,
                    response    TEXT      -- Optional: cached response
                )
                """
            )

    def is_processed(self, key: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM idempotency_keys WHERE key = ?", (key,)).fetchone()
        return row is not None

    def mark_processed(self, key: str, response: str | None = None) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO idempotency_keys (key, timestamp, response) VALUES (?, ?, ?)",
                (key, time.time(), response),
            )

    def get_response(self, key: str) -> str | None:
        row = self.conn.execute("SELECT response FROM idempotency_keys WHERE key = ?", (key,)).fetchone()
        return row["response"] if row else None
