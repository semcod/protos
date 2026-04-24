"""TypeScript code generator from Python dataclasses / Enums.

Reusable library used by ``protogate codegen ts-from-python``. Ported from
``c2004/scripts/generate-typescript-types.py`` (ADR-010 Sprint B).

The generic primitives (type mapping, enum/interface rendering) live here.
Repo-specific orchestration (which classes to export, factory functions,
boilerplate blocks) stays in the calling script which uses ``TypeScriptEmitter``.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Sequence, Union, get_args, get_origin, get_type_hints


PRIMITIVE_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    dict: "Record<string, any>",
    list: "any[]",
    type(None): "null",
}


def python_type_to_typescript(
    py_type: Any,
    *,
    entity_id_base: type | None = None,
) -> str:
    """Convert a Python type annotation to a TypeScript type expression.

    Parameters
    ----------
    py_type:
        The Python type annotation.
    entity_id_base:
        Optional base class. Any ``type`` that is a subclass of this base is
        emitted as ``string`` (domain-specific ID aliasing).
    """
    if py_type is type(None):
        return "null"

    if py_type in PRIMITIVE_TYPE_MAP:
        return PRIMITIVE_TYPE_MAP[py_type]

    origin = get_origin(py_type)
    args = get_args(py_type)

    if origin is dict:
        if args:
            key_type = python_type_to_typescript(args[0], entity_id_base=entity_id_base)
            val_type = python_type_to_typescript(args[1], entity_id_base=entity_id_base)
            return f"Record<{key_type}, {val_type}>"
        return "Record<string, any>"

    if origin is list:
        if args:
            item_type = python_type_to_typescript(args[0], entity_id_base=entity_id_base)
            return f"{item_type}[]"
        return "any[]"

    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            return f"{python_type_to_typescript(non_none[0], entity_id_base=entity_id_base)} | null"
        return " | ".join(
            python_type_to_typescript(a, entity_id_base=entity_id_base) for a in args
        )

    if isinstance(py_type, type) and issubclass(py_type, Enum):
        return py_type.__name__

    if isinstance(py_type, type):
        if entity_id_base is not None and issubclass(py_type, entity_id_base):
            return "string"
        if is_dataclass(py_type):
            return py_type.__name__

    if isinstance(py_type, str):
        return py_type

    return "any"


def generate_enum(enum_class: type[Enum]) -> str:
    """Render a Python ``Enum`` as a TypeScript ``enum`` block."""
    lines = [f"export enum {enum_class.__name__} {{"]
    for member in enum_class:
        lines.append(f'  {member.name} = "{member.value}",')
    lines.append("}")
    return "\n".join(lines)


def generate_interface(
    dataclass_type: type,
    *,
    entity_id_base: type | None = None,
    skip_private: bool = True,
) -> str:
    """Render a Python dataclass as a TypeScript ``interface`` block."""
    if not is_dataclass(dataclass_type):
        return ""

    lines = [f"export interface {dataclass_type.__name__} {{"]

    try:
        hints = get_type_hints(dataclass_type)
    except Exception:
        hints = {}

    for field_def in fields(dataclass_type):
        field_name = field_def.name
        if skip_private and field_name.startswith("_"):
            continue

        py_type = hints.get(field_name, field_def.type)
        ts_type = python_type_to_typescript(py_type, entity_id_base=entity_id_base)

        has_default = (
            field_def.default is not None
            and field_def.default != field_def.default_factory
        )
        is_nullable_union = get_origin(py_type) is Union and type(None) in get_args(py_type)
        is_optional = has_default or is_nullable_union
        optional_marker = "?" if is_optional else ""
        lines.append(f"  {field_name}{optional_marker}: {ts_type};")

    lines.append("}")
    return "\n".join(lines)


class TypeScriptEmitter:
    """Fluent builder for a single generated TypeScript file.

    Usage from a thin wrapper script::

        emitter = TypeScriptEmitter(source_description="c2004 shared types")
        emitter.add_section("ENUMS")
        emitter.add_enum(DeviceStatus)
        emitter.add_section("DTOs")
        emitter.add_interface(DeviceDto, entity_id_base=EntityId)
        emitter.add_raw(FACTORIES_BLOCK)
        output.write_text(emitter.render())
    """

    def __init__(self, *, source_description: str = "Python types", script_hint: str | None = None):
        self._chunks: list[str] = []
        self._source_description = source_description
        self._script_hint = script_hint
        self._entity_id_base: type | None = None

    def with_entity_id_base(self, base: type) -> "TypeScriptEmitter":
        self._entity_id_base = base
        return self

    def add_raw(self, content: str) -> "TypeScriptEmitter":
        self._chunks.append(content)
        return self

    def add_section(self, title: str) -> "TypeScriptEmitter":
        border = "// " + "=" * 77
        self._chunks.append(f"{border}\n// {title}\n{border}\n")
        return self

    def add_enum(self, enum_class: type[Enum]) -> "TypeScriptEmitter":
        self._chunks.append(generate_enum(enum_class))
        self._chunks.append("")
        return self

    def add_enums(self, enum_classes: Sequence[type[Enum]]) -> "TypeScriptEmitter":
        for cls in enum_classes:
            self.add_enum(cls)
        return self

    def add_interface(
        self,
        dataclass_type: type,
        *,
        entity_id_base: type | None = None,
    ) -> "TypeScriptEmitter":
        base = entity_id_base if entity_id_base is not None else self._entity_id_base
        self._chunks.append(generate_interface(dataclass_type, entity_id_base=base))
        self._chunks.append("")
        return self

    def add_interfaces(
        self,
        dataclass_types: Sequence[type],
        *,
        entity_id_base: type | None = None,
    ) -> "TypeScriptEmitter":
        for cls in dataclass_types:
            self.add_interface(cls, entity_id_base=entity_id_base)
        return self

    def header(self) -> str:
        border = "// " + "=" * 77
        lines = [
            border,
            "// AUTO-GENERATED FILE - DO NOT EDIT MANUALLY",
            f"// Generated from {self._source_description} on {datetime.now().isoformat()}",
        ]
        if self._script_hint:
            lines.append(f"// Run: {self._script_hint}")
        lines.extend([border, "", ""])
        return "\n".join(lines)

    def render(self) -> str:
        return self.header() + "\n".join(self._chunks)


__all__ = [
    "PRIMITIVE_TYPE_MAP",
    "python_type_to_typescript",
    "generate_enum",
    "generate_interface",
    "TypeScriptEmitter",
]
