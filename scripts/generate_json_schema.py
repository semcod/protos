"""
generate_json_schema.py – generate JSON Schema (draft-07) from a proto AST.

Usage:
    python scripts/generate_json_schema.py [proto_file] [output_file]

Defaults:
    proto_file  = contracts/user/v1/user.proto
    output_file = generated/schema/user.schema.json
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from parse_proto import parse_proto  # noqa: E402


_JSON_SCHEMA_TYPE_MAP: dict[str, dict] = {
    "string": {"type": "string"},
    "bool": {"type": "boolean"},
    "int32": {"type": "integer"},
    "int64": {"type": "integer"},
    "uint32": {"type": "integer", "minimum": 0},
    "uint64": {"type": "integer", "minimum": 0},
    "float": {"type": "number"},
    "double": {"type": "number"},
    "bytes": {"type": "string", "contentEncoding": "base64"},
}


def generate(ast: dict) -> dict:
    """Convert a proto AST to a JSON Schema definitions object."""
    schemas: dict = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": {},
    }

    for msg in ast["messages"]:
        properties: dict = {}
        required: list[str] = []

        for field in msg["fields"]:
            field_schema = dict(_JSON_SCHEMA_TYPE_MAP.get(field["type"], {"type": "object"}))
            if field["repeated"]:
                field_schema = {"type": "array", "items": field_schema}
            properties[field["name"]] = field_schema
            required.append(field["name"])

        schemas["definitions"][msg["name"]] = {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    return schemas


def main() -> None:
    proto_file = sys.argv[1] if len(sys.argv) > 1 else "contracts/user/v1/user.proto"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "generated/schema/user.schema.json"

    ast = parse_proto(proto_file)
    content = generate(ast)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(content, fh, indent=2)
        fh.write("\n")

    print(f"[json-schema] written → {output_file}")


if __name__ == "__main__":
    main()
