#!/usr/bin/env python3
"""
Generate protogate delegation plan from c2004 migration reports.

Input:
- module candidates report produced by c2004/scripts/detect_migration_candidates.py

Output:
- docs/delegation-plan.generated.md
- docs/delegation-plan.generated.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from legacy_bridge.candidate_selection import is_delegable_candidate, parse_score
    from legacy_bridge.delegation_plan import build_output_row, render_markdown
except ModuleNotFoundError:
    from candidate_selection import is_delegable_candidate, parse_score
    from delegation_plan import build_output_row, render_markdown


def load_candidates(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("candidate report must be a JSON array")
    return [row for row in data if isinstance(row, dict)]


def load_clusters(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[Any]
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and isinstance(data.get("rows"), list):
        rows = data["rows"]
    else:
        return {}

    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        module = row.get("module")
        if isinstance(module, str):
            out[module] = row
    return out


def dedupe_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_module: dict[str, dict[str, Any]] = {}
    for row in rows:
        module = row.get("module")
        if not isinstance(module, str) or not module.strip():
            continue
        existing = by_module.get(module)
        if existing is None or parse_score(row) > parse_score(existing):
            by_module[module] = row
    return list(by_module.values())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate delegation plan for protogate from c2004 candidate report")
    parser.add_argument("--input", required=True, help="path to c2004 migration/module-candidates.json")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[2] / "docs"),
        help="directory where generated plan files are written",
    )
    parser.add_argument(
        "--clusters",
        default="",
        help="optional path to c2004 migration/cqrs-pattern-clusters.json",
    )
    parser.add_argument("--limit", type=int, default=8, help="number of top modules to include")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    out_dir = Path(args.output_dir).resolve()

    if not input_path.exists():
        print(f"[ERROR] input not found: {input_path}")
        return 1

    rows = [row for row in dedupe_candidates(load_candidates(input_path)) if is_delegable_candidate(row)]
    cluster_path = Path(args.clusters).resolve() if args.clusters else None
    clusters = load_clusters(cluster_path)
    rows.sort(key=parse_score, reverse=True)
    limit = max(1, int(args.limit))

    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "delegation-plan.generated.json"
    out_md = out_dir / "delegation-plan.generated.md"

    selected = [build_output_row(row, clusters.get(str(row.get("module", "")), {})) for row in rows[:limit]]
    out_json.write_text(json.dumps(selected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(rows, limit, clusters), encoding="utf-8")

    print(f"[INFO] wrote {out_json}")
    print(f"[INFO] wrote {out_md}")
    print(f"[INFO] modules selected: {len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
