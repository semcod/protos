"""
search_index.py – Read Model for the search vertical slice using SQLite FTS5.

Source: ``protos/scripts/search_index.py`` (kept in sync; see package README).

This module is intentionally dependency-free (stdlib only) so that it can be
embedded into downstream applications without pulling in protogate transitive
dependencies.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any


class SearchIndex:
    """SQLite FTS5-backed search index.

    The index is a single virtual table ``search_entries`` with full-text
    columns (``title``, ``category``, ``content``) and unindexed metadata
    columns (``id``, ``metadata``).
    """

    def __init__(self, db_path: str = "search_index.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS search_entries USING fts5(
                    id UNINDEXED,
                    title,
                    category,
                    content,
                    metadata UNINDEXED
                )
                """
            )

    def upsert_entry(
        self,
        id: str,
        title: str,
        category: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Insert or replace a single entry by ``id``.

        FTS5 has no native upsert with a UNIQUE constraint, so we DELETE+INSERT.
        """
        meta_json = json.dumps(metadata or {})
        with self.conn:
            self.conn.execute("DELETE FROM search_entries WHERE id = ?", (id,))
            self.conn.execute(
                "INSERT INTO search_entries (id, title, category, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (id, title, category, content, meta_json),
            )

    def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Run a full-text search.

        Returns rows with ``id``, ``title``, ``category``, ``rank``.
        Rank is FTS5's intrinsic relevance score (lower = better).
        """
        where_clauses: list[str] = []
        params: list[Any] = []

        if query:
            where_clauses.append("search_entries MATCH ?")
            params.append(query)

        if category:
            where_clauses.append("category = ?")
            params.append(category)

        sql = "SELECT id, title, category, rank FROM search_entries"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def count(self, category: str | None = None) -> int:
        """Count indexed entries, optionally filtered by category."""
        if category:
            cursor = self.conn.execute(
                "SELECT COUNT(*) AS n FROM search_entries WHERE category = ?",
                (category,),
            )
        else:
            cursor = self.conn.execute("SELECT COUNT(*) AS n FROM search_entries")
        row = cursor.fetchone()
        return int(row["n"]) if row else 0

    def delete_entry(self, id: str) -> None:
        """Remove a single entry by ``id``."""
        with self.conn:
            self.conn.execute("DELETE FROM search_entries WHERE id = ?", (id,))

    def close(self) -> None:
        self.conn.close()
