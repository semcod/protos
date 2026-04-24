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
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ContractFix:
    """Structural description of a JSON-only auto-fix for contract enum drift.

    The fix is **always applied to the contract JSON** (never to Python
    Pydantic source). Two actions are supported:

    * ``remove_extra`` -- drop values from the contract enum that Pydantic
      cannot produce (safe cleanup of dead code paths; warning-level).
    * ``expand_contract`` -- add values to the contract enum that Pydantic
      can produce but the contract did not advertise (error-level; fixes
      the Wave 2 regression scenario).

    The ``expand_contract`` action is opt-in because it can hide a server-
    side bug: if Pydantic happens to list a value by accident, expanding
    the contract silently blesses that accident. Callers must pass
    ``include_error_expansion=True`` to :func:`apply_fixes_to_contract`.
    """

    block_kind: str              # "input" | "output" | "payload"
    field_path: str              # dotted path inside the block, e.g. "checks.database"
    action: str                  # "remove_extra" | "expand_contract"
    values: list[str]            # values to remove (remove_extra) or add (expand_contract)
    severity: str                # "warning" | "error"
    rationale: str               # one-line human explanation

    def describe(self) -> str:
        verb = "remove" if self.action == "remove_extra" else "add"
        return (
            f"{self.block_kind} field {self.field_path!r}: {verb} "
            f"{sorted(self.values)!r} ({self.rationale})"
        )


@dataclass
class CrossCheckResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fixes: list[ContractFix] = field(default_factory=list)

    def format(self) -> str:
        parts: list[str] = []
        if self.errors:
            parts.append("errors: " + "; ".join(self.errors))
        if self.warnings:
            parts.append("warnings: " + "; ".join(self.warnings))
        return " | ".join(parts) if parts else "ok"

    def auto_fixable_fixes(self, include_error_expansion: bool = False) -> list[ContractFix]:
        """Return the subset of fixes safe to apply without human review.

        Always includes ``remove_extra`` (warning-level). Includes
        ``expand_contract`` only when *include_error_expansion* is True.
        """
        out: list[ContractFix] = []
        for fix in self.fixes:
            if fix.action == "remove_extra":
                out.append(fix)
            elif fix.action == "expand_contract" and include_error_expansion:
                out.append(fix)
        return out


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


def _contract_schemas(contract: dict) -> list[tuple[str, dict]]:
    """Return ``(block_kind, schema)`` pairs for every block present.

    *block_kind* is one of ``"input"``, ``"output"``, ``"payload"``. The kind
    determines the direction of the subset check (see
    :func:`_classify_drift`).
    """
    blocks: list[tuple[str, dict]] = []
    for key in ("input", "output", "payload"):
        block = contract.get(key)
        if isinstance(block, dict):
            blocks.append((key, block))
    return blocks


