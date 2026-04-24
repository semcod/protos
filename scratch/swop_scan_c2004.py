#!/usr/bin/env python3
"""
Go/no-go test: czy `swop` wykrywa CQRS w c2004 z wystarczającą pokryciem?

Uruchamia `swop.scan.scanner.scan_project` na
`/home/tom/github/maskservice/c2004/backend/app/cqrs` bez tworzenia plików w c2004
(fake config_path, incremental=False, cache=None), a następnie porównuje z naiwnym
"ground truth" opartym na AST (klasy, których nazwa kończy się na Command/Query/
Event/Handler lub które dziedziczą z Base*).

Wypluwa:
- Pokrycie per-kind (command/query/event/handler)
- Pokrycie łączne
- Listę klas z ground-truth, których swop NIE wykrył (false negatives)
- Histogram `reason` i `via` wykryć

Użycie:
    PYTHONPATH=/home/tom/github/semcod/inspect \
    /home/tom/github/semcod/inspect/venv/bin/python \
    scratch/swop_scan_c2004.py
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# --- Konfiguracja celu ---------------------------------------------------------

C2004_ROOT = Path("/home/tom/github/maskservice/c2004")
CQRS_REL = "backend/app/cqrs"
TARGET = C2004_ROOT / CQRS_REL

# --- Ładowanie swop bez instalacji --------------------------------------------

SWOP_REPO = Path("/home/tom/github/semcod/inspect")
if str(SWOP_REPO) not in sys.path:
    sys.path.insert(0, str(SWOP_REPO))

from swop.config import SwopConfig  # noqa: E402
from swop.scan.scanner import scan_project  # noqa: E402

# --- Ground truth: ta sama lista suffixów / baz co swop ------------------------

NAME_SUFFIXES: List[Tuple[str, str]] = [
    ("Command", "command"),
    ("Cmd", "command"),
    ("Query", "query"),
    ("Qry", "query"),
    ("Event", "event"),
    ("Evt", "event"),
    ("Handler", "handler"),
]
BASE_KINDS: Dict[str, str] = {
    "BaseCommand": "command",
    "Command": "command",
    "CommandBase": "command",
    "BaseQuery": "query",
    "Query": "query",
    "QueryBase": "query",
    "BaseEvent": "event",
    "Event": "event",
    "EventBase": "event",
    "DomainEvent": "event",
    "BaseHandler": "handler",
    "Handler": "handler",
    "CommandHandler": "handler",
    "QueryHandler": "handler",
}


def _kind_by_suffix(name: str):
    for suffix, kind in NAME_SUFFIXES:
        if name.endswith(suffix) and name != suffix:
            return kind
    return None


def _base_names(node: ast.ClassDef) -> List[str]:
    names: List[str] = []
    for b in node.bases:
        if isinstance(b, ast.Name):
            names.append(b.id)
        elif isinstance(b, ast.Attribute):
            names.append(b.attr)
        elif isinstance(b, ast.Subscript):
            inner = b.value
            if isinstance(inner, ast.Name):
                names.append(inner.id)
            elif isinstance(inner, ast.Attribute):
                names.append(inner.attr)
    return names


def _kind_by_base(bases: List[str]):
    for b in bases:
        if b in BASE_KINDS:
            return BASE_KINDS[b]
    return None


def collect_ground_truth(root: Path) -> List[Dict[str, object]]:
    """Wszystkie ClassDef z root, klasyfikowane po suffix lub bazie."""
    results: List[Dict[str, object]] = []
    for py in root.rglob("*.py"):
        # pomijamy oczywisty noise
        if "__pycache__" in py.parts:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"),
                             filename=str(py))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = _base_names(node)
            suffix_kind = _kind_by_suffix(node.name)
            base_kind = _kind_by_base(bases)
            if suffix_kind or base_kind:
                results.append({
                    "name": node.name,
                    "kind": suffix_kind or base_kind,
                    "kind_suffix": suffix_kind,
                    "kind_base": base_kind,
                    "bases": bases,
                    "file": str(py.relative_to(C2004_ROOT)),
                    "line": node.lineno,
                })
    return results


def run_swop_scan() -> "object":
    """Programowe wywołanie `scan_project` bez dotykania plików c2004."""
    # Fake config_path: plik nie musi istnieć, tylko parent ma być poprawny
    # (służy tylko do obliczania project_root).
    fake_cfg_path = C2004_ROOT / ".swop_scratch.yaml"
    cfg = SwopConfig(
        project="c2004-cqrs-scan",
        source_roots=[CQRS_REL],
        exclude=["**/__pycache__/**", "**/tests/**"],
        state_dir=".swop",
        config_path=fake_cfg_path,
    )
    return scan_project(cfg, incremental=False, cache=None)


def main() -> int:
    if not TARGET.is_dir():
        print(f"ERR: {TARGET} nie istnieje", file=sys.stderr)
        return 2

    gt = collect_ground_truth(TARGET)
    print(f"[ground-truth] {len(gt)} klas wygląda na CQRS wg suffix/bazy")
    gt_by_kind: Dict[str, int] = {"command": 0, "query": 0, "event": 0, "handler": 0}
    for item in gt:
        gt_by_kind[item["kind"]] = gt_by_kind.get(item["kind"], 0) + 1
    print(f"[ground-truth] per kind: {gt_by_kind}")

    report = run_swop_scan()
    print()
    print(report.format_text())
    print()

    detected_keys: Set[Tuple[str, str, int]] = set()
    for det in report.detections:
        # source_file jest względem project_root == C2004_ROOT
        detected_keys.add((det.name, det.source_file, det.source_line))

    gt_keys: Set[Tuple[str, str, int]] = {
        (item["name"], item["file"], item["line"]) for item in gt
    }

    hits = gt_keys & detected_keys
    missed = gt_keys - detected_keys
    extra = detected_keys - gt_keys

    total_gt = len(gt_keys)
    coverage = (len(hits) / total_gt * 100.0) if total_gt else 0.0
    print(f"[coverage] hit {len(hits)} / {total_gt} ground-truth  =>  {coverage:.1f}%")
    print(f"[coverage] swop nadwykrył: {len(extra)} klas (nie było w ground-truth)")
    print()

    # Histogram reason/via
    via_hist: Dict[str, int] = {}
    reason_hist: Dict[str, int] = {}
    for det in report.detections:
        via_hist[det.via] = via_hist.get(det.via, 0) + 1
        reason_hist[det.reason] = reason_hist.get(det.reason, 0) + 1
    print("[via]", via_hist)
    print("[reason top5]", sorted(reason_hist.items(), key=lambda x: -x[1])[:5])
    print()

    if missed:
        print(f"[missed] {len(missed)} klas z ground-truth NIE wykrytych przez swop:")
        by_kind: Dict[str, List[Dict[str, object]]] = {}
        gt_index = {(g["name"], g["file"], g["line"]): g for g in gt}
        for key in sorted(missed):
            g = gt_index[key]
            by_kind.setdefault(g["kind"], []).append(g)
        for kind, items in by_kind.items():
            print(f"  {kind}: {len(items)}")
            for it in items[:10]:
                print(f"    - {it['name']}  ({it['file']}:{it['line']})  bases={it['bases']}")
            if len(items) > 10:
                print(f"    ... +{len(items) - 10} więcej")

    # Zapis pełnego raportu JSON do /tmp
    out_json = Path("/tmp/c2004-swop-scan.json")
    out_json.write_text(json.dumps({
        "coverage_pct": coverage,
        "ground_truth_total": total_gt,
        "ground_truth_by_kind": gt_by_kind,
        "swop_totals": report.kinds(),
        "swop_via": report.via(),
        "hits": len(hits),
        "missed": sorted([list(k) for k in missed]),
        "extra": sorted([list(k) for k in extra])[:200],
        "report": report.to_dict(),
    }, indent=2, default=str))
    print(f"\n[out] pełny raport: {out_json}")

    # Go/no-go
    if coverage >= 80:
        verdict = "GO — swop wykrywa >=80% istniejącego CQRS; pipeline swop->proto->protos realny"
    elif coverage >= 50:
        verdict = "MAYBE — 50-80%, do rozważenia doklejenie dekoratorów do reszty"
    else:
        verdict = "NO-GO — <50% wykrycia, swop nie pasuje do wzorca c2004 bez zmian"
    print(f"\n[verdict] {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
