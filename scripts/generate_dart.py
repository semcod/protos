"""
generate_dart.py – generate Dart/Flutter model classes from a proto AST.

Produces immutable Dart classes with ``fromJson`` / ``toJson`` helpers
compatible with the ``json_serializable`` package conventions.

Usage:
    python scripts/generate_dart.py [proto_file] [output_file]

Defaults:
    proto_file  = contracts/user/v1/user.proto
    output_file = generated/dart/user_models.dart
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from parse_proto import parse_proto  # noqa: E402


_DART_TYPE_MAP: dict[str, str] = {
    "string": "String",
    "bool": "bool",
    "int32": "int",
    "int64": "int",
    "uint32": "int",
    "uint64": "int",
    "float": "double",
    "double": "double",
    "bytes": "String",  # base64 string convention
}


def _dart_type(proto_type: str, repeated: bool) -> str:
    dart = _DART_TYPE_MAP.get(proto_type, "dynamic")
    return f"List<{dart}>" if repeated else dart


def generate(ast: dict) -> str:
    """Convert a proto AST to Dart model class source code."""
    package = ast.get("package", "")
    lines: list[str] = [
        f"// Generated from proto package: {package}",
        "// ignore_for_file: always_specify_types",
        "",
    ]

    for msg in ast["messages"]:
        name = msg["name"]
        fields = msg["fields"]

        # Class declaration
        lines.append(f"class {name} {{")

        # Fields
        for field in fields:
            dart_t = _dart_type(field["type"], field["repeated"])
            lines.append(f"  final {dart_t} {field['name']};")

        lines.append("")

        # Constructor
        if fields:
            params = ", ".join(f"required this.{f['name']}" for f in fields)
            lines.append(f"  const {name}({{{params}}});")
        else:
            lines.append(f"  const {name}();")

        lines.append("")

        # fromJson factory
        lines.append(f"  factory {name}.fromJson(Map<String, dynamic> json) {{")
        lines.append(f"    return {name}(")
        for field in fields:
            dart_t = _dart_type(field["type"], field["repeated"])
            if field["repeated"]:
                inner = _DART_TYPE_MAP.get(field["type"], "dynamic")
                lines.append(
                    f"      {field['name']}: (json['{field['name']}'] as List<dynamic>)"
                    f".cast<{inner}>(),"
                )
            else:
                lines.append(f"      {field['name']}: json['{field['name']}'] as {dart_t},")
        lines.append("    );")
        lines.append("  }")

        lines.append("")

        # toJson method
        lines.append("  Map<String, dynamic> toJson() {")
        lines.append("    return {")
        for field in fields:
            lines.append(f"      '{field['name']}': {field['name']},")
        lines.append("    };")
        lines.append("  }")

        lines.append("}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    proto_file = sys.argv[1] if len(sys.argv) > 1 else "contracts/user/v1/user.proto"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "generated/dart/user_models.dart"

    ast = parse_proto(proto_file)
    content = generate(ast)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(f"[dart] written → {output_file}")


if __name__ == "__main__":
    main()
