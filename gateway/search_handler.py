"""
search_handler.py – Handlers for the search platform vertical slice.
"""

from __future__ import annotations
import os
import sys
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from event_store import EventStore
from search_index import SearchIndex

_store = EventStore(db_path="event_store.db")
_index = SearchIndex(db_path="search_index.db")


def handle_index_entry(
    id: str, title: str, category: str, content: str, metadata: dict = None
) -> dict[str, Any]:
    # 1. Append to EventStore
    event = _store.append(
        aggregate_id=id,
        event_type="EntryIndexed",
        payload={
            "id": id,
            "title": title,
            "category": category,
            "content": content,
            "metadata": metadata,
        },
    )

    # 2. Update Read Model (Sync for this demo, usually Async)
    _index.upsert_entry(id, title, category, content, metadata)

    return {"status": "indexed", "id": id, "event_id": event.id}


def handle_search(query: str, category: str = None, limit: int = 20) -> dict[str, Any]:
    results = _index.search(query, category, limit)
    return {"results": results, "total_count": len(results)}
