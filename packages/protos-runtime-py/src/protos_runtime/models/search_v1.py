"""Search v1 contract models.

Source: ``protos/generated/python/search_v1_models.py`` (kept in sync; see package README).

The original generator emits ``Result`` after ``SearchResponse`` which uses it,
which is fine under ``from __future__ import annotations`` but requires either
deferred resolution or model_rebuild() at module load. This file reorders so
``Result`` is defined first and SearchResponse references it directly.
"""

from __future__ import annotations

from pydantic import BaseModel


class IndexEntryCommand(BaseModel):
    """Command sent by producers to index (or re-index) a single entry."""

    id: str
    title: str
    category: str
    content: str
    metadata: dict[str, str]


class EntryIndexed(BaseModel):
    """Domain event emitted after a successful index/upsert operation."""

    id: str
    title: str
    category: str
    timestamp: float


class SearchRequest(BaseModel):
    """Read-side query payload."""

    query: str
    category_filter: str
    limit: int


class Result(BaseModel):
    """Single search hit returned in ``SearchResponse``."""

    id: str
    title: str
    category: str
    score: float


class SearchResponse(BaseModel):
    """Aggregated read-side response wrapping a list of ``Result`` items."""

    results: list[Result]
    total_count: int