def _classify_drift(
    block_kind: str,
    contract_set: set[str],
    pydantic_set: set[str],
) -> tuple[str, str] | None:
    """Return ``(severity, detail)`` for a drift between *contract_set* and
    *pydantic_set*, or ``None`` if the two are compatible.

    Directional rules (ADR-012 Wave 2 post-mortem):

    * ``output`` / ``payload`` (server -> client):
      - ``pydantic ⊆ contract``     -> compatible (no error)
      - ``pydantic ⊈ contract``     -> ERROR  (server may produce a value
        the contract does not advertise; runtime break on the client)
      - ``contract ⊇ pydantic``     -> WARNING (contract promises values
        the server will never produce; dead code paths on the client)

    * ``input`` (client -> server):
      - ``contract ⊆ pydantic``     -> compatible (no error)
      - ``contract ⊈ pydantic``     -> ERROR  (contract advertises values
        Pydantic will reject with HTTP 422)
      - ``pydantic ⊇ contract``     -> compatible (server intentionally
        tolerates more; contract is an explicit API restriction)
    """
    if contract_set == pydantic_set:
        return None

    extra_in_pydantic = pydantic_set - contract_set
    extra_in_contract = contract_set - pydantic_set

    if block_kind in ("output", "payload"):
        if extra_in_pydantic:
            detail = (
                "Pydantic Literal has extra values the contract does not "
                "advertise (server may return values the client cannot "
                "decode): " + ", ".join(sorted(extra_in_pydantic))
            )
            return ("error", detail)
        if extra_in_contract:
            detail = (
                "Contract advertises values Pydantic will never return "
                "(dead code paths on the client): "
                + ", ".join(sorted(extra_in_contract))
            )
            return ("warning", detail)
        return None

    # input (or any other block kind): contract is the client-facing
    # surface; Pydantic defines what the server actually accepts.
    if extra_in_contract:
        detail = (
            "Contract advertises values Pydantic will reject at runtime "
            "(HTTP 422 for client): "
            + ", ".join(sorted(extra_in_contract))
        )
        return ("error", detail)
    # pydantic ⊇ contract on input is intentional narrowing, not a drift.
    return None


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
    # Dedup by (block_kind, dotted_path). We only emit one fix per unique
    # location even if ``_iter_enum_fields`` yields both the bare name and
    # the dotted path for the same enum spec.
    seen: set[tuple[str, str]] = set()
    for block_kind, block in _contract_schemas(contract):
        for field_name, enum_values in _iter_enum_fields(block):
            # Only consider dotted paths once; bare-name duplicates are skipped
            # to keep fix emission unique per logical location.
            key = (block_kind, field_name)
            if key in seen:
                continue
            seen.add(key)
            base_name = field_name.rsplit(".", 1)[-1]
            pydantic_values = literal_fields.get(base_name)
            if pydantic_values is None:
                continue
            contract_set = set(enum_values)
            verdict = _classify_drift(block_kind, contract_set, pydantic_values)
            if verdict is None:
                continue
            severity, detail = verdict
            message = (
                f"{block_kind} field {field_name!r} enum drift in "
                f"{contract_file}: {detail}"
            )
            if severity == "error":
                result.errors.append(message)
            else:
                result.warnings.append(message)

            # Emit a structural fix alongside the message. We only emit
            # fixes for drift types that have a deterministic, single-
            # action resolution on the JSON side:
            #   output/payload warning -> remove_extra (safe)
            #   output/payload error   -> expand_contract (opt-in)
            # Input errors are intentionally skipped because they have
            # two equally valid resolutions (narrow contract vs loosen
            # Pydantic) and require a human decision.
            extra_in_contract = contract_set - pydantic_values
            extra_in_pydantic = pydantic_values - contract_set
            if block_kind in ("output", "payload"):
                if severity == "warning" and extra_in_contract:
                    result.fixes.append(
                        ContractFix(
                            block_kind=block_kind,
                            field_path=field_name,
                            action="remove_extra",
                            values=sorted(extra_in_contract),
                            severity="warning",
                            rationale=(
                                "server never returns these values; "
                                "contract should not advertise them"
                            ),
                        )
                    )
                elif severity == "error" and extra_in_pydantic:
                    result.fixes.append(
                        ContractFix(
                            block_kind=block_kind,
                            field_path=field_name,
                            action="expand_contract",
                            values=sorted(extra_in_pydantic),
                            severity="error",
                            rationale=(
                                "server may return these values; "
                                "contract must advertise them"
                            ),
                        )
                    )

    if result.errors:
        result.ok = False
    return result


# ---------------------------------------------------------------------------
# Auto-fix: apply structural fixes to a contract JSON file
# ---------------------------------------------------------------------------


