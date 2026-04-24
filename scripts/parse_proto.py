"""
parse_proto.py – lightweight proto-file AST parser.

In a real system this would use the protobuf compiler API (protoc --descriptor_set_out)
or the `buf` JSON-schema export.  Here we provide a self-contained parser that covers
the subset of proto3 needed by this project's generators:

  * package declaration
  * message blocks (nested messages not supported yet)
  * field lines:  <label> <type> <name> = <number>;
  * reserved declarations:  reserved 1, 2;  /  reserved "field_name";
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
# Matches:  reserved 1, 2, 3;   or   reserved 1 to 5;
_RESERVED_NUMBERS_RE = re.compile(
    r"^\s*reserved\s+((?:\d+(?:\s+to\s+\d+)?(?:\s*,\s*)?)+)\s*;"
)
# Matches:  reserved "field_a", "field_b";
_RESERVED_NAMES_RE = re.compile(r'^\s*reserved\s+("[\w"]+.*?)\s*;')


def _parse_reserved_numbers(token: str) -> list[int]:
    """Parse a reserved-numbers token such as ``1, 2, 3`` or ``1 to 5``."""
    numbers: list[int] = []
    for part in token.split(","):
        part = part.strip()
        if "to" in part:
            lo, hi = part.split("to")
            numbers.extend(range(int(lo.strip()), int(hi.strip()) + 1))
        elif part.isdigit():
            numbers.append(int(part))
    return numbers


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
                ],
                "reserved_numbers": [3, 4],
                "reserved_names": ["old_field"],
            },
            ...
        ]
    }
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError as exc:
        raise FileNotFoundError(f"Proto file not found: {file_path}") from exc

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
                current_message = {
                    "name": msg_match.group(1),
                    "fields": [],
                    "reserved_numbers": [],
                    "reserved_names": [],
                }
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
            # Reserved names: reserved "foo", "bar";
            names_match = _RESERVED_NAMES_RE.match(code)
            if names_match:
                raw = names_match.group(1)
                current_message["reserved_names"].extend(
                    n.strip().strip('"') for n in re.findall(r'"(\w+)"', raw)
                )
                continue

            # Reserved numbers: reserved 1, 2; or reserved 1 to 5;
            numbers_match = _RESERVED_NUMBERS_RE.match(code)
            if numbers_match:
                current_message["reserved_numbers"].extend(
                    _parse_reserved_numbers(numbers_match.group(1))
                )
                continue

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
