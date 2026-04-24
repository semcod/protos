"""
schema_registry.py – SQLite-backed schema registry with compatibility enforcement.

Inspired by Confluent Schema Registry, this module provides:
  * SchemaRegistry – stores proto AST snapshots and enforces compatibility rules
  * IncompatibleSchemaError – raised when a schema change breaks compatibility
  * CompatibilityMode – BACKWARD, FORWARD, FULL_TRANSITIVE, NONE

Compatibility modes
-------------------
BACKWARD
    New schema (version N) can read data written by the previous schema (N-1).
    Violations: field removal without reservation, field type change, field
    number change for same-named field, field number reuse for a renamed field.

FORWARD
    Previous schema (N-1) can read data written by the new schema (N).
    Violations: field type change, field number change/reuse.
    (Removing a field from the new schema is NOT a FORWARD violation because
    the old reader simply receives a default value for that field.)

FULL_TRANSITIVE
    Both BACKWARD and FORWARD compatibility must hold across **every** previously
    registered version, not just the most recent one.

NONE
    No compatibility check is performed; any schema change is accepted.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from parse_proto import parse_proto  # noqa: E402


# ---------------------------------------------------------------------------
# Compatibility modes
# ---------------------------------------------------------------------------

BACKWARD = "BACKWARD"
FORWARD = "FORWARD"
FULL_TRANSITIVE = "FULL_TRANSITIVE"
NONE = "NONE"

VALID_MODES = {BACKWARD, FORWARD, FULL_TRANSITIVE, NONE}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class IncompatibleSchemaError(Exception):
    """Raised when a proposed schema change violates the active compatibility mode."""

    def __init__(self, message: str, violations: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.violations = violations


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class SchemaVersion:
    id: int
    package: str
    version: int
    sha256: str
    ast: dict[str, Any]
    proto_src: str
    timestamp: float


# ---------------------------------------------------------------------------
# DB setup
# ---------------------------------------------------------------------------

_DDL_SCHEMAS = """
CREATE TABLE IF NOT EXISTS schemas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    package     TEXT NOT NULL,
    version     INTEGER NOT NULL,
    sha256      TEXT NOT NULL,
    ast_json    TEXT NOT NULL,
    proto_src   TEXT NOT NULL,
    timestamp   REAL NOT NULL,
    UNIQUE (package, version)
);
"""

_DDL_COMPATIBILITY = """
CREATE TABLE IF NOT EXISTS compatibility (
    package     TEXT PRIMARY KEY,
    mode        TEXT NOT NULL DEFAULT 'BACKWARD'
);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(_DDL_SCHEMAS)
    conn.execute(_DDL_COMPATIBILITY)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Breaking-change detection
# ---------------------------------------------------------------------------


