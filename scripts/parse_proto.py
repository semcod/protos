"""
parse_proto.py – lightweight proto-file AST parser.

In a real system this would use the protobuf compiler API (protoc --descriptor_set_out)
or the `buf` JSON-schema export.  Here we provide a self-contained parser that covers
the subset of proto3 needed by this project's generators:

  * package declaration
  * message blocks (nested messages not supported yet)
  * field lines:  <label> <type> <name> = <number>;
"""

import re
from typing import Any


# Map proto scalar types to a normalised internal type name.
SCALAR_TYPE_MAP: dict[str, str] = {
    "string": "string",
    "bool": "bool",
    "int32": "int32",
    "int64": "int64",
    "uint32": "uint32",
    "uint64": "uint64",
    "float": "float",
    "double": "double",
    "bytes": "bytes",
}

_FIELD_RE = re.compile(
    r"^\s*"
    r"(?:(repeated|optional|required)\s+)?"  # optional label
    r"(\w+)\s+"                               # type
    r"(\w+)\s*=\s*(\d+)\s*;"                 # name = number;
)
_MESSAGE_START_RE = re.compile(r"^\s*message\s+(\w+)\s*\{")
_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;")


def parse_proto(file_path: str) -> dict[str, Any]:
    """Parse a .proto file and return a simplified AST dict.

    Returns
    -------
    {
        "package": "user.v1",
        "messages": [
            {
                "name": "CreateUserCommand",
                "fields": [
                    {"name": "email", "type": "string", "number": 1, "repeated": False},
                    ...
                ]
            },
            ...
        ]
    }
    """
    with open(file_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    ast: dict[str, Any] = {"package": "", "messages": []}
    current_message: dict[str, Any] | None = None
    depth = 0

    for line in lines:
        # Strip inline comments
        code = line.split("//")[0]

        pkg_match = _PACKAGE_RE.match(code)
        if pkg_match and depth == 0:
            ast["package"] = pkg_match.group(1)
            continue

        msg_match = _MESSAGE_START_RE.match(code)
        if msg_match:
            depth += 1
            if depth == 1:
                current_message = {"name": msg_match.group(1), "fields": []}
            continue

        if "{" in code:
            depth += code.count("{")
        if "}" in code:
            depth -= code.count("}")
            if depth == 0 and current_message is not None:
                ast["messages"].append(current_message)
                current_message = None
            continue

        if current_message is not None and depth == 1:
            field_match = _FIELD_RE.match(code)
            if field_match:
                label, ftype, fname, fnumber = field_match.groups()
                current_message["fields"].append(
                    {
                        "name": fname,
                        "type": SCALAR_TYPE_MAP.get(ftype, ftype),
                        "number": int(fnumber),
                        "repeated": label == "repeated",
                    }
                )

    return ast


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "contracts/user/v1/user.proto"
    print(json.dumps(parse_proto(path), indent=2))
