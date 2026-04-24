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
}


def generate(ast: dict) -> str:
    """Convert a proto AST to Pydantic v2 model source code."""
    lines: list[str] = [
        "from __future__ import annotations",
        "",
        "from typing import List",
        "",
        "from pydantic import BaseModel",
        "",
    ]

    for msg in ast["messages"]:
        lines.append(f"class {msg['name']}(BaseModel):")
        if not msg["fields"]:
            lines.append("    pass")
        else:
            for field in msg["fields"]:
                py_type = _PYTHON_TYPE_MAP.get(field["type"], "object")
                if field["repeated"]:
                    py_type = f"List[{py_type}]"
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
