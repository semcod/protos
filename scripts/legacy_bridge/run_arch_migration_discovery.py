from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = CURRENT_DIR.parent
REPO_ROOT = SCRIPTS_DIR.parent

for candidate in (SCRIPTS_DIR, REPO_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

try:
    from detect_migration_candidates import analyze_repository
except ModuleNotFoundError:
    from scripts.detect_migration_candidates import analyze_repository

try:
    from legacy_bridge.candidate_selection import get_candidate_exclusion_reasons, is_delegable_candidate, parse_score
    from legacy_bridge.analyze_service_boundaries import analyze as analyze_service_boundaries
    from legacy_bridge.analyze_service_boundaries import build_markdown as build_service_boundaries_markdown
    from legacy_bridge.analyze_service_boundaries import load_config as load_service_boundary_config
    from legacy_bridge.detect_cqrs_pattern_clusters import analyze_repository as analyze_cqrs_pattern_clusters
    from legacy_bridge.detect_cqrs_pattern_clusters import render_markdown as render_cqrs_pattern_clusters_markdown
    from legacy_bridge.delegation_plan import build_output_row, render_markdown as render_delegation_markdown
    from legacy_bridge.generate_migration_wave_plan import build_waves, render_markdown as render_wave_plan_markdown
except ModuleNotFoundError:
    from candidate_selection import get_candidate_exclusion_reasons, is_delegable_candidate, parse_score
    from analyze_service_boundaries import analyze as analyze_service_boundaries
    from analyze_service_boundaries import build_markdown as build_service_boundaries_markdown
    from analyze_service_boundaries import load_config as load_service_boundary_config
    from detect_cqrs_pattern_clusters import analyze_repository as analyze_cqrs_pattern_clusters
    from detect_cqrs_pattern_clusters import render_markdown as render_cqrs_pattern_clusters_markdown
    from delegation_plan import build_output_row, render_markdown as render_delegation_markdown
    from generate_migration_wave_plan import build_waves, render_markdown as render_wave_plan_markdown

LANGUAGE_SUFFIXES = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".java": "java",
    ".kt": "kotlin",
    ".cs": "csharp",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".proto": "protobuf",
}
MANIFEST_HINTS = {
    "package.json": "node-package",
    "requirements.txt": "python-requirements",
    "pyproject.toml": "python-project",
    "go.mod": "go-module",
    "pom.xml": "maven-project",
    "build.gradle": "gradle-project",
    "build.gradle.kts": "gradle-project",
    "Cargo.toml": "rust-project",
}
FRAMEWORK_HINTS = {
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "react": "react",
    "vue": "vue",
    "angular": "angular",
    "next": "nextjs",
    "vite": "vite",
    "express": "express",
    "nest": "nestjs",
    "spring-boot": "spring-boot",
    "microsoft.aspnetcore": "aspnet-core",
    "gin-gonic": "gin",
    "fiber": "fiber",
}
DEFAULT_IGNORE_DIRS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "reports",
    "venv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run generic migration discovery pipeline for a legacy repository")
    parser.add_argument("--repo-root", required=True, help="path to the repository to analyze")
    parser.add_argument("--config", help="optional JSON config path for service-boundary analysis")
    parser.add_argument("--output-dir", default="reports/migration-discovery", help="directory for generated artifacts, relative to repo root if not absolute")
    parser.add_argument("--top-services", type=int, help="number of top service candidates to recommend in service-boundary analysis")
    parser.add_argument("--delegation-limit", type=int, default=8, help="number of top module candidates to include in generated delegation plan")
    parser.add_argument("--stdout", action="store_true", help="print summary JSON to stdout")
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def resolve_output_dir(repo_root: Path, raw_output_dir: str) -> Path:
    output_dir = Path(raw_output_dir)
    return output_dir if output_dir.is_absolute() else repo_root / output_dir


