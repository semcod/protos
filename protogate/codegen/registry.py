"""Contract registry generator.

Loads JSON contract files matching ``*.command.json``, ``*.query.json`` and
``*.event.json`` from a directory and produces ``registry.json`` plus
``REGISTRY.md``.

Ported from ``c2004/scripts/generate-registry.py`` (ADR-010 Sprint B). The
logic is identical; only paths become arguments.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CONTRACT_PATTERNS = ("*.command.json", "*.query.json", "*.event.json")


@dataclass
class RegistryResult:
    contracts: list[dict]
    errors: list[tuple[str, list[str]]]
    registry: dict
    markdown: str

    @property
    def ok(self) -> bool:
        return not self.errors


def load_contracts(contracts_dir: Path) -> list[dict]:
    """Load every contract JSON file under *contracts_dir*.

    Each returned dict has an extra ``_file`` key with the basename.
    """
    contracts: list[dict] = []
    for pattern in CONTRACT_PATTERNS:
        for path in sorted(contracts_dir.glob(pattern)):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path.name}: {exc}") from exc
            data["_file"] = path.name
            contracts.append(data)
    return contracts


def _check_layer_paths(contract: dict, root: Path, errors: list[str]) -> None:
    for key, value in contract.get("layers", {}).items():
        raw = value.split("::")[0] if isinstance(value, str) else None
        if raw is None:
            continue
        resolved = root / raw
        if not resolved.exists():
            errors.append(f"layers.{key} path not found: {raw}")


def validate_contract(contract: dict, layers_root: Path) -> list[str]:
    """Return a list of validation errors for *contract* (empty if valid)."""
    errors: list[str] = []
    kind = contract.get("kind")

    if "command" in contract:
        required = ["command", "kind", "version", "input", "output", "transport", "layers"]
        for key in required:
            if key not in contract:
                errors.append(f"Missing required field: '{key}'")
        if kind != "CQRS_COMMAND":
            errors.append(f"'kind' for command must be CQRS_COMMAND, got: {kind}")
        _check_layer_paths(contract, layers_root, errors)
    elif "query" in contract:
        required = ["query", "kind", "version", "input", "output", "transport", "layers"]
        for key in required:
            if key not in contract:
                errors.append(f"Missing required field: '{key}'")
        if kind != "CQRS_QUERY":
            errors.append(f"'kind' for query must be CQRS_QUERY, got: {kind}")
        _check_layer_paths(contract, layers_root, errors)
    elif "event" in contract:
        required = ["event", "kind", "version", "payload", "producers"]
        for key in required:
            if key not in contract:
                errors.append(f"Missing required field: '{key}'")
        if kind not in ("DOMAIN_EVENT", "INTEGRATION_EVENT"):
            errors.append(
                f"'kind' for event must be DOMAIN_EVENT or INTEGRATION_EVENT, got: {kind}"
            )
    else:
        errors.append(
            "Missing discriminator field: one of 'command', 'query', 'event' is required"
        )

    return errors


def generate_registry_json(contracts: Iterable[dict]) -> dict:
    contracts = list(contracts)
    registry: dict[str, Any] = {
        "_generated": datetime.now(timezone.utc).isoformat(),
        "_total": len(contracts),
        "commands": {},
        "queries": {},
        "events": {},
    }
    for c in contracts:
        if "command" in c:
            name = c["command"]
            registry["commands"][name] = {
                "file": c["_file"],
                "kind": c.get("kind"),
                "version": c.get("version"),
                "module": c.get("module", "—"),
                "description": c.get("description", ""),
                "transport": {
                    "http": c.get("transport", {}).get("http", {}).get("endpoint", "—"),
                    "ws": c.get("transport", {}).get("ws", {}).get("channel", "—"),
                },
                "layers": c.get("layers", {}),
                "events": c.get("events", {}),
            }
            continue

        if "query" in c:
            name = c["query"]
            registry["queries"][name] = {
                "file": c["_file"],
                "kind": c.get("kind"),
                "version": c.get("version"),
                "module": c.get("module", "—"),
                "description": c.get("description", ""),
                "transport": {
                    "http": c.get("transport", {}).get("http", {}).get("endpoint", "—"),
                    "ws": c.get("transport", {}).get("ws", {}).get("channel", "—"),
                },
                "layers": c.get("layers", {}),
            }
            continue

        name = c["event"]
        registry["events"][name] = {
            "file": c["_file"],
            "kind": c.get("kind"),
            "version": c.get("version"),
            "module": c.get("module", "—"),
            "description": c.get("description", ""),
            "producers": c.get("producers", {}),
            "consumers": c.get("consumers", {}),
            "transport": c.get("transport", {}),
        }
    return registry


def generate_registry_markdown(contracts: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    command_contracts = [c for c in contracts if "command" in c]
    query_contracts = [c for c in contracts if "query" in c]
    event_contracts = [c for c in contracts if "event" in c]

    lines: list[str] = [
        "# Contract Registry",
        "",
        f"> Auto-generated by `protogate codegen registry` — {now}  ",
        (
            f"> Total contracts: **{len(contracts)}** "
            f"(commands: {len(command_contracts)}, "
            f"queries: {len(query_contracts)}, "
            f"events: {len(event_contracts)})  "
        ),
        "> Source: `contracts/*.{command,query,event}.json`",
        "",
        "---",
        "",
        "## Command Map",
        "",
        "| Command | Module | HTTP Endpoint | WS Channel | Python Layer | Events |",
        "|---------|--------|--------------|------------|-------------|--------|",
    ]

    for c in command_contracts:
        name = c["command"]
        module = c.get("module", "—")
        http = c.get("transport", {}).get("http", {}).get("endpoint", "—")
        ws = c.get("transport", {}).get("ws", {}).get("channel", "—")
        python_layer = c.get("layers", {}).get("python", "—")
        events = ", ".join(c.get("events", {}).values()) or "—"
        lines.append(
            f"| `{name}` | `{module}` | `{http}` | `{ws}` | `{python_layer}` | {events} |"
        )

    lines += [
        "",
        "## Query Map",
        "",
        "| Query | Module | HTTP Endpoint | WS Channel | Python Layer |",
        "|-------|--------|--------------|------------|-------------|",
    ]

    for c in query_contracts:
        name = c["query"]
        module = c.get("module", "—")
        http = c.get("transport", {}).get("http", {}).get("endpoint", "—")
        ws = c.get("transport", {}).get("ws", {}).get("channel", "—")
        python_layer = c.get("layers", {}).get("python", "—")
        lines.append(
            f"| `{name}` | `{module}` | `{http}` | `{ws}` | `{python_layer}` |"
        )

    lines += [
        "",
        "## Event Map",
        "",
        "| Event | Kind | Module | Producer (python) | Consumers |",
        "|------|------|--------|-------------------|----------|",
    ]

    for c in event_contracts:
        event_name = c["event"]
        kind = c.get("kind", "—")
        module = c.get("module", "—")
        producer = c.get("producers", {}).get("python", "—")
        raw_consumers = c.get("consumers", [])
        if isinstance(raw_consumers, list):
            consumers = ", ".join(raw_consumers) or "—"
        else:
            consumers = ", ".join(f"{k}:{v}" for k, v in raw_consumers.items()) or "—"
        lines.append(
            f"| `{event_name}` | `{kind}` | `{module}` | `{producer}` | {consumers} |"
        )

    lines += ["", "---", "", "## Command Details", ""]

    for c in command_contracts:
        name = c["command"]
        lines += [
            f"### `{name}`",
            "",
            (
                f"**Kind**: `{c.get('kind')}` | **Module**: `{c.get('module', '—')}` "
                f"| **Version**: `{c.get('version', '?')}`  "
            ),
            f"**Description**: {c.get('description', '—')}",
            "",
            "**Input:**",
            "",
            "| Field | Type | Required | Description |",
            "|-------|------|----------|-------------|",
        ]
        for field_name, meta in c.get("input", {}).items():
            required = "✅" if meta.get("required") else "—"
            desc = meta.get("description", meta.get("enum", ""))
            if isinstance(desc, list):
                desc = f"enum: `{'`, `'.join(desc)}`"
            lines.append(
                f"| `{field_name}` | `{meta.get('type', '?')}` | {required} | {desc} |"
            )

        lines += [
            "",
            "**Output:**",
            "",
            "| Field | Type |",
            "|-------|------|",
        ]
        for field_name, meta in c.get("output", {}).items():
            lines.append(f"| `{field_name}` | `{meta.get('type', '?')}` |")

        if "storage" in c:
            s = c["storage"]
            lines += [
                "",
                f"**Storage**: `{s.get('database')}` → table `{s.get('table')}`",
            ]

        if "layers" in c:
            layers = c["layers"]
            lines += ["", "**Layers:**", ""]
            for layer, path in layers.items():
                lines.append(f"- **{layer}**: `{path}`")

        if "events" in c and c["events"]:
            lines += ["", "**Events:**"]
            for event_type, event_name in c["events"].items():
                lines.append(f"- `{event_type}`: `{event_name}`")

        lines += ["", "---", ""]

    lines += ["", "## Query Details", ""]

    for c in query_contracts:
        name = c["query"]
        lines += [
            f"### `{name}`",
            "",
            (
                f"**Kind**: `{c.get('kind')}` | **Module**: `{c.get('module', '—')}` "
                f"| **Version**: `{c.get('version', '?')}`  "
            ),
            f"**Description**: {c.get('description', '—')}",
            "",
            "**Input:**",
            "",
            "| Field | Type | Required | Description |",
            "|-------|------|----------|-------------|",
        ]
        for field_name, meta in c.get("input", {}).items():
            required = "✅" if meta.get("required") else "—"
            desc = meta.get("description", "")
            lines.append(
                f"| `{field_name}` | `{meta.get('type', '?')}` | {required} | {desc} |"
            )
        lines += ["", "---", ""]

    lines += ["", "## Event Details", ""]

    for c in event_contracts:
        name = c["event"]
        lines += [
            f"### `{name}`",
            "",
            (
                f"**Kind**: `{c.get('kind')}` | **Module**: `{c.get('module', '—')}` "
                f"| **Version**: `{c.get('version', '?')}`  "
            ),
            f"**Description**: {c.get('description', '—')}",
            "",
            "**Payload:**",
            "",
            "| Field | Type | Description |",
            "|-------|------|-------------|",
        ]
        for field_name, meta in c.get("payload", {}).items():
            desc = meta.get("description", "")
            lines.append(f"| `{field_name}` | `{meta.get('type', '?')}` | {desc} |")

        producers = c.get("producers", {})
        if producers:
            lines += ["", "**Producers:**"]
            for producer_type, producer_ref in producers.items():
                lines.append(f"- `{producer_type}`: `{producer_ref}`")

        raw_consumers = c.get("consumers", [])
        if raw_consumers:
            lines += ["", "**Consumers:**"]
            if isinstance(raw_consumers, list):
                for item in raw_consumers:
                    lines.append(f"- {item}")
            else:
                for consumer_type, consumer_ref in raw_consumers.items():
                    lines.append(f"- `{consumer_type}`: `{consumer_ref}`")

        lines += ["", "---", ""]

    return "\n".join(lines)


def build(contracts_dir: Path, layers_root: Path | None = None) -> RegistryResult:
    """End-to-end build: load + validate + generate JSON + Markdown."""
    if layers_root is None:
        layers_root = contracts_dir.parent
    contracts = load_contracts(contracts_dir)
    errors: list[tuple[str, list[str]]] = []
    for c in contracts:
        c_errors = validate_contract(c, layers_root)
        if c_errors:
            errors.append((c["_file"], c_errors))
    registry = generate_registry_json(contracts)
    markdown = generate_registry_markdown(contracts)
    return RegistryResult(
        contracts=contracts, errors=errors, registry=registry, markdown=markdown
    )


def run_cli(
    contracts_dir: Path,
    output_dir: Path | None = None,
    layers_root: Path | None = None,
    check_only: bool = False,
    cross_check_pydantic: bool = False,
    fix_safe: bool = False,
    auto_expand_output: bool = False,
    verbose: bool = True,
) -> int:
    """CLI entry point used by ``protogate codegen registry``.

    Returns 0 on success, 1 on validation failure.

    When *cross_check_pydantic* is ``True`` every contract's enum values are
    additionally cross-checked against ``Literal[...]`` annotations found in
    the Pydantic module referenced by ``layers.python``. See
    :mod:`protogate.codegen.pydantic_cross_check`.

    When *fix_safe* is ``True`` the cross-check additionally auto-applies
    warning-level drift fixes to the contract JSON files on disk (remove
    enum values the Pydantic model does not emit). Requires
    *cross_check_pydantic=True*.

    When *auto_expand_output* is ``True`` (opt-in, requires *fix_safe*), the
    cross-check **also** expands output/payload contract enums to cover
    values the Pydantic Literal emits but the contract did not advertise.
    This resolves the ADR-012 Wave 2 regression class automatically at the
    cost of potentially blessing a server-side bug. Never applied to input
    blocks.
    """
    if output_dir is None:
        output_dir = contracts_dir

    if verbose:
        print("🔍 Loading contracts...")
    try:
        result = build(contracts_dir, layers_root=layers_root)
    except ValueError as exc:
        print(f"  ❌ {exc}", file=sys.stderr)
        return 1

    if not result.contracts:
        if verbose:
            print("  ⚠️  No contracts found in contracts/*.{command,query,event}.json")
        return 0

    if verbose:
        print(f"  Found {len(result.contracts)} contracts")

    if result.errors:
        for file_name, errs in result.errors:
            print(f"  ❌ {file_name}: {'; '.join(errs)}", file=sys.stderr)
        print("\n❌ Validation failed. Fix errors above before generating.", file=sys.stderr)
        return 1

    if verbose:
        for c in result.contracts:
            name = c.get("command") or c.get("query") or c.get("event") or c["_file"]
            print(f"  ✅ {name}")

    if cross_check_pydantic:
        from protogate.codegen.pydantic_cross_check import (
            apply_fixes_to_contract,
            cross_check_contracts,
        )
        cross_root = layers_root if layers_root is not None else contracts_dir.parent

        if fix_safe:
            # First pass: identify drift and proposed fixes.
            first_pairs = cross_check_contracts(result.contracts, layers_root=cross_root)
            any_applied = False
            for raw_contract, cross_result in first_pairs:
                if not cross_result.fixes:
                    continue
                file_name = raw_contract.get("_file")
                if not file_name:
                    continue
                fixes_to_apply = cross_result.auto_fixable_fixes(
                    include_error_expansion=auto_expand_output,
                )
                if not fixes_to_apply:
                    continue
                report = apply_fixes_to_contract(
                    contracts_dir / file_name,
                    fixes_to_apply,
                    include_error_expansion=auto_expand_output,
                )
                if report.applied and verbose:
                    print(f"\n✏️  Auto-fixed {file_name}:")
                    for fix in report.applied:
                        print(f"  ✏️  {fix.describe()}")
                    any_applied = any_applied or True
                if report.not_found and verbose:
                    for fix in report.not_found:
                        print(
                            f"  ⚠️  could not locate enum to fix in "
                            f"{file_name}: {fix.field_path}"
                        )
            if any_applied:
                # Reload contracts so the subsequent second pass sees the edits.
                result = build(contracts_dir, layers_root=layers_root)

        pairs = cross_check_contracts(result.contracts, layers_root=cross_root)
        failures = [(c, r) for c, r in pairs if not r.ok]
        warnings_pairs = [(c, r) for c, r in pairs if r.warnings]
        if warnings_pairs and verbose:
            print("\n⚠️  Cross-check warnings (non-blocking):")
            for _contract, cross_result in warnings_pairs:
                for warn in cross_result.warnings:
                    print(f"  ⚠️  {warn}")
        if failures:
            print(
                "\n❌ Cross-check failed (contract enum vs Pydantic Literal):",
                file=sys.stderr,
            )
            for _contract, cross_result in failures:
                for err in cross_result.errors:
                    print(f"  ❌ {err}", file=sys.stderr)
            if not fix_safe:
                print(
                    "\n💡 Tip: rerun with --fix-safe (auto-fixes warnings) or "
                    "--fix-safe --auto-expand-output (also auto-expands output "
                    "contract enums to match Pydantic).",
                    file=sys.stderr,
                )
            return 1
        if verbose:
            print(
                "\n🔗 Cross-check passed "
                "(contract enums compatible with Pydantic Literal[...] annotations)"
            )

    if check_only:
        if verbose:
            print("\n✅ All contracts valid (--check mode, no files written)")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    registry_json_path = output_dir / "registry.json"
    registry_md_path = output_dir / "REGISTRY.md"
    registry_json_path.write_text(
        json.dumps(result.registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    registry_md_path.write_text(result.markdown, encoding="utf-8")

    if verbose:
        print(f"\n✅ Written: {registry_json_path}")
        print(f"✅ Written: {registry_md_path}")
        command_count = sum(1 for c in result.contracts if "command" in c)
        query_count = sum(1 for c in result.contracts if "query" in c)
        event_count = sum(1 for c in result.contracts if "event" in c)
        modules = {c.get("module", "") for c in result.contracts}
        print(
            f"\n📋 Registry: {len(result.contracts)} contracts "
            f"(commands={command_count}, queries={query_count}, events={event_count}) "
            f"across {len(modules)} modules"
        )
    return 0