def _diff_messages(
    old_msgs: list[dict[str, Any]],
    new_msgs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return a list of schema-change records between two message lists.

    Each record has a ``kind`` key and contextual fields describing the change.
    Possible kinds:

    * ``message_removed``      – a whole message was deleted
    * ``field_removed``        – a field disappeared (and was not reserved)
    * ``field_type_changed``   – same name/number, different type
    * ``field_number_changed`` – same name, different field number
    * ``field_number_reused``  – a number previously belonging to field A is
                                  now assigned to field B
    """
    changes: list[dict[str, Any]] = []

    old_by_name = {m["name"]: m for m in old_msgs}
    new_by_name = {m["name"]: m for m in new_msgs}

    for msg_name, old_msg in old_by_name.items():
        new_msg = new_by_name.get(msg_name)
        if new_msg is None:
            changes.append({"kind": "message_removed", "message": msg_name})
            continue

        old_fields_by_name = {f["name"]: f for f in old_msg["fields"]}
        new_fields_by_name = {f["name"]: f for f in new_msg["fields"]}
        old_fields_by_number = {f["number"]: f for f in old_msg["fields"]}
        new_fields_by_number = {f["number"]: f for f in new_msg["fields"]}

        new_reserved_numbers: set[int] = set(new_msg.get("reserved_numbers", []))
        new_reserved_names: set[str] = set(new_msg.get("reserved_names", []))

        # --- field removals --------------------------------------------------
        for fname, old_field in old_fields_by_name.items():
            if fname not in new_fields_by_name:
                changes.append(
                    {
                        "kind": "field_removed",
                        "message": msg_name,
                        "field": fname,
                        "number": old_field["number"],
                    }
                )

        # --- type / number changes for same-named fields ---------------------
        for fname, old_field in old_fields_by_name.items():
            new_field = new_fields_by_name.get(fname)
            if new_field is None:
                continue
            if new_field["type"] != old_field["type"]:
                changes.append(
                    {
                        "kind": "field_type_changed",
                        "message": msg_name,
                        "field": fname,
                        "old_type": old_field["type"],
                        "new_type": new_field["type"],
                    }
                )
            if new_field["number"] != old_field["number"]:
                changes.append(
                    {
                        "kind": "field_number_changed",
                        "message": msg_name,
                        "field": fname,
                        "old_number": old_field["number"],
                        "new_number": new_field["number"],
                    }
                )

        # --- field number reuse ----------------------------------------------
        for number, new_field in new_fields_by_number.items():
            if number in new_reserved_numbers:
                # Using a number that the schema itself marks reserved is already
                # a proto error; skip here to avoid duplicate noise.
                continue
            old_field = old_fields_by_number.get(number)
            if old_field is not None and old_field["name"] != new_field["name"]:
                changes.append(
                    {
                        "kind": "field_number_reused",
                        "message": msg_name,
                        "number": number,
                        "old_field": old_field["name"],
                        "new_field": new_field["name"],
                    }
                )

    return changes


# Kinds that are always breaking for BACKWARD compatibility.
_BACKWARD_VIOLATION_KINDS = {
    "message_removed",
    "field_removed",
    "field_type_changed",
    "field_number_changed",
    "field_number_reused",
}

# Kinds that are breaking for FORWARD compatibility.
# (field_removed is *not* a FORWARD violation – the old reader just sees the
# default value for that field when reading new-schema data.)
_FORWARD_VIOLATION_KINDS = {
    "message_removed",
    "field_type_changed",
    "field_number_changed",
    "field_number_reused",
}


def check_compatibility(
    new_ast: dict[str, Any],
    old_ast: dict[str, Any],
    mode: str,
) -> list[dict[str, Any]]:
    """Return a list of compatibility violations (empty = compatible).

    Parameters
    ----------
    new_ast:
        Parsed AST of the proposed new schema.
    old_ast:
        Parsed AST of the existing (baseline) schema.
    mode:
        One of ``BACKWARD``, ``FORWARD``, ``FULL_TRANSITIVE``, ``NONE``.
    """
    if mode == NONE:
        return []

    if mode not in VALID_MODES:
        raise ValueError(f"Unknown compatibility mode: {mode!r}. Valid: {VALID_MODES}")

    all_changes = _diff_messages(old_ast["messages"], new_ast["messages"])

    if mode in (BACKWARD, FULL_TRANSITIVE):
        violation_kinds = _BACKWARD_VIOLATION_KINDS
    else:  # FORWARD
        violation_kinds = _FORWARD_VIOLATION_KINDS

    return [c for c in all_changes if c["kind"] in violation_kinds]


# ---------------------------------------------------------------------------
# Schema hash
# ---------------------------------------------------------------------------


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# SchemaRegistry
# ---------------------------------------------------------------------------


class SchemaRegistry:
    """SQLite-backed proto schema registry with compatibility enforcement."""

    def __init__(self, db_path: str = "schema_registry.db") -> None:
        self._conn = _connect(db_path)

    # ------------------------------------------------------------------
    # Compatibility mode management
    # ------------------------------------------------------------------

    def set_compatibility(self, package: str, mode: str) -> None:
        """Set the compatibility mode for *package*."""
        if mode not in VALID_MODES:
            raise ValueError(f"Unknown mode {mode!r}. Valid: {VALID_MODES}")
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO compatibility (package, mode)
                VALUES (?, ?)
                ON CONFLICT(package) DO UPDATE SET mode = excluded.mode
                """,
                (package, mode),
            )

    def get_compatibility(self, package: str) -> str:
        """Return the current compatibility mode for *package* (default BACKWARD)."""
        row = self._conn.execute(
            "SELECT mode FROM compatibility WHERE package = ?", (package,)
        ).fetchone()
        return row["mode"] if row else BACKWARD

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        proto_path: str,
        mode: str | None = None,
    ) -> SchemaVersion:
        """Register a new schema version for the package declared in *proto_path*.

        Parameters
        ----------
        proto_path:
            Path to the ``.proto`` file to register.
        mode:
            Compatibility mode to use for this check.  If ``None``, the mode
            stored for the package is used (defaulting to ``BACKWARD``).

        Returns
        -------
        SchemaVersion
            The newly created registry entry.

        Raises
        ------
        IncompatibleSchemaError
            When the new schema violates the active compatibility mode relative
            to existing registered versions.
        """
        ast = parse_proto(proto_path)
        package = ast["package"]

        with open(proto_path, "r", encoding="utf-8") as fh:
            proto_src = fh.read()

        sha = _sha256_file(proto_path)
        effective_mode = mode if mode is not None else self.get_compatibility(package)

        # --- compatibility check -----------------------------------------
        if effective_mode == FULL_TRANSITIVE:
            all_versions = self._all_versions(package)
            for old_sv in all_versions:
                violations = check_compatibility(ast, old_sv.ast, BACKWARD)
                if violations:
                    raise IncompatibleSchemaError(
                        f"Schema for {package!r} is not FULL_TRANSITIVE compatible "
                        f"with version {old_sv.version}: "
                        + "; ".join(v["kind"] for v in violations),
                        violations,
                    )
        elif effective_mode != NONE:
            latest = self.get_latest(package)
            if latest is not None:
                violations = check_compatibility(ast, latest.ast, effective_mode)
                if violations:
                    raise IncompatibleSchemaError(
                        f"Schema for {package!r} is not {effective_mode} compatible "
                        f"with version {latest.version}: "
                        + "; ".join(v["kind"] for v in violations),
                        violations,
                    )

        # --- persist ---------------------------------------------------------
        new_version = self._next_version(package)
        ts = time.time()

        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO schemas (package, version, sha256, ast_json, proto_src, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (package, new_version, sha, json.dumps(ast), proto_src, ts),
            )
            row_id = cursor.lastrowid

        return SchemaVersion(
            id=row_id,
            package=package,
            version=new_version,
            sha256=sha,
            ast=ast,
            proto_src=proto_src,
            timestamp=ts,
        )

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def get_latest(self, package: str) -> SchemaVersion | None:
        """Return the most recently registered schema for *package*, or None."""
        row = self._conn.execute(
            "SELECT * FROM schemas WHERE package = ? ORDER BY version DESC LIMIT 1",
            (package,),
        ).fetchone()
        return self._row_to_sv(row) if row else None

    def get_by_version(self, package: str, version: int) -> SchemaVersion | None:
        """Return a specific version of the schema for *package*, or None."""
        row = self._conn.execute(
            "SELECT * FROM schemas WHERE package = ? AND version = ?",
            (package, version),
        ).fetchone()
        return self._row_to_sv(row) if row else None

    def list_schemas(self) -> list[dict[str, Any]]:
        """Return summary rows for every registered schema (all packages)."""
        rows = self._conn.execute(
            "SELECT package, version, sha256, timestamp FROM schemas ORDER BY package, version"
        ).fetchall()
        return [
            {
                "package": r["package"],
                "version": r["version"],
                "sha256": r["sha256"],
                "timestamp": r["timestamp"],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_version(self, package: str) -> int:
        row = self._conn.execute(
            "SELECT MAX(version) AS v FROM schemas WHERE package = ?", (package,)
        ).fetchone()
        return (row["v"] or 0) + 1

    def _all_versions(self, package: str) -> list[SchemaVersion]:
        rows = self._conn.execute(
            "SELECT * FROM schemas WHERE package = ? ORDER BY version ASC",
            (package,),
        ).fetchall()
        return [self._row_to_sv(r) for r in rows]

    @staticmethod
    def _row_to_sv(row: sqlite3.Row) -> SchemaVersion:
        return SchemaVersion(
            id=row["id"],
            package=row["package"],
            version=row["version"],
            sha256=row["sha256"],
            ast=json.loads(row["ast_json"]),
            proto_src=row["proto_src"],
            timestamp=row["timestamp"],
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli() -> None:  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Proto Schema Registry CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    reg_p = sub.add_parser("register", help="Register a .proto file")
    reg_p.add_argument("proto", help="Path to .proto file")
    reg_p.add_argument("--mode", default=None, help="Compatibility mode override")
    reg_p.add_argument("--db", default="schema_registry.db")

    chk_p = sub.add_parser("check", help="Check compatibility without registering")
    chk_p.add_argument("proto", help="Path to .proto file")
    chk_p.add_argument("--mode", default=BACKWARD)
    chk_p.add_argument("--db", default="schema_registry.db")

    lst_p = sub.add_parser("list", help="List registered schemas")
    lst_p.add_argument("--db", default="schema_registry.db")

    args = parser.parse_args()
    registry = SchemaRegistry(db_path=args.db)

    if args.command == "register":
        try:
            sv = registry.register(args.proto, mode=args.mode)
            print(f"Registered {sv.package} version {sv.version} (sha256={sv.sha256[:12]}…)")
        except IncompatibleSchemaError as exc:
            print(f"ERROR: {exc}")
            print("Violations:")
            for v in exc.violations:
                print(f"  - {v}")
            raise SystemExit(1) from exc

    elif args.command == "check":
        ast = parse_proto(args.proto)
        package = ast["package"]
        latest = registry.get_latest(package)
        if latest is None:
            print(f"No existing schema for {package!r}; nothing to check against.")
            return
        violations = check_compatibility(ast, latest.ast, args.mode)
        if violations:
            print(f"INCOMPATIBLE ({args.mode}):")
            for v in violations:
                print(f"  - {v}")
            raise SystemExit(1)
        print(f"Compatible with {package} version {latest.version} ({args.mode})")

    elif args.command == "list":
        rows = registry.list_schemas()
        if not rows:
            print("No schemas registered.")
            return
        print(f"{'PACKAGE':<30} {'VER':>5}  {'SHA256':>14}  TIMESTAMP")
        for r in rows:
            print(
                f"{r['package']:<30} {r['version']:>5}  "
                f"{r['sha256'][:12]}…  {r['timestamp']:.0f}"
            )


if __name__ == "__main__":
    _cli()