def profile_repository(repo_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    ignore_dirs = set(config.get("ignore_dirs", [])) | DEFAULT_IGNORE_DIRS
    language_counts: Counter[str] = Counter()
    frameworks: set[str] = set()
    manifests: list[dict[str, str]] = []

    for path in repo_root.rglob("*"):
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            continue
        if any(part in ignore_dirs for part in rel.parts):
            continue
        if path.is_file():
            language = LANGUAGE_SUFFIXES.get(path.suffix)
            if language:
                language_counts[language] += 1
            if path.name in MANIFEST_HINTS:
                manifests.append({"path": rel.as_posix(), "kind": MANIFEST_HINTS[path.name]})
                content = read_text(path).lower()
                for hint, framework in FRAMEWORK_HINTS.items():
                    if hint in content:
                        frameworks.add(framework)

    frontend_roots = [root for root in config.get("frontend", {}).get("roots", []) if (repo_root / root).exists()]
    backend_roots = [root for root in config.get("backend", {}).get("route_roots", []) if (repo_root / root).exists()]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "languages": [{"name": name, "files": count} for name, count in language_counts.most_common()],
        "frameworks": sorted(frameworks),
        "manifests": sorted(manifests, key=lambda item: item["path"]),
        "frontend_roots": frontend_roots,
        "backend_route_roots": backend_roots,
        "detected_architecture_hints": sorted(
            {
                hint
                for hint, present in {
                    "frontend-backend-repo": bool(frontend_roots and backend_roots),
                    "modular-monolith": (repo_root / "modules").exists(),
                    "service-oriented": (repo_root / "services").exists(),
                    "monolith-root-backend": (repo_root / "backend").exists(),
                }.items()
                if present
            }
        ),
    }


def render_repository_profile_markdown(profile: dict[str, Any]) -> str:
    lines = [
        "# Repository Profile",
        "",
        f"Generated at: {profile['generated_at']}",
        "",
        f"- Repository root: `{profile['repo_root']}`",
        f"- Frontend roots: `{', '.join(profile['frontend_roots']) or '-'}`",
        f"- Backend route roots: `{', '.join(profile['backend_route_roots']) or '-'}`",
        f"- Architecture hints: `{', '.join(profile['detected_architecture_hints']) or '-'}`",
        "",
        "## Languages",
        "",
        "| Language | Files |",
        "| --- | ---: |",
    ]
    for row in profile["languages"]:
        lines.append(f"| {row['name']} | {row['files']} |")
    lines.extend([
        "",
        "## Framework hints",
        "",
    ])
    if profile["frameworks"]:
        for item in profile["frameworks"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `none-detected`")
    lines.extend([
        "",
        "## Manifests",
        "",
        "| Path | Kind |",
        "| --- | --- |",
    ])
    for row in profile["manifests"]:
        lines.append(f"| `{row['path']}` | `{row['kind']}` |")
    if not profile["manifests"]:
        lines.append("| `-` | `-` |")
    return "\n".join(lines) + "\n"


def render_module_candidates_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Migration Candidates",
        "",
        "| Module | Score | Phase | Effort | Kind | Service target |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['module']} | {float(row['score']):.2f} | {row['phase']} | {row['effort']} | {row['kind']} | {row['extraction_target']} |"
        )
    return "\n".join(lines) + "\n"


def _parse_score(row: dict[str, Any]) -> float:
    return parse_score(row)


def build_excluded_candidates_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    excluded_rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()

    for row in rows:
        reasons = get_candidate_exclusion_reasons(row)
        if not reasons:
            continue
        for reason in reasons:
            reason_counts[reason] += 1
        excluded_rows.append(
            {
                "module": str(row.get("module", "")),
                "path": str(row.get("path", "")),
                "kind": str(row.get("kind", "")),
                "score": _parse_score(row),
                "phase": str(row.get("phase", "n/a")),
                "reasons": reasons,
            }
        )

    excluded_rows.sort(key=lambda item: (-float(item.get("score", 0.0)), item.get("module", "")))
    return {
        "count": len(excluded_rows),
        "reason_counts": [{"reason": reason, "count": count} for reason, count in reason_counts.most_common()],
        "rows": excluded_rows,
    }


