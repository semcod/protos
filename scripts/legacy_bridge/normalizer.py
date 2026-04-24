"""
normalizer.py – normalize different schema formats (JSON Schema, Pydantic, Proto)
into a common NormalizedField structure for comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class NormalizedField:
    name: str
    norm_type: str      # "string" | "int" | "float" | "bool" | "bytes" | "object" | "array"
    repeated: bool      # True for array / repeated
    required: bool
    origin: str         # "proto" | "json_schema" | "pydantic"
    raw_type: str       # original type string


# Mapping from JSON Schema types to normalized types
JSON_SCHEMA_TYPE_MAP = {
    "string": "string",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "array",
    "object": "object",
}

# Mapping from Proto AST types to normalized types
PROTO_TYPE_MAP = {
    "string": "string",
    "int32": "int",
    "int64": "int",
    "uint32": "int",
    "uint64": "int",
    "float": "float",
    "double": "float",
    "bool": "bool",
    "bytes": "bytes",
}


def normalize_json_schema(schema: dict[str, Any], origin: str = "json_schema") -> list[NormalizedField]:
    """
    Normalize a JSON Schema (draft-07) object.
    Expects a schema with 'properties' and 'required' fields.
    """
    fields = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    for name, prop in properties.items():
        raw_type = prop.get("type", "object")
        norm_type = JSON_SCHEMA_TYPE_MAP.get(raw_type, "object")
        repeated = False

        if raw_type == "array":
            repeated = True
            items = prop.get("items", {})
            item_type = items.get("type", "object")
            norm_type = JSON_SCHEMA_TYPE_MAP.get(item_type, "object")

        fields.append(
            NormalizedField(
                name=name,
                norm_type=norm_type,
                repeated=repeated,
                required=name in required_fields,
                origin=origin,
                raw_type=raw_type,
            )
        )
    return fields


def normalize_proto_ast(message_ast: dict[str, Any]) -> list[NormalizedField]:
    """
    Normalize a message from a proto AST (output of parse_proto).
    """
    fields = []
    for f in message_ast.get("fields", []):
        raw_type = f["type"]
        norm_type = PROTO_TYPE_MAP.get(raw_type, "object")
        
        fields.append(
            NormalizedField(
                name=f["name"],
                norm_type=norm_type,
                repeated=f.get("repeated", False),
                required=True,  # Proto3 fields are technically optional but often treated as required in legacy mappings
                origin="proto",
                raw_type=raw_type,
            )
        )
    return fields
