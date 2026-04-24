"""
parse_proto.py – lightweight proto-file AST parser.

In a real system this would use the protobuf compiler API (protoc --descriptor_set_out)
or the `buf` JSON-schema export.  Here we provide a self-contained parser that covers
the subset of proto3 needed by this project's generators:

  * package declaration
  * message blocks (nested messages supported)
  * enum blocks
  * field lines:  <label> <type> <name> = <number>;
  * map fields: map<K, V> name = number;
  * reserved declarations:  reserved 1, 2;  /  reserved "field_name";
  * import declarations
"""

import re
from dataclasses import dataclass, field
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
    "google.protobuf.Timestamp": "timestamp",
}


@dataclass
class EnumValue:
    name: str
    number: int


@dataclass
class ProtoEnum:
    name: str
    values: list[EnumValue] = field(default_factory=list)


@dataclass
class Field:
    name: str
    type: str
    number: int
    repeated: bool = False
    map_key_type: str | None = None
    map_value_type: str | None = None


@dataclass
class Message:
    name: str
    fields: list[Field] = field(default_factory=list)
    reserved_numbers: list[int] = field(default_factory=list)
    reserved_names: list[str] = field(default_factory=list)
    nested_messages: list["Message"] = field(default_factory=list)
    enums: list[ProtoEnum] = field(default_factory=list)


_FIELD_RE = re.compile(
    r"^\s*"
    r"(?:(repeated|optional|required)\s+)?"  # optional label
    r"(\w+(?:\.\w+)*)\s+"                    # type (supports dotted like google.protobuf.Timestamp)
    r"(\w+)\s*=\s*(\d+)\s*;"                 # name = number;
)
# Matches: map<string, SomeType> field_name = 1;
_MAP_FIELD_RE = re.compile(
    r"^\s*"
    r"map\s*<\s*(\w+)\s*,\s*(\w+)\s*>\s+"  # map<key, value>
    r"(\w+)\s*=\s*(\d+)\s*;"               # name = number;
)
_MESSAGE_START_RE = re.compile(r"^\s*message\s+(\w+)\s*\{")
_ENUM_START_RE = re.compile(r"^\s*enum\s+(\w+)\s*\{")
_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;")
_IMPORT_RE = re.compile(r'^\s*import\s+"([^"]+)"\s*;')
# Matches:  reserved 1, 2, 3;   or   reserved 1 to 5;
_RESERVED_NUMBERS_RE = re.compile(
    r"^\s*reserved\s+((?:\d+(?:\s+to\s+\d+)?(?:\s*,\s*)?)+)\s*;"
)
# Matches:  reserved "field_a", "field_b";
_RESERVED_NAMES_RE = re.compile(r'^\s*reserved\s+("[\w"]+.*?)\s*;')
# Matches enum value: IDENTIFIER_TYPE_RFID = 1;
_ENUM_VALUE_RE = re.compile(r"^\s*(\w+)\s*=\s*(\d+)\s*;")


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


def _to_dict(obj: Any) -> Any:
    """Recursively convert dataclasses to plain dicts for JSON serialisation."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _to_dict(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_to_dict(v) for v in obj]
    return obj


def parse_proto(file_path: str) -> dict[str, Any]:
    """Parse a .proto file and return a simplified AST dict.

    Returns
    -------
    {
        "package": "user.v1",
        "imports": ["google/protobuf/timestamp.proto"],
        "messages": [
            {
                "name": "CreateUserCommand",
                "fields": [
                    {"name": "email", "type": "string", "number": 1, "repeated": False},
                    ...
                ],
                "reserved_numbers": [3, 4],
                "reserved_names": ["old_field"],
                "nested_messages": [...],
                "enums": [...],
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

    ast: dict[str, Any] = {"package": "", "imports": [], "messages": [], "enums": []}
    stack: list[Message] = []  # message stack for nested support
    current_enum: ProtoEnum | None = None

    for line in lines:
        # Strip inline comments
        code = line.split("//")[0]

        pkg_match = _PACKAGE_RE.match(code)
        if pkg_match and not stack:
            ast["package"] = pkg_match.group(1)
            continue

        import_match = _IMPORT_RE.match(code)
        if import_match and not stack:
            ast["imports"].append(import_match.group(1))
            continue

        msg_match = _MESSAGE_START_RE.match(code)
        if msg_match:
            msg = Message(name=msg_match.group(1))
            if stack:
                stack[-1].nested_messages.append(msg)
            stack.append(msg)
            continue

        enum_match = _ENUM_START_RE.match(code)
        if enum_match:
            current_enum = ProtoEnum(name=enum_match.group(1))
            if stack:
                stack[-1].enums.append(current_enum)
            else:
                ast["enums"].append(current_enum)
            continue

        if "{" in code:
            # Already handled message/enum starts above; count extra braces
            pass
        if "}" in code:
            brace_count = code.count("}")
            for _ in range(brace_count):
                if current_enum is not None:
                    # Close enum first (either top-level or inside message)
                    current_enum = None
                    continue
                if stack:
                    finished = stack.pop()
                    if not stack:
                        ast["messages"].append(_to_dict(finished))
            continue

        if current_enum is not None:
            val_match = _ENUM_VALUE_RE.match(code)
            if val_match:
                current_enum.values.append(
                    EnumValue(name=val_match.group(1), number=int(val_match.group(2)))
                )
                continue

        if stack:
            active = stack[-1]

            # Reserved names: reserved "foo", "bar";
            names_match = _RESERVED_NAMES_RE.match(code)
            if names_match:
                raw = names_match.group(1)
                active.reserved_names.extend(
                    n.strip().strip('"') for n in re.findall(r'"(\w+)"', raw)
                )
                continue

            # Reserved numbers: reserved 1, 2; or reserved 1 to 5;
            numbers_match = _RESERVED_NUMBERS_RE.match(code)
            if numbers_match:
                active.reserved_numbers.extend(
                    _parse_reserved_numbers(numbers_match.group(1))
                )
                continue

            # Map fields
            map_match = _MAP_FIELD_RE.match(code)
            if map_match:
                key_type, val_type, fname, fnumber = map_match.groups()
                active.fields.append(
                    Field(
                        name=fname,
                        type="map",
                        number=int(fnumber),
                        map_key_type=key_type,
                        map_value_type=val_type,
                    )
                )
                continue

            field_match = _FIELD_RE.match(code)
            if field_match:
                label, ftype, fname, fnumber = field_match.groups()
                active.fields.append(
                    Field(
                        name=fname,
                        type=SCALAR_TYPE_MAP.get(ftype, ftype),
                        number=int(fnumber),
                        repeated=label == "repeated",
                    )
                )

    # Drain any remaining stack (malformed input tolerance)
    while stack:
        finished = stack.pop()
        if not stack:
            ast["messages"].append(_to_dict(finished))

    ast["enums"] = [_to_dict(e) for e in ast["enums"]]
    return ast


if __name__ == "__main__":
    import json
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "contracts/user/v1/user.proto"
    print(json.dumps(parse_proto(path), indent=2))