def build_service_boundary_decision_report(payload: dict[str, Any]) -> dict[str, Any]:
    selected_rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()

    for row in payload.get("recommended_service_candidates", []):
        if not isinstance(row, dict):
            continue

        module = str(row.get("module", ""))
        service_slug = str(row.get("service_slug", "n/a"))
        page_count = int(row.get("page_count", 0) or 0)
        iframe_score = int(row.get("iframe_score", 0) or 0)
        priority = int(row.get("extraction_priority", 0) or 0)
        delivery_mode = str(row.get("delivery_mode", "n/a"))
        backend_groups = row.get("backend_route_groups", []) if isinstance(row.get("backend_route_groups"), list) else []
        cross_targets = row.get("cross_module_targets", []) if isinstance(row.get("cross_module_targets"), list) else []
        companion_modules = row.get("companion_modules", []) if isinstance(row.get("companion_modules"), list) else []
        shared_deps = row.get("shared_dependency_files", []) if isinstance(row.get("shared_dependency_files"), list) else []

        reasons = [
            f"selected as service-boundary candidate with priority {priority}",
            f"delivery mode: {delivery_mode}",
            f"service grouping target: {service_slug}",
        ]
        if page_count > 0:
            reasons.append(f"page coverage: {page_count}")
        if backend_groups:
            reasons.append(f"backend groups covered: {len(backend_groups)}")
        if cross_targets:
            reasons.append(f"cross-module targets: {len(cross_targets)}")
        if companion_modules:
            reasons.append(f"companion modules: {len(companion_modules)}")
        if shared_deps:
            reasons.append(f"shared dependency files: {len(shared_deps)}")
        if iframe_score >= 60:
            reasons.append(f"strong iframe readiness: {iframe_score}")
        elif iframe_score > 0:
            reasons.append(f"iframe readiness: {iframe_score}")
        else:
            reasons.append("iframe-free extraction path")

        for backend_group in backend_groups[:4]:
            reasons.append(f"backend scope: {backend_group}")
        for target in cross_targets[:4]:
            reasons.append(f"coordination target: {target}")

        for reason in reasons:
            reason_counts[reason] += 1

        selected_rows.append(
            {
                "module": module,
                "service_slug": service_slug,
                "priority": priority,
                "delivery_mode": delivery_mode,
                "iframe_score": iframe_score,
                "page_count": page_count,
                "reasons": reasons,
            }
        )

    selected_rows.sort(key=lambda item: (-item["priority"], item["module"]))
    return {
        "count": len(selected_rows),
        "reason_counts": [{"reason": reason, "count": count} for reason, count in reason_counts.most_common()],
        "rows": selected_rows,
    }


def build_delegation_decision_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()

    for row in rows:
        module = str(row.get("module", ""))
        cqrs = row.get("cqrs", {}) if isinstance(row.get("cqrs"), dict) else {}
        readiness = row.get("readiness", {}) if isinstance(row.get("readiness"), dict) else {}
        reasons: list[str] = []

        phase = str(readiness.get("phase", "n/a"))
        effort = str(readiness.get("effort", "n/a"))
        score = _parse_score(readiness if isinstance(readiness, dict) else row)
        service_reasons = row.get("service_reasons", []) if isinstance(row.get("service_reasons"), list) else []
        readiness_reasons = readiness.get("reasons", []) if isinstance(readiness.get("reasons"), list) else []
        cqrs_pattern = str(cqrs.get("pattern", "n/a"))
        cluster_size = int(cqrs.get("cluster_size", 0) or 0)
        command_count = int(cqrs.get("command_count", 0) or 0)
        event_count = int(cqrs.get("event_count", 0) or 0)

        reasons.append(f"selected as delegable slice with score {score:.2f}")
        reasons.append(f"phase target is {phase}")
        reasons.append(f"estimated effort is {effort}")
        if service_reasons:
            for reason in service_reasons[:5]:
                reasons.append(f"service signal: {reason}")
        if cqrs_pattern != "n/a":
            reasons.append(f"cqrs pattern detected: {cqrs_pattern}")
        if cluster_size > 0:
            reasons.append(f"cqrs cluster size: {cluster_size}")
        if command_count or event_count:
            reasons.append(f"cqrs token coverage: {command_count} commands / {event_count} events")
        for reason in readiness_reasons[:6]:
            reasons.append(f"readiness signal: {reason}")

        for reason in reasons:
            reason_counts[reason] += 1

        selected_rows.append(
            {
                "module": module,
                "score": score,
                "phase": phase,
                "effort": effort,
                "cqrs_pattern": cqrs_pattern,
                "shared_types_package": str(cqrs.get("shared_types_package", "n/a")),
                "reasons": reasons,
            }
        )

    selected_rows.sort(key=lambda item: (-item["score"], item["module"]))
    return {
        "count": len(selected_rows),
        "reason_counts": [{"reason": reason, "count": count} for reason, count in reason_counts.most_common()],
        "rows": selected_rows,
    }


