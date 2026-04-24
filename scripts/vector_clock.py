"""
vector_clock.py – lightweight vector clock for detecting causally concurrent writes.

A vector clock assigns a logical timestamp to each event in a distributed system.
By comparing vector clocks you can determine whether two events are causally
ordered (one *happened-before* the other) or *concurrent* (neither influenced
the other).

Usage example
-------------
>>> from vector_clock import VectorClock
>>> vc_a = VectorClock().increment("nodeA")      # nodeA sends first event
>>> vc_b = VectorClock().increment("nodeB")      # nodeB independently sends event
>>> vc_a.concurrent_with(vc_b)
True
>>> vc_a.happened_before(vc_b)
False
>>> merged = vc_a.merge(vc_b)
>>> merged.clocks
{'nodeA': 1, 'nodeB': 1}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorClock:
    """Immutable vector clock.

    Attributes
    ----------
    clocks:
        Mapping of node/client identifier → logical counter.
    """

    clocks: dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mutation (returns a *new* VectorClock – immutable style)
    # ------------------------------------------------------------------

    def increment(self, node_id: str) -> "VectorClock":
        """Return a new clock with *node_id*'s counter incremented by one."""
        new_clocks = dict(self.clocks)
        new_clocks[node_id] = new_clocks.get(node_id, 0) + 1
        return VectorClock(new_clocks)

    def merge(self, other: "VectorClock") -> "VectorClock":
        """Return the element-wise maximum of *self* and *other*."""
        all_keys = set(self.clocks) | set(other.clocks)
        return VectorClock(
            {k: max(self.clocks.get(k, 0), other.clocks.get(k, 0)) for k in all_keys}
        )

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def happened_before(self, other: "VectorClock") -> bool:
        """Return ``True`` if *self* causally happened before *other*.

        *self* happened-before *other* iff every entry in *self* is ≤ the
        corresponding entry in *other*, and at least one entry is strictly <.
        """
        all_keys = set(self.clocks) | set(other.clocks)
        less_or_equal = all(
            self.clocks.get(k, 0) <= other.clocks.get(k, 0) for k in all_keys
        )
        strictly_less = any(
            self.clocks.get(k, 0) < other.clocks.get(k, 0) for k in all_keys
        )
        return less_or_equal and strictly_less

    def concurrent_with(self, other: "VectorClock") -> bool:
        """Return ``True`` if *self* and *other* are causally concurrent.

        Two clocks are concurrent when neither happened-before the other.
        """
        return not self.happened_before(other) and not other.happened_before(self)

    def dominates(self, other: "VectorClock") -> bool:
        """Return ``True`` if *self* happened-after *other* (alias for readability)."""
        return other.happened_before(self)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, int]:
        """Return a plain dict copy of the internal clocks mapping."""
        return dict(self.clocks)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "VectorClock":
        """Reconstruct a ``VectorClock`` from a plain dict."""
        return cls({str(k): int(v) for k, v in d.items()})

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VectorClock):
            return NotImplemented
        all_keys = set(self.clocks) | set(other.clocks)
        return all(self.clocks.get(k, 0) == other.clocks.get(k, 0) for k in all_keys)

    def __repr__(self) -> str:
        return f"VectorClock({self.clocks!r})"
