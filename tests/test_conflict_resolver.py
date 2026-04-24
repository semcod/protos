"""
tests/test_conflict_resolver.py – tests for the conflict resolution model.

Run with:
    python -m pytest tests/ -v
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from event_store import EventStore, StoredEvent  # noqa: E402
from conflict_resolver import (
    ConflictResolver,
    UnresolvableConflictError,
    _EXCLUSIVE_PAIRS,
)  # noqa: E402
from vector_clock import VectorClock  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers to build synthetic StoredEvent objects without a real DB
# ---------------------------------------------------------------------------


def _event(
    event_type: str,
    payload: dict[str, Any],
    timestamp: float,
    aggregate_id: str = "agg-1",
    version: int = 1,
) -> StoredEvent:
    import uuid

    return StoredEvent(
        id=str(uuid.uuid4()),
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
        version=version,
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path):
    return EventStore(db_path=str(tmp_path / "test_cr.db"))


@pytest.fixture()
def resolver():
    return ConflictResolver()


# ===========================================================================
# VectorClock tests
# ===========================================================================


class TestVectorClock:
    def test_increment_creates_new_instance(self):
        vc = VectorClock()
        vc2 = vc.increment("A")
        assert vc.clocks == {}
        assert vc2.clocks == {"A": 1}

    def test_increment_increases_counter(self):
        vc = VectorClock({"A": 1}).increment("A")
        assert vc.clocks["A"] == 2

    def test_merge_takes_element_wise_max(self):
        vc_a = VectorClock({"A": 3, "B": 1})
        vc_b = VectorClock({"A": 1, "B": 4})
        merged = vc_a.merge(vc_b)
        assert merged.clocks == {"A": 3, "B": 4}

    def test_merge_includes_missing_keys(self):
        vc_a = VectorClock({"A": 2})
        vc_b = VectorClock({"B": 1})
        merged = vc_a.merge(vc_b)
        assert merged.clocks == {"A": 2, "B": 1}

    def test_happened_before_simple(self):
        vc1 = VectorClock({"A": 1})
        vc2 = VectorClock({"A": 2})
        assert vc1.happened_before(vc2)
        assert not vc2.happened_before(vc1)

    def test_concurrent_when_neither_dominates(self):
        vc_a = VectorClock({"A": 1, "B": 0})
        vc_b = VectorClock({"A": 0, "B": 1})
        assert vc_a.concurrent_with(vc_b)
        assert vc_b.concurrent_with(vc_a)

    def test_not_concurrent_when_one_dominates(self):
        vc1 = VectorClock({"A": 1})
        vc2 = VectorClock({"A": 2})
        assert not vc1.concurrent_with(vc2)

    def test_equal_clocks_not_happened_before(self):
        vc = VectorClock({"A": 1})
        assert not vc.happened_before(vc)

    def test_dominates_is_reverse_happened_before(self):
        vc1 = VectorClock({"A": 1})
        vc2 = VectorClock({"A": 2})
        assert vc2.dominates(vc1)
        assert not vc1.dominates(vc2)

    def test_to_dict_and_from_dict_round_trip(self):
        vc = VectorClock({"A": 3, "B": 7})
        assert VectorClock.from_dict(vc.to_dict()) == vc

    def test_equality(self):
        assert VectorClock({"A": 1}) == VectorClock({"A": 1})
        assert VectorClock({"A": 1}) != VectorClock({"A": 2})

    def test_missing_key_treated_as_zero(self):
        vc1 = VectorClock({"A": 1})
        vc2 = VectorClock({"A": 1, "B": 0})
        assert vc1 == vc2


# ===========================================================================
# LWW strategy
# ===========================================================================


class TestLWWStrategy:
    def test_lww_concurrent_email_updates_picks_latest(self, resolver):
        """Two concurrent EmailChanged events – LWW orders by timestamp."""
        e_server = _event("EmailChanged", {"email": "server@x.com"}, timestamp=2.0, version=2)
        e_branch = _event("EmailChanged", {"email": "branch@x.com"}, timestamp=1.0, version=2)
        merged = resolver.resolve_lww([e_server], [e_branch])
        assert len(merged) == 2
        # Both events are preserved; the last one (by timestamp) wins on replay
        assert merged[0].payload["email"] == "branch@x.com"
        assert merged[1].payload["email"] == "server@x.com"

    def test_lww_returns_all_events_sorted_by_timestamp(self, resolver):
        t = time.time()
        e1 = _event("UserCreated", {"email": "a@x.com"}, timestamp=t, version=1)
        e2 = _event("EmailChanged", {"email": "b@x.com"}, timestamp=t + 1, version=2)
        e3 = _event("UserDeactivated", {}, timestamp=t + 2, version=3)
        # Mix order between server and branch
        merged = resolver.resolve_lww([e1, e3], [e2])
        assert [e.timestamp for e in merged] == sorted(e.timestamp for e in [e1, e2, e3])

    def test_lww_server_preferred_on_timestamp_tie(self, resolver):
        """When timestamps are equal the server event should come first (stable sort)."""
        ts = 100.0
        e_server = _event("EmailChanged", {"email": "server@x.com"}, timestamp=ts, version=2)
        e_branch = _event("EmailChanged", {"email": "branch@x.com"}, timestamp=ts, version=2)
        merged = resolver.resolve_lww([e_server], [e_branch])
        assert merged[0].payload["email"] == "server@x.com"

    def test_lww_empty_branch_returns_server_stream(self, resolver):
        t = time.time()
        e1 = _event("UserCreated", {"email": "a@x.com"}, timestamp=t, version=1)
        assert resolver.resolve_lww([e1], []) == [e1]

    def test_lww_empty_server_returns_branch_stream(self, resolver):
        t = time.time()
        e1 = _event("EmailChanged", {"email": "x@x.com"}, timestamp=t, version=2)
        assert resolver.resolve_lww([], [e1]) == [e1]


# ===========================================================================
# MERGE strategy – non-conflicting events
# ===========================================================================


class TestMergeNonConflicting:
    def test_concurrent_deactivation_and_email_change_both_apply(self, resolver):
        """Deactivation and email change touch different fields → both accepted."""
        t = time.time()
        e_server = _event("UserDeactivated", {}, timestamp=t + 1, version=2)
        e_branch = _event("EmailChanged", {"email": "new@x.com"}, timestamp=t, version=2)
        merged = resolver.resolve_merge([e_server], [e_branch])
        event_types = {e.event_type for e in merged}
        assert "UserDeactivated" in event_types
        assert "EmailChanged" in event_types

    def test_merge_returns_chronological_order(self, resolver):
        t = time.time()
        e_server = _event("UserDeactivated", {}, timestamp=t + 2, version=2)
        e_branch = _event("EmailChanged", {"email": "new@x.com"}, timestamp=t + 1, version=2)
        merged = resolver.resolve_merge([e_server], [e_branch])
        assert merged[0].event_type == "EmailChanged"
        assert merged[1].event_type == "UserDeactivated"

    def test_empty_branch_returns_server_stream(self, resolver):
        t = time.time()
        e = _event("UserCreated", {"email": "a@x.com"}, timestamp=t, version=1)
        assert resolver.resolve_merge([e], []) == [e]


# ===========================================================================
# MERGE strategy – true conflicts
# ===========================================================================


class TestMergeConflicts:
    def test_concurrent_email_updates_raises(self, resolver):
        """Two concurrent EmailChanged events with different emails → conflict."""
        t = time.time()
        e_server = _event("EmailChanged", {"email": "server@x.com"}, timestamp=t + 1, version=2)
        e_branch = _event("EmailChanged", {"email": "branch@x.com"}, timestamp=t, version=2)
        with pytest.raises(UnresolvableConflictError) as exc_info:
            resolver.resolve_merge([e_server], [e_branch])
        assert exc_info.value.conflicts
        assert any(c["kind"] == "field_value_conflict" for c in exc_info.value.conflicts)
        assert any(c.get("field") == "email" for c in exc_info.value.conflicts)

    def test_mutually_exclusive_events_raise(self, resolver):
        """UserDeactivated on server + UserActivated on branch → unresolvable."""
        t = time.time()
        e_server = _event("UserDeactivated", {}, timestamp=t + 1, version=2)
        e_branch = _event("UserActivated", {}, timestamp=t, version=2)
        with pytest.raises(UnresolvableConflictError) as exc_info:
            resolver.resolve_merge([e_server], [e_branch])
        assert exc_info.value.conflicts
        assert any(c["kind"] == "exclusive_event_pair" for c in exc_info.value.conflicts)

    def test_deactivated_plus_reactivated_raises(self, resolver):
        """UserDeactivated + UserReactivated is also an exclusive pair."""
        t = time.time()
        e_s = _event("UserDeactivated", {}, timestamp=t + 1, version=2)
        e_b = _event("UserReactivated", {}, timestamp=t, version=2)
        with pytest.raises(UnresolvableConflictError):
            resolver.resolve_merge([e_s], [e_b])

    def test_conflict_error_carries_structured_data(self, resolver):
        t = time.time()
        e_s = _event("EmailChanged", {"email": "s@x.com"}, timestamp=t + 1)
        e_b = _event("EmailChanged", {"email": "b@x.com"}, timestamp=t)
        try:
            resolver.resolve_merge([e_s], [e_b])
            pytest.fail("Expected UnresolvableConflictError")
        except UnresolvableConflictError as exc:
            conflict = exc.conflicts[0]
            assert "field" in conflict
            assert "server_value" in conflict
            assert "branch_value" in conflict


# ===========================================================================
# EventStore.merge_streams integration
# ===========================================================================


class TestEventStoreMergeStreams:
    def test_lww_merge_via_event_store(self, store):
        t = time.time()
        store.append("user-1", "UserCreated", {"email": "a@x.com"})  # version 1

        # Simulate branch events (offline client saw version 1 before disconnecting)
        branch = [
            _event("EmailChanged", {"email": "branch@x.com"}, timestamp=t, aggregate_id="user-1", version=2),
        ]
        # Server appended another email change while branch was offline
        store.append("user-1", "EmailChanged", {"email": "server@x.com"})  # version 2

        merged = store.merge_streams("user-1", branch, strategy="LWW", fork_version=1)
        assert len(merged) == 2  # one server event + one branch event
        # Last by timestamp wins
        last = max(merged, key=lambda e: e.timestamp)
        # Either branch or server wins depending on timestamps; just ensure both present
        event_emails = {e.payload["email"] for e in merged}
        assert "server@x.com" in event_emails
        assert "branch@x.com" in event_emails

    def test_merge_strategy_deactivation_plus_email(self, store):
        t = time.time()
        store.append("user-1", "UserCreated", {"email": "a@x.com"})  # version 1

        branch = [
            _event("EmailChanged", {"email": "new@x.com"}, timestamp=t, aggregate_id="user-1", version=2),
        ]
        # Server deactivated while branch was offline
        store.append("user-1", "UserDeactivated", {})  # version 2

        merged = store.merge_streams("user-1", branch, strategy="MERGE", fork_version=1)
        types = {e.event_type for e in merged}
        assert "UserDeactivated" in types
        assert "EmailChanged" in types

    def test_unknown_strategy_raises(self, store):
        with pytest.raises(ValueError, match="Unknown merge strategy"):
            store.merge_streams("user-1", [], strategy="INVALID")

    def test_offline_gap_detection(self, store):
        """Branch that forked at version 0 gets all server events as concurrent."""
        store.append("user-1", "UserCreated", {"email": "a@x.com"})  # version 1
        store.append("user-1", "EmailChanged", {"email": "b@x.com"})  # version 2

        t = time.time()
        branch = [
            _event("UserDeactivated", {}, timestamp=t, aggregate_id="user-1", version=1),
        ]
        # fork_version=0 → ALL server events are returned as concurrent
        merged = store.merge_streams("user-1", branch, strategy="LWW", fork_version=0)
        # server gave 2 events + 1 branch event = 3 total
        assert len(merged) == 3

    def test_merge_with_no_server_events_after_fork(self, store):
        """No server events after fork → branch events are just returned."""
        store.append("user-1", "UserCreated", {"email": "a@x.com"})  # version 1

        t = time.time()
        branch = [
            _event("EmailChanged", {"email": "b@x.com"}, timestamp=t, aggregate_id="user-1", version=2),
        ]
        # fork_version=1 → no server events after version 1
        merged = store.merge_streams("user-1", branch, strategy="MERGE", fork_version=1)
        assert len(merged) == 1
        assert merged[0].payload["email"] == "b@x.com"


class TestConflictResolverHelpers:
    def test_check_exclusive_event_pairs_detects_conflicts(self, resolver):
        """Test _check_exclusive_event_pairs helper."""
        e_server = _event("UserDeactivated", {}, timestamp=1.0)
        e_branch = _event("UserActivated", {}, timestamp=2.0)
        
        conflicts = resolver._check_exclusive_event_pairs([e_server], [e_branch])
        assert len(conflicts) == 1
        assert conflicts[0]["kind"] == "exclusive_event_pair"
        assert "UserDeactivated" in conflicts[0]["types"]
        assert "UserActivated" in conflicts[0]["types"]
    
    def test_check_exclusive_event_pairs_no_conflict(self, resolver):
        """Test _check_exclusive_event_pairs with no conflicts."""
        e_server = _event("EmailChanged", {"email": "a@x.com"}, timestamp=1.0)
        e_branch = _event("UserCreated", {"email": "b@x.com"}, timestamp=2.0)
        
        conflicts = resolver._check_exclusive_event_pairs([e_server], [e_branch])
        assert len(conflicts) == 0
    
    def test_check_field_conflicts_detects_value_conflicts(self, resolver):
        """Test _check_field_conflicts helper."""
        e_server = _event("EmailChanged", {"email": "server@x.com"}, timestamp=1.0)
        e_branch = _event("EmailChanged", {"email": "branch@x.com"}, timestamp=2.0)
        
        conflicts = resolver._check_field_conflicts([e_server], [e_branch])
        assert len(conflicts) == 1
        assert conflicts[0]["kind"] == "field_value_conflict"
        assert conflicts[0]["field"] == "email"
    
    def test_check_field_conflicts_no_conflict_different_fields(self, resolver):
        """Test _check_field_conflicts with different fields (no conflict)."""
        e_server = _event("UserCreated", {"first_name": "John"}, timestamp=1.0)
        e_branch = _event("EmailChanged", {"email": "b@x.com"}, timestamp=2.0)
        
        conflicts = resolver._check_field_conflicts([e_server], [e_branch])
        assert len(conflicts) == 0
