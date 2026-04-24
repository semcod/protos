from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from legacy_bridge.detect_cqrs_pattern_clusters import analyze_repository, normalize_config, render_markdown


def test_detect_cqrs_pattern_clusters_identifies_data_grid_cluster(tmp_path: Path):
    repo_root = tmp_path / "legacy-app"
    module_root = repo_root / "frontend" / "src" / "modules"

    data_dir = module_root / "connect-data" / "cqrs"
    data_dir.mkdir(parents=True)
    (data_dir / "types.ts").write_text(
        "export type ConnectDataCommand =\n"
        "  | { type: 'LoadSchema' }\n"
        "  | { type: 'LoadRows' }\n"
        "  | { type: 'SaveRow' }\n"
        "  | { type: 'DeleteRow' }\n"
        "  | { type: 'CreateRow' }\n"        
        "export type ConnectDataEvent =\n"
        "  | { type: 'SchemaLoaded' }\n"
        "  | { type: 'RowsLoaded' }\n"
        "  | { type: 'RowSaved' }\n"
        "  | { type: 'RowDeleted' }\n"
        "  | { type: 'RowCreated' }\n",
        encoding="utf-8",
    )

    workshop_dir = module_root / "connect-workshop" / "cqrs"
    workshop_dir.mkdir(parents=True)
    (workshop_dir / "types.ts").write_text(
        "export type ConnectWorkshopCommand =\n"
        "  | { type: 'LoadSchema' }\n"
        "  | { type: 'LoadRows' }\n"
        "  | { type: 'BulkSave' }\n"
        "  | { type: 'BulkDelete' }\n"        
        "export type ConnectWorkshopEvent =\n"
        "  | { type: 'SchemaLoaded' }\n"
        "  | { type: 'RowsLoaded' }\n"
        "  | { type: 'BulkSaveCompleted' }\n"
        "  | { type: 'BulkDeleteCompleted' }\n",
        encoding="utf-8",
    )

    payload = analyze_repository(
        repo_root,
        normalize_config(None),
        {
            "connect-data": {"module": "connect-data", "score": 84.0, "phase": "phase-1"},
            "connect-workshop": {"module": "connect-workshop", "score": 60.0, "phase": "phase-2"},
        },
    )

    rows = {row["module"]: row for row in payload["rows"]}
    assert rows["connect-data"]["pattern"] == "data-grid-cqrs"
    assert rows["connect-data"]["extraction_target"] == "@semcod/contracts-types:cqrs-data-grid"
    assert rows["connect-data"]["priority_hint"] == "early"
    assert rows["connect-workshop"]["pattern"] == "data-grid-cqrs"
    assert rows["connect-workshop"]["cluster_members"] == ["connect-data", "connect-workshop"]

    markdown = render_markdown(payload)
    assert "# CQRS Pattern Clusters" in markdown
    assert "data-grid-cqrs" in markdown
