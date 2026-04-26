"""Smoke tests for protos_runtime.search_index."""

from __future__ import annotations

import os
import tempfile

import pytest

from protos_runtime.search_index import SearchIndex
from protos_runtime.models.search_v1 import IndexEntryCommand, SearchResponse, Result


@pytest.fixture()
def index() -> SearchIndex:
    fd, path = tempfile.mkstemp(suffix=".db", prefix="protos_runtime_test_")
    os.close(fd)
    idx = SearchIndex(db_path=path)
    yield idx
    idx.close()
    os.unlink(path)


def test_upsert_and_search(index: SearchIndex) -> None:
    index.upsert_entry(
        id="abc-1",
        title="Hello world",
        category="docs",
        content="This is a test entry",
        metadata={"source": "unit-test"},
    )
    results = index.search("Hello")
    assert len(results) == 1
    assert results[0]["id"] == "abc-1"
    assert results[0]["category"] == "docs"


def test_upsert_replaces_by_id(index: SearchIndex) -> None:
    index.upsert_entry(id="x", title="First", category="a", content="one")
    index.upsert_entry(id="x", title="Second", category="a", content="two")
    rows = index.search("Second")
    assert len(rows) == 1
    rows = index.search("First")
    assert len(rows) == 0


def test_count_and_filter(index: SearchIndex) -> None:
    index.upsert_entry(id="1", title="a", category="x", content="alpha")
    index.upsert_entry(id="2", title="b", category="y", content="beta")
    assert index.count() == 2
    assert index.count(category="x") == 1


def test_delete(index: SearchIndex) -> None:
    index.upsert_entry(id="d1", title="t", category="c", content="z")
    assert index.count() == 1
    index.delete_entry("d1")
    assert index.count() == 0


def test_pydantic_contracts_roundtrip() -> None:
    cmd = IndexEntryCommand(
        id="x",
        title="t",
        category="c",
        content="contents",
        metadata={"k": "v"},
    )
    payload = cmd.model_dump()
    assert payload["metadata"] == {"k": "v"}

    resp = SearchResponse(
        results=[Result(id="x", title="t", category="c", score=0.5)],
        total_count=1,
    )
    assert resp.results[0].id == "x"
