from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from legacy_bridge.generate_migration_wave_plan import build_waves, estimate_effort, WaveModule


def test_build_waves_groups_by_pattern_priority():
    clusters = {
        "rows": [
            {"module": "connect-data", "pattern": "data-grid-cqrs", "extraction_target": "t:cqrs-data-grid", "score": 85.0, "phase": "phase-1", "cluster_members": ["connect-data", "connect-workshop"]},
            {"module": "connect-workshop", "pattern": "data-grid-cqrs", "extraction_target": "t:cqrs-data-grid", "score": 82.0, "phase": "phase-1", "cluster_members": ["connect-data", "connect-workshop"]},
            {"module": "connect-reports", "pattern": "reports-filtering-cqrs", "extraction_target": "t:reports-core", "score": 78.0, "phase": "phase-2", "cluster_members": ["connect-reports"]},
            {"module": "connect-manager", "pattern": "manager-library-workflow-cqrs", "extraction_target": "t:manager-core", "score": 65.0, "phase": "phase-2", "cluster_members": ["connect-manager"]},
        ],
        "clusters": [],
    }
    candidates = [
        {"module": "connect-data", "score": 85.0, "phase": "phase-1"},
        {"module": "connect-workshop", "score": 82.0, "phase": "phase-1"},
        {"module": "connect-reports", "score": 78.0, "phase": "phase-2"},
        {"module": "connect-manager", "score": 65.0, "phase": "phase-2"},
    ]

    waves = build_waves(clusters, candidates, max_waves=5)

    assert len(waves) >= 2
    assert waves[0].pattern_type == "data-grid-cqrs"
    assert len(waves[0].modules) == 2
    assert waves[0].modules[0].module == "connect-data"
    assert waves[0].estimated_effort == "low"


def test_estimate_effort():
    # Empty defaults to medium (avg_score=50)
    assert estimate_effort([]) == "medium"
    modules = [WaveModule(module="m1", pattern="data-grid-cqrs", extraction_target="t", score=80.0, phase="phase-1", cluster_members=["m1"])]
    assert estimate_effort(modules) == "low"
