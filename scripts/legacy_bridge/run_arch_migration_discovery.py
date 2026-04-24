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
    from legacy_bridge.analyze_service_boundaries import analyze as analyze_service_boundaries
    from legacy_bridge.analyze_service_boundaries import build_markdown as build_service_boundaries_markdown
    from legacy_bridge.analyze_service_boundaries import load_config as load_service_boundary_config
    from legacy_bridge.detect_cqrs_pattern_clusters import analyze_repository as analyze_cqrs_pattern_clusters
    from legacy_bridge.detect_cqrs_pattern_clusters import render_markdown as render_cqrs_pattern_clusters_markdown
    from legacy_bridge.delegation_plan import build_output_row, render_markdown as render_delegation_markdown
    from legacy_bridge.generate_migration_wave_plan import build_waves, render_markdown as render_wave_plan_markdown
except ModuleNotFoundError:
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
    try:
        return float(row.get("score", 0.0))
    except (TypeError, ValueError):
        return 0.0


def build_delegation_plan(
    rows: list[dict[str, Any]],
    limit: int,
    clusters_by_module: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    clusters_by_module = clusters_by_module or {}
    sorted_rows = sorted(rows, key=_parse_score, reverse=True)
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
) -> dict[str, Any]:
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
            "service_boundary_modules": len(service_boundary_payload.get("frontend_modules", [])),
            "cqrs_pattern_modules": len(cqrs_pattern_payload.get("rows", [])),
            "cqrs_clusters": len(cqrs_pattern_payload.get("clusters", [])),
            "migration_waves": len(wave_plan_payload.get("waves", [])),
            "recommended_services": len(service_boundary_payload.get("recommended_service_candidates", [])),
            "delegation_plan_modules": len(delegation_rows),
        },
        "top_candidates": [row["module"] for row in candidate_rows[:5]],
        "top_service_candidates": [row["module"] for row in service_boundary_payload.get("recommended_service_candidates", [])[:5]],
        "top_cqrs_pattern_candidates": [row["module"] for row in cqrs_pattern_payload.get("rows", [])[:5]],
        "top_migration_waves": [w["wave_name"] for w in wave_plan_payload.get("waves", [])[:5]],
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
        "## Top migration candidates",
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

    artifact_paths = {name: relative_artifact_path(path, repo_root) for name, path in artifacts.items()}
    summary = build_summary(repo_root, profile, candidate_rows, service_boundary_payload, cqrs_pattern_payload, delegation_rows, wave_plan_payload, artifact_paths)
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
        "cqrs_pattern_clusters": cqrs_pattern_payload,
        "migration_wave_plan": wave_plan_payload,
        "delegation_plan": delegation_rows,
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
