"""Zod TypeScript validator generator from JSON Schema.

Reads ``*.schema.json`` files from a directory and emits ``*.validator.ts``
files using the ``zod`` library, plus a barrel ``index.ts``.

Ported from ``c2004/scripts/generate_zod_validators.mjs`` (ADR-010 Sprint C).
Logic is faithful to the JS version; only the host language differs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def json_schema_to_zod(schema: Any, *, indent: str = "") -> str:
    """Convert a JSON Schema (Python dict) to a Zod expression string."""
    if not isinstance(schema, dict):
        return "z.unknown()"

    # $ref → ReferenceSchema
    ref = schema.get("$ref")
    if ref:
        ref_name = ref.split("/")[-1]
        return f"{ref_name}Schema"

    # anyOf → nullable or union
    any_of = schema.get("anyOf")
    if any_of:
        non_null = [s for s in any_of if s.get("type") != "null"]
        has_null = any(s.get("type") == "null" for s in any_of)
        if len(non_null) == 1:
            base = json_schema_to_zod(non_null[0], indent=indent)
            return f"{base}.nullable()" if has_null else base
        variants = [json_schema_to_zod(s, indent=indent) for s in any_of]
        return f"z.union([{', '.join(variants)}])"

    # enum
    if "enum" in schema:
        values = [json.dumps(v) for v in schema["enum"]]
        if len(values) == 1:
            return f"z.literal({values[0]})"
        return f"z.enum([{', '.join(values)}])"

    # const
    if "const" in schema:
        return f"z.literal({json.dumps(schema['const'])})"

    type_ = schema.get("type")

    if type_ == "string":
        chain = "z.string()"
        fmt = schema.get("format")
        if fmt == "date-time":
            chain = "z.string().datetime()"
        elif fmt == "email":
            chain = "z.string().email()"
        elif fmt == "uri":
            chain = "z.string().url()"
        if "minLength" in schema:
            chain += f".min({schema['minLength']})"
        if "maxLength" in schema:
            chain += f".max({schema['maxLength']})"
        if "pattern" in schema and fmt not in ("date-time", "email", "uri"):
            chain += f".regex(/{schema['pattern']}/)"
        return chain

    if type_ == "number" or type_ == "integer":
        chain = "z.number().int()" if type_ == "integer" else "z.number()"
        if "minimum" in schema:
            chain += f".min({schema['minimum']})"
        if "maximum" in schema:
            chain += f".max({schema['maximum']})"
        return chain

    if type_ == "boolean":
        return "z.boolean()"

    if type_ == "array":
        items = schema.get("items")
        inner = json_schema_to_zod(items, indent=indent) if items else "z.unknown()"
        return f"z.array({inner})"

    if type_ == "object":
        properties = schema.get("properties")
        if not properties:
            additional = schema.get("additionalProperties")
            if isinstance(additional, dict):
                return f"z.record(z.string(), {json_schema_to_zod(additional, indent=indent)})"
            return "z.record(z.string(), z.unknown())"

        required = set(schema.get("required", []))
        inner_indent = indent + "  "
        prop_lines: list[str] = []
        for key, prop in properties.items():
            zod_type = json_schema_to_zod(prop, indent=inner_indent)
            opt_suffix = "" if key in required else ".optional()"
            def_val = ""
            if isinstance(prop, dict) and "default" in prop:
                def_val = f".default({json.dumps(prop['default'])})"
            prop_lines.append(f"{inner_indent}{key}: {zod_type}{opt_suffix}{def_val},")
        body = "\n".join(prop_lines)
        return f"z.object({{\n{body}\n{indent}}})"

    if type_ == "null":
        return "z.null()"

    return "z.unknown()"


def _collect_refs(schema: Any) -> set[str]:
    refs: set[str] = set()
    if not isinstance(schema, (dict, list)):
        return refs
    if isinstance(schema, dict):
        if "$ref" in schema and isinstance(schema["$ref"], str):
            refs.add(schema["$ref"].split("/")[-1])
        for val in schema.values():
            refs |= _collect_refs(val)
    else:
        for item in schema:
            refs |= _collect_refs(item)
    return refs


def _topo_sort_defs(defs: dict[str, Any]) -> list[str]:
    visited: set[str] = set()
    order: list[str] = []

    def visit(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        for ref in _collect_refs(defs.get(name, {})):
            if ref in defs:
                visit(ref)
        order.append(name)

    for name in defs:
        visit(name)
    return order


def _pascal_from_kebab(name: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in name.split("-") if part)


def schema_file_to_zod(schema_path: Path) -> tuple[str, list[str]]:
    """Convert a single ``*.schema.json`` file to Zod TypeScript source.

    Returns
    -------
    (content, exported_names)
    """
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    name = schema_path.name
    if name.endswith(".schema.json"):
        name = name[: -len(".schema.json")]

    defs = schema.get("$defs", schema.get("definitions", {})) or {}
    sorted_defs = _topo_sort_defs(defs)

    lines: list[str] = [
        f"// Auto-generated from {schema_path.name}",
        "// Do not edit manually — regenerate with: protogate codegen zod",
        "",
        "import { z } from 'zod';",
        "",
    ]

    exported: list[str] = []
    for def_name in sorted_defs:
        expr = json_schema_to_zod(defs[def_name])
        lines.append(f"export const {def_name}Schema = {expr};")
        lines.append(f"export type {def_name} = z.infer<typeof {def_name}Schema>;")
        lines.append("")
        exported.append(def_name)

    pascal = _pascal_from_kebab(name)
    expr = json_schema_to_zod(schema)
    lines.append(f"export const {pascal}Schema = {expr};")
    lines.append(f"export type {pascal} = z.infer<typeof {pascal}Schema>;")
    lines.append("")
    exported.append(pascal)

    return "\n".join(lines), exported


def run_cli(input_dir: Path, output_dir: Path, *, verbose: bool = True) -> int:
    input_dir = input_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    schema_files = sorted(
        p for p in input_dir.iterdir() if p.name.endswith(".schema.json")
    )
    if not schema_files:
        print(f"❌ No .schema.json files found in {input_dir}", file=__import__("sys").stderr)
        print("   Run: protogate codegen json-schema first", file=__import__("sys").stderr)
        return 1

    if verbose:
        print(f"🔧 Generating Zod validators from {len(schema_files)} schemas")
        print()

    global_first: dict[str, str] = {}
    module_exports: list[tuple[str, list[str]]] = []

    for schema_file in schema_files:
        if schema_file.name.startswith("_"):
            continue
        content, exported = schema_file_to_zod(schema_file)
        ts_name = schema_file.name.replace(".schema.json", ".validator.ts")
        (output_dir / ts_name).write_text(content, encoding="utf-8")
        module_name = schema_file.name.replace(".schema.json", "")
        module_exports.append((module_name, exported))
        for export_name in exported:
            global_first.setdefault(export_name, module_name)
        if verbose:
            print(f"  ✅ {schema_file.name} → {ts_name}")

    index_lines: list[str] = ["// Auto-generated barrel export — do not edit manually"]
    for module_name, exported in sorted(module_exports, key=lambda x: x[0]):
        own = [n for n in exported if global_first.get(n) == module_name]
        if not own:
            continue
        if len(own) == len(exported):
            index_lines.append(f"export * from './{module_name}.validator';")
        else:
            values = ", ".join(f"{n}Schema" for n in own)
            types = ", ".join(own)
            index_lines.append(
                f"export {{ {values} }} from './{module_name}.validator';"
            )
            index_lines.append(
                f"export type {{ {types} }} from './{module_name}.validator';"
            )
    index_lines.append("")
    (output_dir / "index.ts").write_text("\n".join(index_lines), encoding="utf-8")

    if verbose:
        print()
        print(f"📦 Generated {len(schema_files)} validator files + index.ts")
        print(f"📁 Output: {output_dir}/")
    return 0


__all__ = [
    "json_schema_to_zod",
    "schema_file_to_zod",
    "run_cli",
]
