"""
generate_zod.py – generate TypeScript Zod schemas from a proto AST.

Usage:
    python scripts/generate_zod.py [proto_file] [output_file]

Defaults:
    proto_file  = contracts/user/v1/user.proto
    output_file = generated/ts/zod/user.ts
"""

import os
import sys
from typing import Any

# Allow running from the repo root without installing the package.
sys.path.insert(0, os.path.dirname(__file__))

from parse_proto import parse_proto  # noqa: E402


_ZOD_TYPE_MAP: dict[str, str] = {
    "string": "z.string()",
    "bool": "z.boolean()",
    "int32": "z.number().int()",
    "int64": "z.number().int()",
    "uint32": "z.number().int().nonnegative()",
    "uint64": "z.number().int().nonnegative()",
    "float": "z.number()",
    "double": "z.number()",
    "bytes": "z.string()",  # base64 string convention
    "timestamp": "z.string().datetime()",
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


def _zod_type(field: dict[str, Any], message_names: set[str], enum_names: set[str]) -> str:
    """Map a single proto field to a Zod schema expression."""
    if field.get("map_key_type"):
        key_type = _ZOD_TYPE_MAP.get(field["map_key_type"], field["map_key_type"])
        val_type = _ZOD_TYPE_MAP.get(field["map_value_type"], field["map_value_type"])
        if field["map_value_type"] in message_names:
            val_type = f"{field['map_value_type']}Schema"
        elif field["map_value_type"] in enum_names:
            val_type = f"z.nativeEnum({field['map_value_type']})"
        return f"z.record({key_type}, {val_type})"

    ftype = field["type"]
    if ftype in enum_names:
        zod_type = f"z.nativeEnum({ftype})"
    elif ftype in message_names:
        zod_type = f"z.lazy(() => {ftype}Schema)"
    else:
        zod_type = _ZOD_TYPE_MAP.get(ftype, "z.unknown()")

    if field.get("repeated"):
        return f"z.array({zod_type})"
    return zod_type


def to_zod(ast: dict[str, Any]) -> str:
    """Convert a proto AST to TypeScript Zod schema source code."""
    lines: list[str] = ['import { z } from "zod";', ""]

    all_enums = _flatten_enums(ast)
    for enm in all_enums:
        lines.append(f"export enum {enm['name']} {{")
        for val in enm.get("values", []):
            lines.append(f"  {val['name']} = {val['number']},")
        lines.append("}")
        lines.append("")

    all_messages = _flatten_messages(ast)
    message_names = {m["name"] for m in all_messages}
    enum_names = {e["name"] for e in all_enums}

    for msg in all_messages:
        lines.append(f"export const {msg['name']}Schema = z.object({{")
        for field in msg.get("fields", []):
            zod_type = _zod_type(field, message_names, enum_names)
            lines.append(f"  {field['name']}: {zod_type},")
        lines.append("});")
        lines.append(f"export type {msg['name']} = z.infer<typeof {msg['name']}Schema>;")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    proto_file = sys.argv[1] if len(sys.argv) > 1 else "contracts/user/v1/user.proto"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "generated/ts/zod/user.ts"

    ast = parse_proto(proto_file)
    content = to_zod(ast)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"[zod] written → {output_file}")


if __name__ == "__main__":
    main()
