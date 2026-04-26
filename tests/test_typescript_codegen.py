"""Unit tests for protogate TypeScript codegen guard rails."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Union

import pytest

from protogate.codegen.typescript import TypeScriptEmitter


class Status(Enum):
    OK = "ok"
    ERROR = "error"


@dataclass
class Child:
    status: Status


@dataclass
class Parent:
    child: Child


@dataclass
class Broken:
    missing: MissingType


@dataclass(frozen=True)
class GoldenEntityId:
    value: str


@dataclass(frozen=True)
class GoldenDeviceId(GoldenEntityId):
    pass


class GoldenSeverity(Enum):
    LOW = "low"
    HIGH = "high"


@dataclass
class GoldenChild:
    score: float


@dataclass
class GoldenModel:
    device_id: GoldenDeviceId
    severity: GoldenSeverity
    child: GoldenChild
    tags: list[str]
    props: dict[str, int]
    either: Union[str, int]
    note: str | None = None
    retries: int = 0


def _normalize_generated(content: str) -> str:
    lines = []
    for line in content.splitlines():
        if line.startswith("// Generated from ") and " on " in line:
            prefix, _timestamp = line.split(" on ", 1)
            lines.append(f"{prefix} on <TIMESTAMP>")
            continue
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def test_render_succeeds_for_declared_symbols() -> None:
    emitter = TypeScriptEmitter(source_description="test")
    content = (
        emitter
        .add_enum(Status)
        .add_interface(Child)
        .add_interface(Parent)
        .render()
    )
    assert "export enum Status" in content
    assert "export interface Parent" in content


def test_render_fails_for_unresolved_symbol() -> None:
    emitter = TypeScriptEmitter(source_description="test")
    emitter.add_interface(Broken)

    with pytest.raises(ValueError, match="Unresolved TypeScript type symbols"):
        emitter.render()


def test_raw_declared_symbol_satisfies_reference() -> None:
    emitter = TypeScriptEmitter(source_description="test")
    emitter.add_raw("export interface MissingType { id: string; }")
    emitter.add_interface(Broken)

    content = emitter.render()
    assert "export interface MissingType" in content
    assert "export interface Broken" in content


def test_typescript_emitter_golden_snapshot() -> None:
    emitter = (
        TypeScriptEmitter(source_description="golden", script_hint="python demo_codegen.py")
        .with_entity_id_base(GoldenEntityId)
    )
    content = (
        emitter
        .add_section("ENUMS")
        .add_enum(GoldenSeverity)
        .add_section("MODELS")
        .add_interface(GoldenChild)
        .add_interface(GoldenModel)
        .add_section("ALIASES")
        .add_dto_projections({"GoldenModelDto": "GoldenModel"})
        .render()
    )

    normalized = _normalize_generated(content)
    fixture = Path(__file__).parent / "fixtures" / "typescript_emitter_golden.expected.ts"
    expected = fixture.read_text(encoding="utf-8")
    assert normalized == expected


def test_add_dto_projections_accepts_sequence() -> None:
    emitter = TypeScriptEmitter(source_description="dto")
    content = (
        emitter
        .add_enum(Status)
        .add_interface(Child)
        .add_dto_projections([("ChildDto", "Child")])
        .render()
    )
    assert "export type ChildDto = Child;" in content


def test_add_dto_projections_fails_for_unresolved_target() -> None:
    emitter = TypeScriptEmitter(source_description="dto")
    emitter.add_dto_projections({"ChildDto": "MissingChild"})
    with pytest.raises(ValueError, match="Unresolved TypeScript type symbols"):
        emitter.render()


def test_add_legacy_name_mappings_generates_aliases() -> None:
    emitter = TypeScriptEmitter(source_description="legacy")
    content = (
        emitter
        .add_enum(Status)
        .add_interface(Child)
        .add_legacy_name_mappings({"Child": "ChildDto"})
        .render()
    )
    assert "export type ChildDto = Child;" in content


def test_add_legacy_name_mappings_fails_on_legacy_name_conflict() -> None:
    emitter = TypeScriptEmitter(source_description="legacy")
    with pytest.raises(ValueError, match="Legacy mapping conflict"):
        emitter.add_legacy_name_mappings([
            ("Child", "SharedDto"),
            ("Parent", "SharedDto"),
        ])


def test_add_legacy_name_mappings_fails_on_existing_symbol_conflict() -> None:
    emitter = TypeScriptEmitter(source_description="legacy")
    emitter.add_enum(Status)
    with pytest.raises(ValueError, match="conflicts with an existing symbol"):
        emitter.add_legacy_name_mappings({"Child": "Status"})
