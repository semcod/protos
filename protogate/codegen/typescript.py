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
import re
from types import UnionType
from typing import Any, Callable, Mapping, Sequence, Union, get_args, get_origin, get_type_hints


PRIMITIVE_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    dict: "Record<string, any>",
    list: "any[]",
    type(None): "null",
}


TS_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

# Built-in/global TypeScript symbols that should never require local declarations.
TS_GLOBAL_SYMBOLS: set[str] = {
    "any",
    "unknown",
    "never",
    "void",
    "object",
    "null",
    "undefined",
    "string",
    "number",
    "boolean",
    "bigint",
    "symbol",
    "true",
    "false",
    "Record",
    "Array",
    "Promise",
    "Date",
    "Map",
    "Set",
    "Readonly",
    "Partial",
    "Required",
    "Pick",
    "Omit",
    "Exclude",
    "Extract",
    "NonNullable",
    "Parameters",
    "ReturnType",
    "ConstructorParameters",
    "InstanceType",
    "Awaited",
    "keyof",
    "typeof",
    "infer",
    "extends",
}


def _extract_type_identifiers(ts_type: str) -> set[str]:
    """Extract potential type identifiers from a TypeScript type expression."""
    tokens = set(TS_IDENTIFIER_RE.findall(ts_type))
    return {token for token in tokens if token not in TS_GLOBAL_SYMBOLS}


def _extract_declared_symbols(content: str) -> set[str]:
    """Extract top-level symbol declarations from a TypeScript raw section."""
    symbols: set[str] = set()
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        match = re.match(
            r"^(?:export\s+)?(?:declare\s+)?(?:interface|enum|type|class)\s+([A-Za-z_][A-Za-z0-9_]*)\b",
            stripped,
        )
        if match:
            symbols.add(match.group(1))
    return symbols


