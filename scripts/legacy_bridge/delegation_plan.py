from __future__ import annotations

from typing import Any


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_shared_types_package(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "@semcod/contracts-types:custom-per-module"
    if ":" not in raw and raw.startswith("@semcod/contracts-types"):
        return f"{raw}:custom-per-module"
    return raw


def _normalize_reasons(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(reason) for reason in value if str(reason).strip()]


def to_slice_name(module: str) -> str:
    return module.strip().replace("_", "-").replace(" ", "-").lower()


def build_steps(module: str) -> list[str]:
    slice_name = to_slice_name(module)
    return [
        f"Create contract under contracts/{slice_name}/v1",
        f"Implement gateway handler for {slice_name} commands and queries",
        f"Add read model storage and replay/bootstrap adapter for {slice_name}",
        f"Create delegated UI entrypoint for {slice_name}",
        f"Expose delegated UI through gateway static or dedicated frontend service",
        f"Switch c2004 route to iframe host for {slice_name}",
        f"Run data bootstrap and smoke checks",
        f"Archive legacy {slice_name} implementation in c2004",
    ]


def build_slice_blueprint(module: str) -> dict[str, Any]:
    slice_name = to_slice_name(module)
    return {
        "slice_name": slice_name,
        "contract_dir": f"contracts/{slice_name}/v1",
        "gateway": {
            "commands": f"/commands/{slice_name}/*",
            "queries": f"/queries/{slice_name}/*",
            "health": f"/health/modules/{slice_name}",
        },
        "frontend": {
            "strategy": "gateway-static-or-dedicated-frontend-service",
            "host_mode": "iframe",
        },
        "migration": {
            "legacy_host": "shell-auth-session-iframe-routing-only",
            "checklist": build_steps(module),
        },
    }


def build_output_row(row: dict[str, Any], cluster_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    module = str(row.get("module", "unknown"))
    cluster_meta = cluster_meta or {}
    cqrs_pattern = str(cluster_meta.get("pattern", "n/a"))
    shared_types_package = _normalize_shared_types_package(cluster_meta.get("extraction_target"))
    score = _to_float(row.get("score", 0.0), 0.0)
    phase = str(row.get("phase", "n/a"))
    effort = str(row.get("effort", "n/a"))
    command_count = int(cluster_meta.get("command_count", 0) or 0)
    event_count = int(cluster_meta.get("event_count", 0) or 0)
    cluster_members = cluster_meta.get("cluster_members", [module])
    if not isinstance(cluster_members, list) or not cluster_members:
        cluster_members = [module]
    return {
        **row,
        "module": module,
        "slice": build_slice_blueprint(module),
        "cqrs": {
            "pattern": cqrs_pattern,
            "shared_types_package": shared_types_package,
            "command_count": command_count,
            "event_count": event_count,
            "cluster_size": len(cluster_members),
        },
        "readiness": {
            "score": score,
            "phase": phase,
            "effort": effort,
            "reasons": _normalize_reasons(row.get("reasons", [])),
        },
    }


def render_markdown(rows: list[dict[str, Any]], limit: int, clusters: dict[str, dict[str, Any]] | None = None) -> str:
    clusters = clusters or {}
    selected = [build_output_row(row, clusters.get(str(row.get("module", "")), {})) for row in rows[:limit]]
    lines = [
        "# Delegation Plan (Generated)",
        "",
        "This file is generated from c2004 migration candidate report.",
        "",
        "## Top modules to delegate first",
        "",
    ]

    for row in selected:
        lines.append(f"- {row['module']}: score={row['readiness']['score']:.2f}, phase={row['readiness']['phase']}, effort={row['readiness']['effort']}, pattern={row['cqrs']['pattern']}, cmds={row['cqrs']['command_count']}, evts={row['cqrs']['event_count']}, shared={row['cqrs']['shared_types_package']}")

    lines.append("")
    lines.append("## Slice blueprints")
    lines.append("")

    for row in selected:
        blueprint = row["slice"]
        lines.append(f"### Slice blueprint: {row['module']}")
        lines.append("")
        lines.append(f"- Slice: `{blueprint['slice_name']}`")
        lines.append(f"- Contract dir: `{blueprint['contract_dir']}`")
        lines.append(f"- Commands: `{blueprint['gateway']['commands']}`")
        lines.append(f"- Queries: `{blueprint['gateway']['queries']}`")
        lines.append(f"- Health: `{blueprint['gateway']['health']}`")
        lines.append(f"- Frontend strategy: `{blueprint['frontend']['strategy']}`")
        lines.append(f"- Host mode: `{blueprint['frontend']['host_mode']}`")
        lines.append(f"- CQRS pattern: `{row['cqrs']['pattern']}`")
        lines.append(f"- CQRS command tokens: `{row['cqrs']['command_count']}`")
        lines.append(f"- CQRS event tokens: `{row['cqrs']['event_count']}`")
        lines.append(f"- CQRS cluster size: `{row['cqrs']['cluster_size']}`")
        lines.append(f"- Shared types package: `{row['cqrs']['shared_types_package']}`")
        lines.append("- Readiness reasons:")
        for reason in row["readiness"]["reasons"]:
            lines.append(f"  - {reason}")
        lines.append("")

    lines.append("## Per-module execution checklist")
    lines.append("")

    for row in selected:
        lines.append(f"### Checklist: {row['module']}")
        lines.append("")
        for idx, step in enumerate(row["slice"]["migration"]["checklist"], start=1):
            lines.append(f"{idx}. {step}")
        lines.append("")

    return "\n".join(lines)
