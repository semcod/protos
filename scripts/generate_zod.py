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
}


def to_zod(ast: dict) -> str:
    """Convert a proto AST to TypeScript Zod schema source code."""
    lines: list[str] = ['import { z } from "zod";', ""]

    for msg in ast["messages"]:
        lines.append(f"export const {msg['name']}Schema = z.object({{")
        for field in msg["fields"]:
            zod_type = _ZOD_TYPE_MAP.get(field["type"], "z.unknown()")
            if field["repeated"]:
                zod_type = f"z.array({zod_type})"
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