def build_delegation_plan(
    rows: list[dict[str, Any]],
    limit: int,
    clusters_by_module: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    clusters_by_module = clusters_by_module or {}
    delegable_rows = [row for row in rows if is_delegable_candidate(row)]
    sorted_rows = sorted(delegable_rows, key=_parse_score, reverse=True)
    selected = [
        build_output_row(row, clusters_by_module.get(str(row.get("module", "")), {}))
        for row in sorted_rows[:limit]
    ]
    markdown = render_delegation_markdown(sorted_rows, limit, clusters_by_module)
    return selected, markdown


def build_summary(
    repo_root: Path,
    profile: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
    service_boundary_payload: dict[str, Any],
    cqrs_pattern_payload: dict[str, Any],
    delegation_rows: list[dict[str, Any]],
    wave_plan_payload: dict[str, Any],
    artifact_paths: dict[str, str],
    service_boundary_decisions_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    service_boundary_decisions_payload = service_boundary_decisions_payload or {}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "profile": {
            "languages": profile["languages"],
            "frameworks": profile["frameworks"],
            "architecture_hints": profile["detected_architecture_hints"],
        },
        "counts": {
            "candidate_modules": len(candidate_rows),
            "delegable_candidate_modules": len([row for row in candidate_rows if is_delegable_candidate(row)]),
            "excluded_candidate_modules": len([row for row in candidate_rows if not is_delegable_candidate(row)]),
            "service_boundary_modules": len(service_boundary_payload.get("frontend_modules", [])),
            "cqrs_pattern_modules": len(cqrs_pattern_payload.get("rows", [])),
            "cqrs_clusters": len(cqrs_pattern_payload.get("clusters", [])),
            "migration_waves": len(wave_plan_payload.get("waves", [])),
            "recommended_services": len(service_boundary_payload.get("recommended_service_candidates", [])),
            "delegation_plan_modules": len(delegation_rows),
        },
        "top_candidates": [row["module"] for row in candidate_rows[:5]],
        "top_delegable_candidates": [row["module"] for row in sorted((row for row in candidate_rows if is_delegable_candidate(row)), key=_parse_score, reverse=True)[:5]],
        "top_service_candidates": [row["module"] for row in service_boundary_payload.get("recommended_service_candidates", [])[:5]],
        "top_cqrs_pattern_candidates": [row["module"] for row in cqrs_pattern_payload.get("rows", [])[:5]],
        "top_migration_waves": [w["wave_name"] for w in wave_plan_payload.get("waves", [])[:5]],
        "service_boundary_decision_reasons": service_boundary_decisions_payload.get("reason_counts", []),
        "artifacts": artifact_paths,
    }


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
    lines.extend([
        "",
        "## Top delegable candidates",
        "",
    ])
    for item in summary.get("top_delegable_candidates", []):
        lines.append(f"- `{item}`")
    if not summary.get("top_delegable_candidates"):
        lines.append("- `none`")
    lines.extend([
        "",
        "## Top raw migration candidates",
        "",
    ])
    for item in summary["top_candidates"]:
        lines.append(f"- `{item}`")
    if not summary["top_candidates"]:
        lines.append("- `none`")
    lines.extend([
        "",
        "## Top service candidates",
        "",
    ])
    for item in summary["top_service_candidates"]:
        lines.append(f"- `{item}`")
    if not summary["top_service_candidates"]:
        lines.append("- `none`")
    lines.extend([
        "",
        "## Service-boundary decision reasons",
        "",
    ])
    for item in summary.get("service_boundary_decision_reasons", [])[:10]:
        lines.append(f"- `{item['reason']}`: {item['count']}")
    if not summary.get("service_boundary_decision_reasons"):
        lines.append("- `none`")
    lines.extend([
        "",
        "## Excluded candidate reasons",
        "",
    ])
    for item in summary.get("excluded_candidate_reasons", [])[:10]:
        lines.append(f"- `{item['reason']}`: {item['count']}")
    if not summary.get("excluded_candidate_reasons"):
        lines.append("- `none`")
    lines.extend([
        "",
        "## Delegation decision reasons",
        "",
    ])
    for item in summary.get("delegation_decision_reasons", [])[:10]:
        lines.append(f"- `{item['reason']}`: {item['count']}")
    if not summary.get("delegation_decision_reasons"):
        lines.append("- `none`")
    lines.extend([
        "",
        "## Top CQRS pattern candidates",
        "",
    ])
    for item in summary["top_cqrs_pattern_candidates"]:
        lines.append(f"- `{item}`")
    if not summary["top_cqrs_pattern_candidates"]:
        lines.append("- `none`")
    lines.extend([
        "",
        "## Artifacts",
        "",
        "| Name | Path |",
        "| --- | --- |",
    ])
    for name, path in sorted(summary["artifacts"].items()):
        lines.append(f"| {name} | `{path}` |")
    return "\n".join(lines) + "\n"


def render_excluded_candidates_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Excluded Delegation Candidates",
        "",
        f"Total excluded candidates: {payload['count']}",
        "",
        "## Exclusion reasons",
        "",
    ]
    for item in payload.get("reason_counts", []):
        lines.append(f"- `{item['reason']}`: {item['count']}")
    if not payload.get("reason_counts"):
        lines.append("- `none`")

    lines.extend([
        "",
        "## Excluded candidates",
        "",
    ])
    for row in payload.get("rows", []):
        lines.append(f"### Excluded: {row['module'] or 'unknown'}")
        lines.append("")
        lines.append(f"- Path: `{row['path'] or '-'}`")
        lines.append(f"- Kind: `{row['kind'] or '-'}`")
        lines.append(f"- Score: `{row['score']:.2f}`")
        lines.append(f"- Phase: `{row['phase']}`")
        lines.append("- Reasons:")
        for reason in row.get("reasons", []):
            lines.append(f"  - {reason}")
        lines.append("")
    if not payload.get("rows"):
        lines.append("No excluded candidates.")
        lines.append("")
    return "\n".join(lines)


