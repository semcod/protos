"""
generate_sql.py – generate SQL DDL (CREATE TABLE statements) from a proto AST.

Only messages whose name appears in the ENTITY_MESSAGES set are mapped to
SQL tables.  The rest are considered command/query objects and are skipped.

Usage:
    python scripts/generate_sql.py [proto_file] [output_file]

Defaults:
    proto_file  = contracts/user/v1/user.proto
    output_file = generated/sql/user.sql
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from parse_proto import parse_proto  # noqa: E402


# Only these messages are treated as persisted entities (tables).
ENTITY_MESSAGES: set[str] = {"User"}

_SQL_TYPE_MAP: dict[str, str] = {
    "string": "TEXT",
    "bool": "BOOLEAN",
    "int32": "INTEGER",
    "int64": "BIGINT",
    "uint32": "INTEGER",
    "uint64": "BIGINT",
    "float": "REAL",
    "double": "DOUBLE PRECISION",
    "bytes": "BYTEA",
}

# Fields that should be declared as PRIMARY KEY.
_PRIMARY_KEY_FIELDS: set[str] = {"id"}


def _table_name(message_name: str) -> str:
    """Convert CamelCase message name to snake_case plural table name."""
    import re

    s = re.sub(r"(?<!^)(?=[A-Z])", "_", message_name).lower()
    return s + "s"


def generate_sql(ast: dict) -> str:
    """Convert a proto AST to SQL DDL statements."""
    statements: list[str] = []

    for msg in ast["messages"]:
        if msg["name"] not in ENTITY_MESSAGES:
            continue

        table = _table_name(msg["name"])
        col_lines: list[str] = []

        for field in msg["fields"]:
            sql_type = _SQL_TYPE_MAP.get(field["type"], "TEXT")
            if field["repeated"]:
                # Store repeated scalars as a JSON array column.
                sql_type = "JSONB"

            col_def = f"    {field['name']} {sql_type}"

            if field["name"] in _PRIMARY_KEY_FIELDS:
                col_def += " PRIMARY KEY"
            else:
                col_def += " NOT NULL"

            col_lines.append(col_def)

        col_block = ",\n".join(col_lines)
        statements.append(f"CREATE TABLE {table} (\n{col_block}\n);")

    return "\n\n".join(statements) + "\n"


def main() -> None:
    proto_file = sys.argv[1] if len(sys.argv) > 1 else "contracts/user/v1/user.proto"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "generated/sql/user.sql"

    ast = parse_proto(proto_file)
    content = generate_sql(ast)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"[sql] written → {output_file}")


if __name__ == "__main__":
    main()
