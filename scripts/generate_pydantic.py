"""
generate_pydantic.py – generate Python Pydantic v2 models from a proto AST.

Usage:
    python scripts/generate_pydantic.py [proto_file] [output_file]

Defaults:
    proto_file  = contracts/user/v1/user.proto
    output_file = generated/python/user_models.py
"""

import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))

from parse_proto import parse_proto  # noqa: E402


_PYTHON_TYPE_MAP: dict[str, str] = {
    "string": "str",
    "bool": "bool",
    "int32": "int",
    "int64": "int",
    "uint32": "int",
    "uint64": "int",
    "float": "float",
    "double": "float",
    "bytes": "bytes",
    "timestamp": "datetime.datetime",
}


def _flatten_messages(ast: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all messages (top-level + nested, recursively) as flat list."""
    result: list[dict[str, Any]] = []

    def walk(msgs: list[dict[str, Any]]) -> None:
        for msg in msgs:
            result.append(msg)
            walk(msg.get("nested_messages", []))

    walk(ast.get("messages", []))
    return result


def _flatten_enums(ast: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all enums from all messages and top-level as flat list."""
    result: list[dict[str, Any]] = list(ast.get("enums", []))

    def walk(msgs: list[dict[str, Any]]) -> None:
        for msg in msgs:
            result.extend(msg.get("enums", []))
            walk(msg.get("nested_messages", []))

    walk(ast.get("messages", []))
    return result


def _py_type(field: dict[str, Any], message_names: set[str], enum_names: set[str]) -> str:
    """Map a single proto field to a Python type annotation."""
    if field.get("map_key_type"):
        key_type = _PYTHON_TYPE_MAP.get(field["map_key_type"], field["map_key_type"])
        val_type = _PYTHON_TYPE_MAP.get(field["map_value_type"], field["map_value_type"])
        # If value type is a nested message or enum, use its name directly
        if field["map_value_type"] in message_names:
            val_type = field["map_value_type"]
        elif field["map_value_type"] in enum_names:
            val_type = field["map_value_type"]
        return f"dict[{key_type}, {val_type}]"

    ftype = field["type"]
    if ftype in enum_names:
        py_type = ftype
    elif ftype in message_names:
        py_type = ftype
    else:
        py_type = _PYTHON_TYPE_MAP.get(ftype, "object")

    if field.get("repeated"):
        return f"list[{py_type}]"
    return py_type


def generate(ast: dict[str, Any]) -> str:
    """Convert a proto AST to Pydantic v2 model + enum source code."""
    lines: list[str] = [
        "from __future__ import annotations",
        "",
        "import datetime",
        "from enum import Enum",
        "from typing import List, Dict",
        "",
        "from pydantic import BaseModel",
        "",
    ]

    has_timestamp = any(
        f["type"] == "timestamp"
        for msg in _flatten_messages(ast)
        for f in msg.get("fields", [])
    )
    # datetime import already unconditional for simplicity
    _ = has_timestamp  # silence unused warning if any

    all_enums = _flatten_enums(ast)
    for enm in all_enums:
        lines.append(f"class {enm['name']}(Enum):")
        for val in enm.get("values", []):
            lines.append(f"    {val['name']} = {val['number']}")
        lines.append("")

    all_messages = _flatten_messages(ast)
    message_names = {m["name"] for m in all_messages}
    enum_names = {e["name"] for e in all_enums}

    for msg in all_messages:
        lines.append(f"class {msg['name']}(BaseModel):")
        if not msg.get("fields"):
            lines.append("    pass")
        else:
            for field in msg["fields"]:
                py_type = _py_type(field, message_names, enum_names)
                lines.append(f"    {field['name']}: {py_type}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    proto_file = sys.argv[1] if len(sys.argv) > 1 else "contracts/user/v1/user.proto"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "generated/python/user_models.py"

    ast = parse_proto(proto_file)
    content = generate(ast)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"[pydantic] written → {output_file}")


if __name__ == "__main__":
    main()
