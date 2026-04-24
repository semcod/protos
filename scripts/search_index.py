"""
search_index.py – Read Model for the search platform using SQLite FTS5.
"""

from __future__ import annotations
import sqlite3
import json
import os
import sys

class SearchIndex:
    def __init__(self, db_path: str = "search_index.db") -> None:
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            # FTS5 table for fast text searching
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

    def upsert_entry(self, entry_id: str, title: str, category: str, content: str, metadata: dict = None) -> None:
        meta_json = json.dumps(metadata or {})
        with self.conn:
            # FTS5 doesn't support traditional UPDATE with UNIQUE, so we delete and re-insert
            self.conn.execute("DELETE FROM search_entries WHERE id = ?", (entry_id,))
            self.conn.execute(
                "INSERT INTO search_entries (id, title, category, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (entry_id, title, category, content, meta_json)
            )

    def search(self, query: str, category: str = None, limit: int = 20) -> list[dict]:
        where_clauses = []
        params = []

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
