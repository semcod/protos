"""
Generate phased migration wave plan from CQRS pattern clusters and candidate scoring.

Input:
- migration/cqrs-pattern-clusters.json (from detect_cqrs_pattern_clusters)
- migration/module-candidates.json (from detect_migration_candidates)

Output:
- migration/migration-wave-plan.json
- migration/migration-wave-plan.md

Waves are ordered by:
1. Pattern maturity (data-grid > reports > manager > config > custom)
2. Candidate phase (phase-1 first, then phase-2)
3. Cluster size (larger clusters first for bigger ROI)
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


# Wave ordering priority (lower = earlier)
PATTERN_WAVE_PRIORITY: dict[str, int] = {
    "data-grid-cqrs": 1,  # Most mature, already extracted in c2004
    "reports-filtering-cqrs": 2,
    "manager-library-workflow-cqrs": 3,
    "config-admin-cqrs": 4,
    "custom-cqrs": 5,  # Least mature, per-module extraction
}

PHASE_PRIORITY: dict[str, int] = {
    "phase-1": 1,
    "phase-2": 2,
    "phase-3": 3,
    None: 4,
}


@dataclass
class WaveModule:
    module: str
    pattern: str
    extraction_target: str
    score: float | None
    phase: str | None
    cluster_members: list[str]


@dataclass
class MigrationWave:
    wave_number: int
    wave_name: str
    pattern_type: str
    extraction_target: str
    priority_reason: str
    modules: list[WaveModule]
    estimated_effort: str  # low/medium/high based on module count and complexity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate phased migration wave plan")
    parser.add_argument("--repo-root", required=True, help="repository root")
    parser.add_argument("--cqrs-clusters", default="reports/migration-discovery/cqrs-pattern-clusters.json",
                        help="path to CQRS pattern clusters JSON (relative to repo-root or absolute)")
    parser.add_argument("--candidates", default="reports/migration-discovery/module-candidates.json",
                        help="path to module candidates JSON (relative to repo-root or absolute)")
    parser.add_argument("--output-dir", default="reports/migration-discovery",
                        help="output directory for wave plan")
    parser.add_argument("--max-waves", type=int, default=5, help="maximum number of waves to generate")
    parser.add_argument("--stdout", action="store_true", help="print JSON to stdout")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def resolve_path(repo_root: Path, raw: str) -> Path:
    p = Path(raw)
    return p if p.is_absolute() else repo_root / p


def determine_wave_name(pattern: str, extraction_target: str) -> str:
    """Generate human-readable wave name from pattern type."""
    if pattern == "data-grid-cqrs":
        return "CQRS Data-Grid Base Types"
    if pattern == "reports-filtering-cqrs":
        return "Reports Core Types"
    if pattern == "manager-library-workflow-cqrs":
        return "Manager Library Workflow"
    if pattern == "config-admin-cqrs":
        return "Config Admin Types"
    if "custom" in pattern:
        return f"Custom Extraction: {extraction_target.split(':')[-1]}"
    return f"{pattern.replace('-', ' ').title()}"


def estimate_effort(modules: list[WaveModule]) -> str:
    """Estimate effort based on module count and complexity."""
    count = len(modules)
    avg_score = sum(m.score or 50 for m in modules) / count if count > 0 else 50

    if count <= 2 and avg_score >= 70:
        return "low"
    if count <= 4 and avg_score >= 50:
        return "medium"
    return "high"


def build_waves(clusters_data: dict[str, Any] | None, candidates_data: list[dict[str, Any]] | None, max_waves: int) -> list[MigrationWave]:
    """Build migration waves from CQRS clusters and candidates."""
    if clusters_data is None:
        clusters_data = {"rows": [], "clusters": []}
    if candidates_data is None:
        candidates_data = []

    rows = clusters_data.get("rows", [])

    # Group modules by pattern type
    pattern_groups: dict[str, list[WaveModule]] = defaultdict(list)

    for row in rows:
        module = row.get("module", "")
        pattern = row.get("pattern", "custom-cqrs")
        extraction_target = row.get("extraction_target", "@semcod/contracts-types:custom")

        wave_module = WaveModule(
            module=module,
            pattern=pattern,
            extraction_target=extraction_target,
            score=row.get("score"),
            phase=row.get("phase"),
            cluster_members=row.get("cluster_members", [module]),
        )
        pattern_groups[pattern].append(wave_module)

    # Sort patterns by priority
    sorted_patterns = sorted(
        pattern_groups.items(),
        key=lambda item: (PATTERN_WAVE_PRIORITY.get(item[0], 99), -len(item[1]))
    )

    waves: list[MigrationWave] = []
    for idx, (pattern, modules) in enumerate(sorted_patterns[:max_waves], 1):
        # Sort modules within wave: phase-1 first, then by score
        modules.sort(key=lambda m: (PHASE_PRIORITY.get(m.phase, 99), -(m.score or 0)))

        # Deduplicate by extraction target (merge similar targets)
        target_groups: dict[str, list[WaveModule]] = defaultdict(list)
        for m in modules:
            target_groups[m.extraction_target].append(m)

        for target_idx, (target, target_modules) in enumerate(target_groups.items()):
            wave_num = idx if len(target_groups) == 1 else f"{idx}.{target_idx + 1}"

            # Determine priority reason
            phases = {m.phase for m in target_modules if m.phase}
            if "phase-1" in phases:
                reason = "phase-1 candidates with low coupling"
            elif len(target_modules) >= 3:
                reason = f"large cluster ({len(target_modules)} modules) for maximum ROI"
            elif pattern in PATTERN_WAVE_PRIORITY and PATTERN_WAVE_PRIORITY[pattern] <= 2:
                reason = "mature CQRS pattern ready for extraction"
            else:
                reason = "pattern-based extraction opportunity"

            waves.append(MigrationWave(
                wave_number=int(str(wave_num).replace(".", "")),  # Simple numeric for sorting
                wave_name=determine_wave_name(pattern, target),
                pattern_type=pattern,
                extraction_target=target,
                priority_reason=reason,
                modules=target_modules,
                estimated_effort=estimate_effort(target_modules),
            ))

    return waves[:max_waves]


def render_markdown(waves: list[MigrationWave]) -> str:
    """Render wave plan as Markdown."""
    lines = [
        "# Migration Wave Plan",
        "",
        "Generated by generate_migration_wave_plan.py.",
        "",
        f"**Total waves:** {len(waves)}",
        "",
        "## Execution Order",
        "",
        "Execute waves in order. Each wave should be completed and validated before starting the next.",
        "",
    ]

    for wave in waves:
        lines.extend([
            f"### Wave {wave.wave_number}: {wave.wave_name}",
            "",
            f"- **Pattern type:** `{wave.pattern_type}`",
            f"- **Extraction target:** `{wave.extraction_target}`",
            f"- **Priority reason:** {wave.priority_reason}",
            f"- **Estimated effort:** {wave.estimated_effort}",
            f"- **Modules:** {len(wave.modules)}",
            "",
            "| Module | Score | Phase | Cluster Size |",
            "|--------|-------|-------|--------------|",
        ])

        for m in wave.modules[:10]:  # Show first 10
            score = f"{m.score:.1f}" if m.score else "n/a"
            phase = m.phase or "n/a"
            cluster_size = len(m.cluster_members)
            lines.append(f"| {m.module} | {score} | {phase} | {cluster_size} |")

        if len(wave.modules) > 10:
            lines.append(f"| ... ({len(wave.modules) - 10} more) | | | |")

        lines.append("")

    # Add summary by pattern type
    lines.extend([
        "## Summary by Pattern Type",
        "",
    ])

    pattern_summary: dict[str, list[str]] = defaultdict(list)
    for wave in waves:
        pattern_summary[wave.pattern_type].extend([m.module for m in wave.modules])

    for pattern, modules in sorted(pattern_summary.items(),
                                    key=lambda x: PATTERN_WAVE_PRIORITY.get(x[0], 99)):
        lines.append(f"- **{pattern}**: {len(modules)} modules ({', '.join(modules[:5])}{'...' if len(modules) > 5 else ''})")

    lines.extend([
        "",
        "## Next Steps",
        "",
        "1. Start with Wave 1 (highest priority)",
        "2. Create the shared type package for the extraction target",
        "3. Migrate each module in the wave, updating imports",
        "4. Run regression tests after each module",
        "5. Mark wave as complete before proceeding to next",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    if not repo_root.exists() or not repo_root.is_dir():
        print(f"[ERROR] repo root not found: {repo_root}")
        return 1

    # Load inputs
    clusters_path = resolve_path(repo_root, args.cqrs_clusters)
    candidates_path = resolve_path(repo_root, args.candidates)

    clusters_data = load_json(clusters_path)
    candidates_data = load_json(candidates_path)

    if clusters_data is None:
        print(f"[WARN] CQRS clusters not found at {clusters_path}, generating empty plan")
        clusters_data = {"rows": [], "clusters": []}

    if candidates_data is None:
        print(f"[WARN] Module candidates not found at {candidates_path}")
        candidates_data = []

    # Generate waves
    waves = build_waves(clusters_data, candidates_data, args.max_waves)

    # Prepare output
    output = {
        "generated_at": str(Path(__file__).stat().st_mtime),  # Simple timestamp placeholder
        "repo_root": str(repo_root),
        "total_waves": len(waves),
        "waves": [asdict(w) for w in waves],
    }

    if args.stdout:
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    # Write outputs
    out_dir = resolve_path(repo_root, args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "migration-wave-plan.json"
    md_path = out_dir / "migration-wave-plan.md"

    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(waves), encoding="utf-8")

    print(f"[INFO] wrote {json_path}")
    print(f"[INFO] wrote {md_path}")
    print(f"[INFO] generated {len(waves)} migration waves")

    # Print summary
    for wave in waves:
        print(f"  Wave {wave.wave_number}: {wave.wave_name} ({len(wave.modules)} modules, {wave.estimated_effort} effort)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
