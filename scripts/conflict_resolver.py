"""
conflict_resolver.py – multi-client write conflict resolution for the event store.

Two strategies are provided:

Last-Write-Wins (LWW)
    Concurrent events are merged into a single stream ordered by timestamp.
    When two events touch the same logical field, the one with the later
    timestamp silently wins.  This is the simplest strategy and is always
    safe – it never raises an error.

Field-level Merge (MERGE)
    Concurrent events are inspected field-by-field.  Events that modify
    *different* fields are both accepted; if two concurrent events modify the
    *same* field with *different* values, an ``UnresolvableConflictError`` is
    raised.  Events of mutually-exclusive types (e.g. ``UserDeactivated`` vs
    ``UserActivated``) are also treated as conflicts.

Usage
-----
From ``EventStore`` (higher-level API):

    merged = store.merge_streams(
        aggregate_id="user-1",
        branch_events=offline_events,
        strategy="LWW",          # or "MERGE"
        fork_version=3,
    )

Or call ``ConflictResolver`` directly:

    resolver = ConflictResolver()
    merged = resolver.resolve_lww(server_events, branch_events)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class UnresolvableConflictError(Exception):
    """Raised when two concurrent events cannot be automatically merged."""

    def __init__(self, message: str, conflicts: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.conflicts = conflicts


# ---------------------------------------------------------------------------
# Field-effect mapping
# ---------------------------------------------------------------------------

# Maps event_type → set of logical state fields that the event modifies.
# This is the domain-awareness layer; extend as new event types are added.
_DEFAULT_FIELD_EFFECTS: dict[str, set[str]] = {
    "UserCreated": {"email", "active", "first_name", "last_name"},
    "EmailChanged": {"email"},
    "UserDeactivated": {"active"},
    "UserActivated": {"active"},
    "UserReactivated": {"active"},
}

# Pairs of event types that set the same state field to *mutually exclusive*
# values (e.g. active=False vs active=True).  Expressed as frozensets so
# order does not matter.
_EXCLUSIVE_PAIRS: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"UserDeactivated", "UserActivated"}),
        frozenset({"UserDeactivated", "UserReactivated"}),
    }
)


def _field_effects(
    event_type: str,
    payload: dict[str, Any],
    effect_map: dict[str, set[str]],
) -> set[str]:
    """Return the set of logical fields affected by an event.

    Falls back to using the payload keys when the event type is not in the
    effect map (generic / unknown events).
    """
    if event_type in effect_map:
        return set(effect_map[event_type])
    return set(payload.keys())


# ---------------------------------------------------------------------------
# ConflictResolver
# ---------------------------------------------------------------------------


@dataclass
class ConflictResolver:
    """Resolves conflicts between concurrent event streams.

    Parameters
    ----------
    field_effect_map:
        Mapping of ``event_type`` → set of logical field names the event
        modifies.  Defaults to :data:`_DEFAULT_FIELD_EFFECTS`.
    exclusive_pairs:
        Set of ``frozenset`` pairs of mutually-exclusive event types.
        Defaults to :data:`_EXCLUSIVE_PAIRS`.
    """

    field_effect_map: dict[str, set[str]] | None = None
    exclusive_pairs: frozenset[frozenset[str]] | None = None

    def __post_init__(self) -> None:
        if self.field_effect_map is None:
            self.field_effect_map = _DEFAULT_FIELD_EFFECTS
        if self.exclusive_pairs is None:
            self.exclusive_pairs = _EXCLUSIVE_PAIRS

    # ------------------------------------------------------------------
    # LWW strategy
    # ------------------------------------------------------------------

    def resolve_lww(
        self,
        server_events: list[Any],
        branch_events: list[Any],
    ) -> list[Any]:
        """Last-Write-Wins: merge by sorting all events by timestamp.

        Returns a list of events (``StoredEvent``-like objects with a
        ``timestamp`` attribute) ordered by timestamp ascending.  When two
        events have equal timestamps the server event is preferred (stable
        sort preserves relative order within each source).
        """
        # Stable sort: server events come first in the combined list so that
        # ties resolve in favour of the server.
        combined = list(server_events) + list(branch_events)
        return sorted(combined, key=lambda e: e.timestamp)

    # ------------------------------------------------------------------
    # MERGE strategy
    # ------------------------------------------------------------------

    def resolve_merge(
        self,
        server_events: list[Any],
        branch_events: list[Any],
    ) -> list[Any]:
        """Field-level merge of concurrent event streams.

        Rules
        -----
        1. Mutually-exclusive event type pairs (e.g. UserDeactivated +
           UserActivated) → ``UnresolvableConflictError``.
        2. Two events that affect the same logical field with different payload
           values → ``UnresolvableConflictError``.
        3. Events that affect non-overlapping fields → both accepted.

        Returns a chronologically ordered merged list when no conflicts exist.

        Raises
        ------
        UnresolvableConflictError
            On the first detected unresolvable conflict.
        """
        assert self.field_effect_map is not None  # set in __post_init__
        assert self.exclusive_pairs is not None

        conflicts: list[dict[str, Any]] = []

        # --- check mutually-exclusive event type pairs -------------------
        server_types = {e.event_type for e in server_events}
        branch_types = {e.event_type for e in branch_events}

        for pair in self.exclusive_pairs:
            if pair <= (server_types | branch_types):
                pair_list = list(pair)
                if any(t in server_types for t in pair_list) and any(
                    t in branch_types for t in pair_list
                ):
                    conflicts.append(
                        {
                            "kind": "exclusive_event_pair",
                            "types": pair_list,
                        }
                    )

        if conflicts:
            raise UnresolvableConflictError(
                "Mutually exclusive events cannot be merged: "
                + ", ".join(str(c["types"]) for c in conflicts),
                conflicts,
            )

        # --- check field-level conflicts ---------------------------------
        # For each pair of (server_event, branch_event), check if they write
        # the same field with different values.
        for s_evt in server_events:
            s_effects = _field_effects(s_evt.event_type, s_evt.payload, self.field_effect_map)
            for b_evt in branch_events:
                b_effects = _field_effects(b_evt.event_type, b_evt.payload, self.field_effect_map)
                shared_fields = s_effects & b_effects
                for fld in shared_fields:
                    s_val = s_evt.payload.get(fld)
                    b_val = b_evt.payload.get(fld)
                    if s_val is not None and b_val is not None and s_val != b_val:
                        conflicts.append(
                            {
                                "kind": "field_value_conflict",
                                "field": fld,
                                "server_event": s_evt.event_type,
                                "branch_event": b_evt.event_type,
                                "server_value": s_val,
                                "branch_value": b_val,
                            }
                        )

        if conflicts:
            raise UnresolvableConflictError(
                "Concurrent events write conflicting values to the same fields: "
                + ", ".join(c["field"] for c in conflicts),
                conflicts,
            )

        # --- no conflicts: merge both streams chronologically ------------
        combined = list(server_events) + list(branch_events)
        return sorted(combined, key=lambda e: e.timestamp)
