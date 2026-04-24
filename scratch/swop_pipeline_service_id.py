#!/usr/bin/env python3
"""
End-to-end test swop pipeline dla `backend/app/cqrs/identification/` w c2004.

Krok 1: scan tylko `identification/` jako bounded context "identification"
Krok 2: generate_manifests -> /tmp/swop-pipeline/manifests/identification/*.yml
Krok 3: generate_proto_from_manifests -> /tmp/swop-pipeline/proto/identification/v1/identification.proto

Cel: zobaczyc na ile wygenerowany .proto jest sensowny (nazwy pol, typy, RPC signatures)
zanim zobowiązemy się do walking skeleton service-id.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

C2004_ROOT = Path("/home/tom/github/maskservice/c2004")
CQRS_REL = "backend/app/cqrs/identification"

SWOP_REPO = Path("/home/tom/github/semcod/inspect")
if str(SWOP_REPO) not in sys.path:
    sys.path.insert(0, str(SWOP_REPO))

from swop.config import BoundedContextConfig, SwopConfig  # noqa: E402
from swop.manifests import generate_manifests  # noqa: E402
from swop.proto.generator import generate_proto_from_manifests  # noqa: E402
from swop.scan.scanner import scan_project  # noqa: E402


def main() -> int:
    target = C2004_ROOT / CQRS_REL
    if not target.is_dir():
        print(f"ERR: {target} nie istnieje", file=sys.stderr)
        return 2

    out_root = Path("/tmp/swop-pipeline")
    if out_root.exists():
        shutil.rmtree(out_root)
    manifests_dir = out_root / "manifests"
    proto_dir = out_root / "proto"
    manifests_dir.mkdir(parents=True)
    proto_dir.mkdir(parents=True)

    fake_cfg_path = C2004_ROOT / ".swop_scratch.yaml"
    cfg = SwopConfig(
        project="c2004-identification",
        source_roots=[CQRS_REL],
        exclude=["**/__pycache__/**", "**/tests/**"],
        bounded_contexts=[
            BoundedContextConfig(name="identification", source=CQRS_REL),
        ],
        state_dir=".swop",
        config_path=fake_cfg_path,
    )

    print("### KROK 1: swop scan")
    report = scan_project(cfg, incremental=False, cache=None)
    print(report.format_text())
    print()

    print("### KROK 2: swop gen manifests")
    mres = generate_manifests(report, cfg, out_dir=manifests_dir)
    print(mres.format())
    for mf in mres.files:
        print(f"\n--- {mf.path.relative_to(out_root)} ---")
        print(mf.path.read_text(encoding="utf-8"))
    print()

    print("### KROK 3: swop gen proto --out", proto_dir)
    pres = generate_proto_from_manifests(manifests_dir, proto_dir)
    print(pres.format())
    if pres.warnings:
        print("[warnings]")
        for w in pres.warnings:
            print("  !", w)
    for pf in pres.files:
        print(f"\n--- {pf.path.relative_to(out_root)} ---")
        print(pf.path.read_text(encoding="utf-8"))

    print()
    print("=== Podsumowanie ===")
    print(f"  manifesty:  {manifests_dir}")
    print(f"  .proto   :  {proto_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