def render_delegation_decisions_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Delegation Decision Rationale",
        "",
        f"Total selected delegation candidates: {payload['count']}",
        "",
        "## Repeated decision signals",
        "",
    ]
    for item in payload.get("reason_counts", [])[:20]:
        lines.append(f"- `{item['reason']}`: {item['count']}")
    if not payload.get("reason_counts"):
        lines.append("- `none`")

    lines.extend([
        "",
        "## Selected candidates",
        "",
    ])
    for row in payload.get("rows", []):
        lines.append(f"### Selected: {row['module']}")
        lines.append("")
        lines.append(f"- Score: `{row['score']:.2f}`")
        lines.append(f"- Phase: `{row['phase']}`")
        lines.append(f"- Effort: `{row['effort']}`")
        lines.append(f"- CQRS pattern: `{row['cqrs_pattern']}`")
        lines.append(f"- Shared types package: `{row['shared_types_package']}`")
        lines.append("- Why selected:")
        for reason in row.get("reasons", []):
            lines.append(f"  - {reason}")
        lines.append("")
    if not payload.get("rows"):
        lines.append("No selected delegation candidates.")
        lines.append("")
    return "\n".join(lines)


def render_service_boundary_decisions_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Service Boundary Decision Rationale",
        "",
        f"Total recommended service candidates: {payload['count']}",
        "",
        "## Repeated decision signals",
        "",
    ]
    for item in payload.get("reason_counts", [])[:20]:
        lines.append(f"- `{item['reason']}`: {item['count']}")
    if not payload.get("reason_counts"):
        lines.append("- `none`")

    lines.extend([
        "",
        "## Recommended candidates",
        "",
    ])
    for row in payload.get("rows", []):
        lines.append(f"### Recommended: {row['module']}")
        lines.append("")
        lines.append(f"- Service slug: `{row['service_slug']}`")
        lines.append(f"- Priority: `{row['priority']}`")
        lines.append(f"- Delivery mode: `{row['delivery_mode']}`")
        lines.append(f"- Iframe score: `{row['iframe_score']}`")
        lines.append(f"- Pages: `{row['page_count']}`")
        lines.append("- Why selected:")
        for reason in row.get("reasons", []):
            lines.append(f"  - {reason}")
        lines.append("")
    if not payload.get("rows"):
        lines.append("No recommended service candidates.")
        lines.append("")
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def relative_artifact_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def run_discovery(
    repo_root: Path,
    output_dir: Path,
    config_path: Path | None = None,
    top_services: int | None = None,
    delegation_limit: int = 8,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    config = load_service_boundary_config(config_path)

    profile = profile_repository(repo_root, config)
    candidate_rows = analyze_repository(repo_root)
    excluded_candidates_payload = build_excluded_candidates_report(candidate_rows)
    service_boundary_payload = analyze_service_boundaries(repo_root, config, top_services=top_services)
    cqrs_pattern_payload = analyze_cqrs_pattern_clusters(
        repo_root,
        config,
        {str(row.get("module")): row for row in candidate_rows if isinstance(row.get("module"), str)},
    )
    cqrs_rows = cqrs_pattern_payload.get("rows", [])
    clusters_by_module = {
        str(row.get("module")): row
        for row in cqrs_rows
        if isinstance(row, dict) and isinstance(row.get("module"), str)
    }
    delegation_rows, delegation_markdown = build_delegation_plan(
        candidate_rows,
        delegation_limit,
        clusters_by_module,
    )
    service_boundary_decisions_payload = build_service_boundary_decision_report(service_boundary_payload)
    delegation_decisions_payload = build_delegation_decision_report(delegation_rows)

    # Generate migration wave plan
    waves = build_waves(cqrs_pattern_payload, candidate_rows, max_waves=5)
    wave_plan_payload = {
        "waves": [asdict(w) for w in waves]
    }
    wave_plan_markdown = render_wave_plan_markdown(waves)

    artifacts: dict[str, Path] = {
        "repository_profile_json": output_dir / "repository-profile.json",
        "repository_profile_md": output_dir / "repository-profile.md",
        "module_candidates_json": output_dir / "module-candidates.json",
        "module_candidates_md": output_dir / "module-candidates.md",
        "service_boundaries_json": output_dir / "service-boundaries.json",
        "service_boundaries_md": output_dir / "service-boundaries.md",
        "cqrs_pattern_clusters_json": output_dir / "cqrs-pattern-clusters.json",
        "cqrs_pattern_clusters_md": output_dir / "cqrs-pattern-clusters.md",
        "migration_wave_plan_json": output_dir / "migration-wave-plan.json",
        "migration_wave_plan_md": output_dir / "migration-wave-plan.md",
        "delegation_plan_json": output_dir / "delegation-plan.generated.json",
        "delegation_plan_md": output_dir / "delegation-plan.generated.md",
        "excluded_candidates_json": output_dir / "excluded-candidates.json",
        "excluded_candidates_md": output_dir / "excluded-candidates.md",
        "service_boundary_decisions_json": output_dir / "service-boundary-decisions.json",
        "service_boundary_decisions_md": output_dir / "service-boundary-decisions.md",
        "delegation_decisions_json": output_dir / "delegation-decisions.json",
        "delegation_decisions_md": output_dir / "delegation-decisions.md",
    }

    write_json(artifacts["repository_profile_json"], profile)
    write_text(artifacts["repository_profile_md"], render_repository_profile_markdown(profile))
    write_json(artifacts["module_candidates_json"], candidate_rows)
    write_text(artifacts["module_candidates_md"], render_module_candidates_markdown(candidate_rows))
    write_json(artifacts["service_boundaries_json"], service_boundary_payload)
    write_text(artifacts["service_boundaries_md"], build_service_boundaries_markdown(service_boundary_payload))
    write_json(artifacts["cqrs_pattern_clusters_json"], cqrs_pattern_payload)
    write_text(artifacts["cqrs_pattern_clusters_md"], render_cqrs_pattern_clusters_markdown(cqrs_pattern_payload))
    write_json(artifacts["migration_wave_plan_json"], wave_plan_payload)
    write_text(artifacts["migration_wave_plan_md"], wave_plan_markdown)
    write_json(artifacts["delegation_plan_json"], delegation_rows)
    write_text(artifacts["delegation_plan_md"], delegation_markdown)
    write_json(artifacts["excluded_candidates_json"], excluded_candidates_payload)
    write_text(artifacts["excluded_candidates_md"], render_excluded_candidates_markdown(excluded_candidates_payload))
    write_json(artifacts["service_boundary_decisions_json"], service_boundary_decisions_payload)
    write_text(artifacts["service_boundary_decisions_md"], render_service_boundary_decisions_markdown(service_boundary_decisions_payload))
    write_json(artifacts["delegation_decisions_json"], delegation_decisions_payload)
    write_text(artifacts["delegation_decisions_md"], render_delegation_decisions_markdown(delegation_decisions_payload))

    artifact_paths = {name: relative_artifact_path(path, repo_root) for name, path in artifacts.items()}
    summary = build_summary(
        repo_root,
        profile,
        candidate_rows,
        service_boundary_payload,
        cqrs_pattern_payload,
        delegation_rows,
        wave_plan_payload,
        artifact_paths,
        service_boundary_decisions_payload,
    )
    summary["excluded_candidate_reasons"] = excluded_candidates_payload.get("reason_counts", [])
    summary["delegation_decision_reasons"] = delegation_decisions_payload.get("reason_counts", [])
    artifacts["summary_json"] = output_dir / "migration-discovery.summary.json"
    artifacts["summary_md"] = output_dir / "migration-discovery.summary.md"
    write_json(artifacts["summary_json"], summary)
    write_text(artifacts["summary_md"], render_summary_markdown(summary))
    artifact_paths.update({
        "summary_json": relative_artifact_path(artifacts["summary_json"], repo_root),
        "summary_md": relative_artifact_path(artifacts["summary_md"], repo_root),
    })
    summary["artifacts"] = artifact_paths
    write_json(artifacts["summary_json"], summary)

    return {
        "profile": profile,
        "module_candidates": candidate_rows,
        "service_boundaries": service_boundary_payload,
        "service_boundary_decisions": service_boundary_decisions_payload,
        "cqrs_pattern_clusters": cqrs_pattern_payload,
        "migration_wave_plan": wave_plan_payload,
        "delegation_plan": delegation_rows,
        "excluded_candidates": excluded_candidates_payload,
        "delegation_decisions": delegation_decisions_payload,
        "summary": summary,
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"[ERROR] repo root not found: {repo_root}")
        return 1

    config_path = Path(args.config).resolve() if args.config else None
    output_dir = resolve_output_dir(repo_root, args.output_dir)
    try:
        payload = run_discovery(
            repo_root=repo_root,
            output_dir=output_dir,
            config_path=config_path,
            top_services=args.top_services,
            delegation_limit=args.delegation_limit,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] discovery failed: {exc}")
        return 1

    if args.stdout:
        print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
        return 0

    print(f"[INFO] wrote discovery artifacts to {output_dir}")
    print(f"[INFO] candidate modules: {len(payload['module_candidates'])}")
    print(f"[INFO] service boundary modules: {len(payload['service_boundaries'].get('frontend_modules', []))}")
    print(f"[INFO] cqrs pattern modules: {len(payload['cqrs_pattern_clusters'].get('rows', []))}")
    print(f"[INFO] delegation plan modules: {len(payload['delegation_plan'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
