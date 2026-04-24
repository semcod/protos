"""
legacy_registry.py – Extended Schema Registry for legacy (JSON/Pydantic) and Proto schemas.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import os
import sys
from dataclasses import dataclass
from typing import Any

# Ensure we can import from the same directory
sys.path.insert(0, os.path.dirname(__file__))

from parse_proto import parse_proto
from legacy_bridge.normalizer import normalize_json_schema, normalize_proto_ast
from legacy_bridge.diff_engine import diff_fields
from legacy_bridge.migration_advisor import get_migration_summary

DB_PATH = "legacy_registry.db"

DDL_LEGACY_SCHEMAS = """
CREATE TABLE IF NOT EXISTS legacy_schemas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject     TEXT NOT NULL,
    format      TEXT NOT NULL,         -- "json_schema" | "pydantic" | "proto"
    version     INTEGER NOT NULL,
    sha256      TEXT NOT NULL,
    schema_json TEXT NOT NULL,
    source_file TEXT,
    timestamp   REAL NOT NULL,
    UNIQUE (subject, format, version)
);
"""

DDL_SCHEMA_DIFFS = """
CREATE TABLE IF NOT EXISTS schema_diffs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    legacy_id    INTEGER REFERENCES legacy_schemas(id),
    proto_id     INTEGER REFERENCES legacy_schemas(id),
    diff_json    TEXT NOT NULL,
    readiness    REAL NOT NULL,
    timestamp    REAL NOT NULL
);
"""


@dataclass
class LegacySchemaVersion:
    id: int
    subject: str
    format: str
    version: int
    sha256: str
    schema_dict: dict[str, Any]
    source_file: str | None
    timestamp: float


class LegacySchemaRegistry:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.execute(DDL_LEGACY_SCHEMAS)
            self.conn.execute(DDL_SCHEMA_DIFFS)

    def register(self, subject: str, schema_format: str, schema_dict: dict[str, Any], source_file: str | None = None) -> LegacySchemaVersion:
        schema_json = json.dumps(schema_dict, sort_keys=True)
        sha256 = hashlib.sha256(schema_json.encode()).hexdigest()
        
        version = self._get_next_version(subject, schema_format)
        ts = time.time()

        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO legacy_schemas (subject, format, version, sha256, schema_json, source_file, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (subject, schema_format, version, sha256, schema_json, source_file, ts),
            )
            row_id = cursor.lastrowid

        return LegacySchemaVersion(
            id=row_id,
            subject=subject,
            format=schema_format,
            version=version,
            sha256=sha256,
            schema_dict=schema_dict,
            source_file=source_file,
            timestamp=ts,
        )

    def _get_next_version(self, subject: str, schema_format: str) -> int:
        row = self.conn.execute(
            "SELECT MAX(version) as v FROM legacy_schemas WHERE subject = ? AND format = ?",
            (subject, schema_format),
        ).fetchone()
        return (row["v"] or 0) + 1

    def get_latest(self, subject: str, schema_format: str) -> LegacySchemaVersion | None:
        row = self.conn.execute(
            "SELECT * FROM legacy_schemas WHERE subject = ? AND format = ? ORDER BY version DESC LIMIT 1",
            (subject, schema_format),
        ).fetchone()
        if not row:
            return None
        return self._row_to_sv(row)

    def _row_to_sv(self, row: sqlite3.Row) -> LegacySchemaVersion:
        return LegacySchemaVersion(
            id=row["id"],
            subject=row["subject"],
            format=row["format"],
            version=row["version"],
            sha256=row["sha256"],
            schema_dict=json.loads(row["schema_json"]),
            source_file=row["source_file"],
            timestamp=row["timestamp"],
        )


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Legacy Schema Registry CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # Register JSON
    reg_json = sub.add_parser("register-json", help="Register a JSON Schema")
    reg_json.add_argument("subject", help="Schema subject name")
    reg_json.add_argument("file", help="Path to JSON Schema file")

    # Register Proto
    reg_proto = sub.add_parser("register-proto", help="Register a Proto contract")
    reg_proto.add_argument("subject", help="Schema subject name")
    reg_proto.add_argument("file", help="Path to .proto file")

    # Diff
    diff_cmd = sub.add_parser("diff", help="Perform cross-format diff")
    diff_cmd.add_argument("legacy_subject", help="Legacy subject name")
    diff_cmd.add_argument("proto_subject", help="Proto subject name")

    args = parser.parse_args()
    registry = LegacySchemaRegistry()

    if args.command == "register-json":
        with open(args.file, "r") as f:
            schema = json.load(f)
        sv = registry.register(args.subject, "json_schema", schema, args.file)
        print(f"Registered {sv.subject} (JSON) version {sv.version}")

    elif args.command == "register-proto":
        ast = parse_proto(args.file)
        sv = registry.register(args.subject, "proto", ast, args.file)
        print(f"Registered {sv.subject} (Proto) version {sv.version}")

    elif args.command == "diff":
        legacy = registry.get_latest(args.legacy_subject, "json_schema")
        proto = registry.get_latest(args.proto_subject, "proto")

        if not legacy or not proto:
            print("Error: Could not find latest version for one of the subjects.")
            sys.exit(1)

        # Normalize (assuming first message in proto for simplicity in CLI)
        legacy_fields = normalize_json_schema(legacy.schema_dict)
        proto_fields = normalize_proto_ast(proto.schema_dict["messages"][0])

        report = diff_fields(legacy_fields, proto_fields)
        print(get_migration_summary(report))


if __name__ == "__main__":
    main()
