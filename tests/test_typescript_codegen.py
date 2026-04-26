"""Unit tests for protogate TypeScript codegen guard rails."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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
