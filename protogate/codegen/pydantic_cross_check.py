"""Cross-check contract enums against Pydantic Literal annotations.

A recurring class of bugs when authoring CQRS contracts by hand is that
the JSON ``enum`` in a contract drifts away from the ``Literal[...]`` used
in the Pydantic model that actually implements the request/response.

Concrete c2004 example (2026-04-24, ADR-012 Wave 2):

* ``contracts/GetServiceIdHealth.query.json`` declared
  ``output.checks.database.enum = ["ok", "error"]``
* The Pydantic model ``_ServiceIdHealthChecks.database`` was typed
  ``Literal["ok", "error"]``
* The route handler assigned ``db_status = "degraded"`` under a
  ``# type: ignore`` comment — which Pydantic rejected at runtime.

This validator catches that class of drift at registry time by

1. parsing every contract's ``layers.python`` file with :mod:`ast`
   (no import, no Pydantic required as protogate dependency);
2. collecting every ``Literal[...]`` annotation whose string arguments
   look enum-like (only string literals);
3. for every contract field carrying an ``enum`` key, looking up a
   matching Pydantic model field by name;
4. reporting a drift error if the Literal's value set is not equal
   to the contract's enum set.

Design notes
------------

* AST-based — no runtime import, no Pydantic dependency.
* Supports ``Literal[...]``, ``typing.Literal[...]``,
  ``Optional[Literal[...]]`` and ``Literal[...] | None`` unions.
* Silent skip when no Pydantic field name matches, avoiding false
  positives for response-factory fields like ``success``.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CrossCheckResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def format(self) -> str:
        return "; ".join(self.errors) if self.errors else "ok"


# ---------------------------------------------------------------------------
# Pydantic model extraction (ast-based, no runtime import)
# ---------------------------------------------------------------------------


def _node_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _node_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _literal_slice_values(slice_node: ast.AST) -> set[str] | None:
    values: set[str] = set()
    if isinstance(slice_node, ast.Tuple):
        elements: list[ast.AST] = list(slice_node.elts)
    else:
        elements = [slice_node]
    for el in elements:
        if isinstance(el, ast.Constant) and isinstance(el.value, str):
            values.add(el.value)
        else:
            return None
    return values if values else None


def _extract_literal_values(annotation: ast.AST) -> set[str] | None:
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        left = _extract_literal_values(annotation.left)
        right = _extract_literal_values(annotation.right)
        return left or right
    if isinstance(annotation, ast.Subscript):
        value = annotation.value
        name = _node_name(value)
        if name == "Optional":
            return _extract_literal_values(annotation.slice)
        if name in ("Literal", "typing.Literal"):
            return _literal_slice_values(annotation.slice)
    return None


def _collect_literal_fields(tree: ast.AST) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    values = _extract_literal_values(stmt.annotation)
                    if values is not None:
                        out[stmt.target.id] = values
    return out


def _load_literal_fields(python_path: Path) -> dict[str, set[str]]:
    try:
        source = python_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    return _collect_literal_fields(tree)


# ---------------------------------------------------------------------------
# Contract walking
# ---------------------------------------------------------------------------


def _iter_enum_fields(
    schema: Any, prefix: str = ""
) -> list[tuple[str, list[str]]]:
    """Yield ``(field_name, enum_values)`` pairs for every leaf with ``enum``."""
    results: list[tuple[str, list[str]]] = []
    if not isinstance(schema, dict):
        return results
    for name, spec in schema.items():
        if not isinstance(spec, dict):
            continue
        dotted = f"{prefix}.{name}" if prefix else name
        if isinstance(spec.get("enum"), list):
            values = [v for v in spec["enum"] if isinstance(v, str)]
            if values:
                results.append((name, values))
                if dotted != name:
                    results.append((dotted, values))
        if spec.get("type") == "object" and isinstance(spec.get("properties"), dict):
            results.extend(_iter_enum_fields(spec["properties"], prefix=dotted))
    return results


def _contract_schemas(contract: dict) -> list[dict]:
    blocks: list[dict] = []
    for key in ("input", "output", "payload"):
        block = contract.get(key)
        if isinstance(block, dict):
            blocks.append(block)
    return blocks


def _parse_layer_path(raw_layer: Any) -> str | None:
    if not isinstance(raw_layer, str) or not raw_layer:
        return None
    return raw_layer.split("::", 1)[0]


# ---------------------------------------------------------------------------
# Public API (dict-based; matches protogate.codegen.registry style)
# ---------------------------------------------------------------------------


def cross_check_contract(
    contract: dict,
    layers_root: Path | None = None,
) -> CrossCheckResult:
    """Compare contract enums against Pydantic ``Literal[...]`` annotations
    found in ``layers.python``.

    *contract* is the raw dict loaded by
    :func:`protogate.codegen.registry.load_contracts` (has ``_file`` key).
    """
    result = CrossCheckResult()
    layers = contract.get("layers") or {}
    raw_layer = layers.get("python")
    layer_path = _parse_layer_path(raw_layer)
    if not layer_path:
        return result

    python_path = Path(layer_path)
    if layers_root is not None and not python_path.is_absolute():
        python_path = layers_root / python_path
    if not python_path.is_file():
        return result

    literal_fields = _load_literal_fields(python_path)
    if not literal_fields:
        return result

    contract_file = contract.get("_file", "<unknown>")
    seen: set[str] = set()
    for block in _contract_schemas(contract):
        for field_name, enum_values in _iter_enum_fields(block):
            if field_name in seen:
                continue
            seen.add(field_name)
            base_name = field_name.rsplit(".", 1)[-1]
            pydantic_values = literal_fields.get(base_name)
            if pydantic_values is None:
                continue
            contract_set = set(enum_values)
            if contract_set != pydantic_values:
                missing_in_contract = sorted(pydantic_values - contract_set)
                missing_in_pydantic = sorted(contract_set - pydantic_values)
                parts: list[str] = []
                if missing_in_contract:
                    parts.append(
                        "Pydantic Literal has extra values not in contract enum: "
                        + ", ".join(missing_in_contract)
                    )
                if missing_in_pydantic:
                    parts.append(
                        "Contract enum has extra values not in Pydantic Literal: "
                        + ", ".join(missing_in_pydantic)
                    )
                result.errors.append(
                    f"field {field_name!r} enum drift in {contract_file}: "
                    + " / ".join(parts)
                )

    if result.errors:
        result.ok = False
    return result


def cross_check_contracts(
    contracts: list[dict],
    layers_root: Path | None = None,
) -> list[tuple[dict, CrossCheckResult]]:
    """Run :func:`cross_check_contract` over every contract.

    Returns pairs ``(contract, result)`` in the same order as the input list.
    """
    return [(c, cross_check_contract(c, layers_root=layers_root)) for c in contracts]
