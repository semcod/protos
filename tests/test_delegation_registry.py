from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from gateway.delegation import DelegatedSlice, get_delegation_health, get_delegated_slice, list_delegated_slices


def test_registry_contains_existing_slices():
    summaries = list_delegated_slices()
    names = {item["name"] for item in summaries}

    assert names == {"search", "user"}


def test_search_slice_reports_static_frontend_asset():
    delegated_slice = get_delegated_slice("search")

    assert delegated_slice is not None
    detail = delegated_slice.detail()
    assert detail["frontend"] == "static"
    assert "gateway/static/search_v2.html" in detail["frontend_paths"]


def test_delegated_slice_health_marks_missing_required_assets(tmp_path: Path):
    delegated_slice = DelegatedSlice(
        name="template",
        phase="phase-1",
        backend="planned",
        frontend="static",
        contract_paths=("contracts/template/v1/template.proto",),
        read_model_paths=("event_store.db",),
        frontend_paths=("gateway/static/template/index.html",),
    )

    health = delegated_slice.health(tmp_path)

    assert health["status"] == "degraded"
    assert set(health["missing_required"]) == {
        "contracts/template/v1/template.proto",
        "event_store.db",
        "gateway/static/template/index.html",
    }


def test_aggregate_delegation_health_returns_counts():
    health = get_delegation_health()

    assert health["module_count"] == 2
    assert health["ok_count"] + health["degraded_count"] == 2