def _is_union_origin(origin: Any) -> bool:
    return origin is Union or origin is UnionType


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

    if _is_union_origin(origin):
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
        is_nullable_union = _is_union_origin(get_origin(py_type)) and type(None) in get_args(py_type)
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
        self._declared_symbols: set[str] = set()
        self._referenced_symbols: list[tuple[str, str]] = []
        self._alias_targets: dict[str, str] = {}

    def with_entity_id_base(self, base: type) -> "TypeScriptEmitter":
        self._entity_id_base = base
        return self

    def add_raw(self, content: str) -> "TypeScriptEmitter":
        self._chunks.append(content)
        self._declared_symbols.update(_extract_declared_symbols(content))
        return self

    def add_section(self, title: str) -> "TypeScriptEmitter":
        border = "// " + "=" * 77
        self._chunks.append(f"{border}\n// {title}\n{border}\n")
        return self

    def add_enum(self, enum_class: type[Enum]) -> "TypeScriptEmitter":
        self._chunks.append(generate_enum(enum_class))
        self._chunks.append("")
        self._declared_symbols.add(enum_class.__name__)
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
        interface_name = dataclass_type.__name__
        self._declared_symbols.add(interface_name)

        # Track referenced symbols for fail-fast validation at render-time.
        try:
            hints = get_type_hints(dataclass_type)
        except Exception:
            hints = {}
        for field_def in fields(dataclass_type):
            field_name = field_def.name
            if field_name.startswith("_"):
                continue
            py_type = hints.get(field_name, field_def.type)
            ts_type = python_type_to_typescript(py_type, entity_id_base=base)
            for symbol in _extract_type_identifiers(ts_type):
                self._referenced_symbols.append((f"{interface_name}.{field_name}", symbol))

        self._chunks.append(generate_interface(dataclass_type, entity_id_base=base))
        self._chunks.append("")
        return self

    def _validate_references(self) -> None:
        unresolved: dict[str, list[str]] = {}
        for context, symbol in self._referenced_symbols:
            if symbol in self._declared_symbols:
                continue
            unresolved.setdefault(symbol, []).append(context)

        if not unresolved:
            return

        details = []
        for symbol in sorted(unresolved):
            contexts = ", ".join(unresolved[symbol][:4])
            if len(unresolved[symbol]) > 4:
                contexts += ", ..."
            details.append(f"{symbol} (used in: {contexts})")
        joined = "; ".join(details)
        raise ValueError(
            "Unresolved TypeScript type symbols detected. "
            "Declare the symbols via add_interface/add_enum/add_raw before render(): "
            f"{joined}"
        )

    def add_interfaces(
        self,
        dataclass_types: Sequence[type],
        *,
        entity_id_base: type | None = None,
    ) -> "TypeScriptEmitter":
        for cls in dataclass_types:
            self.add_interface(cls, entity_id_base=entity_id_base)
        return self

    def add_dto_projections(
        self,
        projections: Mapping[str, str] | Sequence[tuple[str, str]],
    ) -> "TypeScriptEmitter":
        """Add first-class DTO projection aliases.

        Example:
            emitter.add_dto_projections({"DeviceDto": "Device"})
            emitter.add_dto_projections([("TestSessionDto", "TestSession")])
        """
        if isinstance(projections, Mapping):
            items = list(projections.items())
        else:
            items = list(projections)

        for dto_name, canonical_name in items:
            if not TS_IDENTIFIER_RE.fullmatch(dto_name):
                raise ValueError(f"Invalid DTO projection alias name: {dto_name}")
            if not TS_IDENTIFIER_RE.fullmatch(canonical_name):
                raise ValueError(f"Invalid DTO projection target name: {canonical_name}")

            existing_target = self._alias_targets.get(dto_name)
            if existing_target is not None and existing_target != canonical_name:
                raise ValueError(
                    f"Conflicting DTO projection for {dto_name}: "
                    f"{existing_target} vs {canonical_name}"
                )
            if dto_name in self._declared_symbols and existing_target is None:
                raise ValueError(
                    f"DTO projection alias '{dto_name}' conflicts with an existing symbol"
                )

            self._chunks.append(f"export type {dto_name} = {canonical_name};")
            self._chunks.append("")
            self._declared_symbols.add(dto_name)
            self._referenced_symbols.append((f"dto_projection:{dto_name}", canonical_name))
            self._alias_targets[dto_name] = canonical_name

        return self

    def add_legacy_name_mappings(
        self,
        canonical_to_legacy: Mapping[str, str] | Sequence[tuple[str, str]],
    ) -> "TypeScriptEmitter":
        """Add canonical <-> legacy name mappings with conflict validation.

        Mapping format: canonical -> legacy, for example
        ``{"Device": "DeviceDto", "TestSession": "TestSessionDto"}``.
        The emitted TypeScript aliases are ``legacy = canonical``.
        """
        if isinstance(canonical_to_legacy, Mapping):
            items = list(canonical_to_legacy.items())
        else:
            items = list(canonical_to_legacy)

        legacy_to_canonical: dict[str, str] = {}
        projections: dict[str, str] = {}
        for canonical_name, legacy_name in items:
            if not TS_IDENTIFIER_RE.fullmatch(canonical_name):
                raise ValueError(f"Invalid canonical mapping name: {canonical_name}")
            if not TS_IDENTIFIER_RE.fullmatch(legacy_name):
                raise ValueError(f"Invalid legacy mapping name: {legacy_name}")

            previous = legacy_to_canonical.get(legacy_name)
            if previous is not None and previous != canonical_name:
                raise ValueError(
                    f"Legacy mapping conflict for {legacy_name}: "
                    f"{previous} vs {canonical_name}"
                )
            legacy_to_canonical[legacy_name] = canonical_name
            projections[legacy_name] = canonical_name

        return self.add_dto_projections(projections)

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
        self._validate_references()
        return self.header() + "\n".join(self._chunks)


__all__ = [
    "PRIMITIVE_TYPE_MAP",
    "python_type_to_typescript",
    "generate_enum",
    "generate_interface",
    "TypeScriptEmitter",
]
