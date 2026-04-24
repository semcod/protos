from __future__ import annotations

from typing import Any, Callable


def _append_reason_counts_section(
    lines: list[str],
    heading: str,
    reason_counts: list[dict[str, Any]],
    *,
    limit: int | None = None,
) -> None:
    lines.extend([
        "",
        heading,
        "",
    ])
    items = reason_counts[:limit] if limit is not None else reason_counts
    for item in items:
        lines.append(f"- `{item['reason']}`: {item['count']}")
    if not reason_counts:
        lines.append("- `none`")


def _append_simple_list_section(lines: list[str], heading: str, items: list[str]) -> None:
    lines.extend([
        "",
        heading,
        "",
    ])
    for item in items:
        lines.append(f"- `{item}`")
    if not items:
        lines.append("- `none`")


def _append_artifacts_table(lines: list[str], artifacts: dict[str, str]) -> None:
    lines.extend([
        "",
        "## Artifacts",
        "",
        "| Name | Path |",
        "| --- | --- |",
    ])
    for name, path in sorted(artifacts.items()):
        lines.append(f"| {name} | `{path}` |")


def _format_detail_value(row: dict[str, Any], key: str, value_format: str) -> str:
    value = row.get(key)
    if value_format == "float2":
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return "0.00"
    if value is None or value == "":
        return "-"
    return str(value)


def _append_detail_section(
    lines: list[str],
    *,
    heading: str,
    empty_message: str,
    rows: list[dict[str, Any]],
    row_title: Callable[[dict[str, Any]], str],
    metadata_specs: list[tuple[str, str, str]],
    reasons_heading: str,
) -> None:
    lines.extend([
        "",
        heading,
        "",
    ])
    for row in rows:
        lines.append(row_title(row))
        lines.append("")
        for label, key, value_format in metadata_specs:
            value = _format_detail_value(row, key, value_format)
            lines.append(f"- {label}: `{value}`")
        lines.append(reasons_heading)
        for reason in row.get("reasons", []):
            lines.append(f"  - {reason}")
        lines.append("")
    if not rows:
        lines.append(empty_message)
        lines.append("")


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Migration Discovery Summary",
        "",
        f"Generated at: {summary['generated_at']}",
        "",
        f"- Repository root: `{summary['repo_root']}`",
        f"- Languages: `{', '.join(row['name'] for row in summary['profile']['languages']) or '-'}`",
        f"- Frameworks: `{', '.join(summary['profile']['frameworks']) or '-'}`",
        f"- Architecture hints: `{', '.join(summary['profile']['architecture_hints']) or '-'}`",
        "",
        "## Counts",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in summary["counts"].items():
        lines.append(f"| {key} | {value} |")
    _append_simple_list_section(lines, "## Top delegable candidates", summary.get("top_delegable_candidates", []))
    _append_simple_list_section(lines, "## Top raw migration candidates", summary["top_candidates"])
    _append_simple_list_section(lines, "## Top service candidates", summary["top_service_candidates"])
    _append_reason_counts_section(
        lines,
        "## Service-boundary decision reasons",
        summary.get("service_boundary_decision_reasons", []),
        limit=10,
    )
    _append_reason_counts_section(
        lines,
        "## Excluded candidate reasons",
        summary.get("excluded_candidate_reasons", []),
        limit=10,
    )
    _append_reason_counts_section(
        lines,
        "## Delegation decision reasons",
        summary.get("delegation_decision_reasons", []),
        limit=10,
    )
    _append_simple_list_section(lines, "## Top CQRS pattern candidates", summary["top_cqrs_pattern_candidates"])
    _append_simple_list_section(lines, "## Top swop contexts", summary.get("top_swop_contexts", []))
    _append_artifacts_table(lines, summary["artifacts"])
    return "\n".join(lines) + "\n"


def render_excluded_candidates_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Excluded Delegation Candidates",
        "",
        f"Total excluded candidates: {payload['count']}",
    ]
    _append_reason_counts_section(lines, "## Exclusion reasons", payload.get("reason_counts", []))
    _append_detail_section(
        lines,
        heading="## Excluded candidates",
        empty_message="No excluded candidates.",
        rows=payload.get("rows", []),
        row_title=lambda row: f"### Excluded: {row['module'] or 'unknown'}",
        metadata_specs=[
            ("Path", "path", "text"),
            ("Kind", "kind", "text"),
            ("Score", "score", "float2"),
            ("Phase", "phase", "text"),
        ],
        reasons_heading="- Reasons:",
    )
    return "\n".join(lines)


def render_delegation_decisions_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Delegation Decision Rationale",
        "",
        f"Total selected delegation candidates: {payload['count']}",
    ]
    _append_reason_counts_section(lines, "## Repeated decision signals", payload.get("reason_counts", []), limit=20)
    _append_detail_section(
        lines,
        heading="## Selected candidates",
        empty_message="No selected delegation candidates.",
        rows=payload.get("rows", []),
        row_title=lambda row: f"### Selected: {row['module']}",
        metadata_specs=[
            ("Score", "score", "float2"),
            ("Phase", "phase", "text"),
            ("Effort", "effort", "text"),
            ("CQRS pattern", "cqrs_pattern", "text"),
            ("Shared types package", "shared_types_package", "text"),
        ],
        reasons_heading="- Why selected:",
    )
    return "\n".join(lines)


def render_service_boundary_decisions_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Service Boundary Decision Rationale",
        "",
        f"Total recommended service candidates: {payload['count']}",
    ]
    _append_reason_counts_section(lines, "## Repeated decision signals", payload.get("reason_counts", []), limit=20)
    _append_detail_section(
        lines,
        heading="## Recommended candidates",
        empty_message="No recommended service candidates.",
        rows=payload.get("rows", []),
        row_title=lambda row: f"### Recommended: {row['module']}",
        metadata_specs=[
            ("Service slug", "service_slug", "text"),
            ("Priority", "priority", "text"),
            ("Delivery mode", "delivery_mode", "text"),
            ("Iframe score", "iframe_score", "text"),
            ("Pages", "page_count", "text"),
        ],
        reasons_heading="- Why selected:",
    )
    return "\n".join(lines)