def _navigate_to_enum_spec(
    raw: dict, block_kind: str, field_path: str
) -> dict | None:
    """Walk *raw* contract dict to the dict holding the ``enum`` key for the
    given ``block_kind`` + ``field_path``. Returns ``None`` if not found.

    Handles both direct keys (top-level block) and JSON-Schema-style nested
    ``properties`` (objects).
    """
    block = raw.get(block_kind)
    if not isinstance(block, dict):
        return None
    current: Any = block
    for segment in field_path.split("."):
        if not isinstance(current, dict):
            return None
        # Prefer a direct key (top-level block case).
        if segment in current and isinstance(current[segment], dict):
            current = current[segment]
            continue
        # Fall back to JSON-Schema ``properties`` traversal.
        props = current.get("properties") if isinstance(current, dict) else None
        if isinstance(props, dict) and segment in props and isinstance(props[segment], dict):
            current = props[segment]
            continue
        return None
    if isinstance(current, dict) and isinstance(current.get("enum"), list):
        return current
    return None


@dataclass
class FixApplicationReport:
    applied: list[ContractFix] = field(default_factory=list)
    skipped: list[ContractFix] = field(default_factory=list)
    not_found: list[ContractFix] = field(default_factory=list)

    @property
    def any_applied(self) -> bool:
        return bool(self.applied)


def apply_fixes_to_contract(
    contract_path: Path,
    fixes: list[ContractFix],
    *,
    include_error_expansion: bool = False,
) -> FixApplicationReport:
    """Apply *fixes* in place to the JSON file at *contract_path*.

    Only safe fixes are applied by default:

    * ``remove_extra`` (warning-level, output/payload): always applied.

    Opt-in with ``include_error_expansion=True``:

    * ``expand_contract`` (error-level, output/payload): add Pydantic-known
      values to the contract enum.

    Fixes whose ``block_kind`` is not in ``{"output", "payload"}`` or whose
    ``action`` is neither ``remove_extra`` nor ``expand_contract`` are
    recorded in ``skipped`` without modifying the file.

    On success the file is rewritten with ``indent=2`` and ``ensure_ascii=False``
    so UTF-8 content (e.g. ``"—"`` for ws.channel) survives.
    """
    report = FixApplicationReport()
    if not fixes:
        return report

    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        report.skipped.extend(fixes)
        return report

    modified = False
    for fix in fixes:
        if fix.action not in ("remove_extra", "expand_contract"):
            report.skipped.append(fix)
            continue
        if fix.action == "expand_contract" and not include_error_expansion:
            report.skipped.append(fix)
            continue
        if fix.block_kind not in ("output", "payload"):
            # Input fixes require human decision; never auto-apply.
            report.skipped.append(fix)
            continue

        spec = _navigate_to_enum_spec(raw, fix.block_kind, fix.field_path)
        if spec is None:
            report.not_found.append(fix)
            continue

        current_enum = [v for v in spec["enum"] if isinstance(v, str)]
        if fix.action == "remove_extra":
            new_enum = [v for v in current_enum if v not in set(fix.values)]
        else:  # expand_contract
            existing = set(current_enum)
            new_enum = list(current_enum) + [v for v in fix.values if v not in existing]

        if new_enum == current_enum:
            # No-op; already in sync (e.g. fix was already applied).
            report.skipped.append(fix)
            continue

        spec["enum"] = new_enum
        modified = True
        report.applied.append(fix)

    if modified:
        # Preserve the canonical indent=2 ensure_ascii=False format used by
        # protogate.codegen.registry.write_registry and the rest of the
        # contract authoring toolchain.
        text = json.dumps(raw, indent=2, ensure_ascii=False) + "\n"
        contract_path.write_text(text, encoding="utf-8")

    return report


def cross_check_contracts(
    contracts: list[dict],
    layers_root: Path | None = None,
) -> list[tuple[dict, CrossCheckResult]]:
    """Run :func:`cross_check_contract` over every contract.

    Returns pairs ``(contract, result)`` in the same order as the input list.
    """
    return [(c, cross_check_contract(c, layers_root=layers_root)) for c in contracts]
