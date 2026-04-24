"""
tests/test_event_store.py – tests for the Event Store + Replay Engine.

Run with:
    python -m pytest tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from event_store import EventStore, ReplayEngine, make_user_replay_engine  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path):
    """Return a fresh EventStore backed by a temp SQLite file."""
    return EventStore(db_path=str(tmp_path / "test_events.db"))


@pytest.fixture()
def user_engine(store):
    return make_user_replay_engine(store)


# ---------------------------------------------------------------------------
# EventStore – basic append / read
# ---------------------------------------------------------------------------


class TestEventStore:
    def test_append_returns_event(self, store):
        event = store.append("user-1", "UserCreated", {"email": "a@b.com"})
        assert event.event_type == "UserCreated"
        assert event.version == 1
        assert event.aggregate_id == "user-1"

    def test_version_auto_increments(self, store):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        e2 = store.append("user-1", "EmailChanged", {"email": "b@b.com"})
        assert e2.version == 2

    def test_get_stream_returns_ordered_events(self, store):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        store.append("user-1", "EmailChanged", {"email": "b@b.com"})
        events = store.get_stream("user-1")
        assert len(events) == 2
        assert events[0].version < events[1].version

    def test_get_stream_from_version(self, store):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        store.append("user-1", "EmailChanged", {"email": "b@b.com"})
        events = store.get_stream("user-1", from_version=1)
        assert len(events) == 1
        assert events[0].event_type == "EmailChanged"

    def test_optimistic_concurrency_conflict(self, store):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        with pytest.raises(ValueError, match="concurrency conflict"):
            store.append("user-1", "EmailChanged", {"email": "x"}, expected_version=0)

    def test_optimistic_concurrency_success(self, store):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        e = store.append("user-1", "EmailChanged", {"email": "b@b.com"}, expected_version=1)
        assert e.version == 2

    def test_separate_aggregates_independent(self, store):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        store.append("user-2", "UserCreated", {"email": "c@d.com"})
        assert store.get_stream("user-1")[0].payload["email"] == "a@b.com"
        assert store.get_stream("user-2")[0].payload["email"] == "c@d.com"

    def test_iter_all_yields_all_events(self, store):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        store.append("user-2", "UserCreated", {"email": "c@d.com"})
        all_events = list(store.iter_all())
        assert len(all_events) == 2


# ---------------------------------------------------------------------------
# EventStore – snapshots
# ---------------------------------------------------------------------------


class TestSnapshots:
    def test_save_and_load_snapshot(self, store):
        store.save_snapshot("user-1", {"id": "user-1", "email": "a@b.com"}, version=5)
        snap = store.load_snapshot("user-1")
        assert snap is not None
        assert snap.state["email"] == "a@b.com"
        assert snap.version == 5

    def test_load_snapshot_none_when_missing(self, store):
        assert store.load_snapshot("no-such-user") is None

    def test_snapshot_overwrite(self, store):
        store.save_snapshot("user-1", {"email": "a@b.com"}, version=1)
        store.save_snapshot("user-1", {"email": "b@b.com"}, version=2)
        snap = store.load_snapshot("user-1")
        assert snap.state["email"] == "b@b.com"
        assert snap.version == 2


# ---------------------------------------------------------------------------
# ReplayEngine
# ---------------------------------------------------------------------------


class TestReplayEngine:
    def test_replay_creates_state(self, store, user_engine):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        state = user_engine.replay("user-1")
        assert state["email"] == "a@b.com"
        assert state["active"] is True

    def test_replay_applies_email_change(self, store, user_engine):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        store.append("user-1", "EmailChanged", {"email": "new@b.com"})
        state = user_engine.replay("user-1")
        assert state["email"] == "new@b.com"

    def test_replay_deactivate(self, store, user_engine):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        store.append("user-1", "UserDeactivated", {})
        state = user_engine.replay("user-1")
        assert state["active"] is False

    def test_replay_uses_snapshot(self, store, user_engine):
        store.append("user-1", "UserCreated", {"email": "a@b.com"})
        store.save_snapshot("user-1", {"id": "user-1", "email": "a@b.com", "active": True}, 1)
        store.append("user-1", "EmailChanged", {"email": "after@b.com"})
        state = user_engine.replay("user-1")
        assert state["email"] == "after@b.com"

    def test_replay_empty_stream(self, store):
        engine = ReplayEngine(event_store=store)
        state = engine.replay("unknown-user", initial_state={"custom": True})
        assert state["custom"] is True

    def test_register_decorator(self, store):
        engine = ReplayEngine(event_store=store)

        @engine.register("SomeEvent")
        def handler(state, event):
            return {**state, "handled": True}

        store.append("agg-1", "SomeEvent", {})
        state = engine.replay("agg-1", initial_state={})
        assert state["handled"] is True
