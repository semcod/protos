from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from legacy_bridge.analyze_service_boundaries import (
    _build_module_index,
    _calculate_module_stats,
    _generate_merge_hints,
    _build_eligible_modules,
    _apply_merge_hints,
    _determine_component_action,
    _build_component_row,
    analyze,
    build_markdown,
    iter_files,
    load_config,
    resolve_ts_import,
    TsFile,
    DEFAULT_CONFIG,
)


def test_analyze_service_boundaries_detects_iframe_candidates(tmp_path: Path):
    repo_root = tmp_path / "legacy-app"

    connect_id_pages = repo_root / "frontend" / "src" / "pages" / "id"
    connect_id_pages.mkdir(parents=True)
    (connect_id_pages / "connect-id-list.page.ts").write_text(
        "import { getUsers } from '../../services/id.service';\n"
        "export const page = getUsers;\n",
        encoding="utf-8",
    )
    (connect_id_pages / "connect-id-edit.page.ts").write_text(
        "import { getUsers } from '../../services/id.service';\n"
        "export const page2 = getUsers;\n",
        encoding="utf-8",
    )

    shared_service_dir = repo_root / "frontend" / "src" / "services"
    shared_service_dir.mkdir(parents=True)
    (shared_service_dir / "id.service.ts").write_text(
        "export async function getUsers() {\n"
        "  return fetch('/api/v3/identification/users');\n"
        "}\n",
        encoding="utf-8",
    )

    connect_scenario_pages = repo_root / "frontend" / "src" / "pages" / "scenario"
    connect_scenario_pages.mkdir(parents=True)
    (connect_scenario_pages / "connect-scenario-editor.page.ts").write_text(
        "export async function loadScenario() {\n"
        "  return fetch('/api/v3/scenarios/list');\n"
        "}\n",
        encoding="utf-8",
    )
    (connect_scenario_pages / "connect-scenario-run.page.ts").write_text(
        "export async function runScenario() {\n"
        "  return fetch('/api/v3/scenarios/run');\n"
        "}\n",
        encoding="utf-8",
    )

    routes_root = repo_root / "backend" / "api" / "routes" / "v3"
    routes_root.mkdir(parents=True)
    (routes_root / "identification.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(prefix='/api/v3/identification')\n"
        "@router.get('/users')\n"
        "def users():\n"
        "    return []\n",
        encoding="utf-8",
    )
    (routes_root / "scenarios.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(prefix='/api/v3/scenarios')\n"
        "@router.get('/list')\n"
        "def list_items():\n"
        "    return []\n",
        encoding="utf-8",
    )

    payload = analyze(repo_root, load_config(None), top_services=3)

    modules = {row["module"]: row for row in payload["frontend_modules"]}
    assert "connect-id" in modules
    assert "connect-scenario" in modules

    connect_id = modules["connect-id"]
    assert connect_id["backend_route_groups"] == ["identification"]
    assert connect_id["iframe_candidate"] is True
    assert connect_id["delivery_mode"] == "iframe-first"

    recommended = [row["module"] for row in payload["recommended_service_candidates"]]
    assert "connect-id" in recommended
    assert "connect-scenario" in recommended


def test_build_markdown_contains_expected_sections(tmp_path: Path):
    repo_root = tmp_path / "legacy-app"
    pages_dir = repo_root / "frontend" / "src" / "pages"
    pages_dir.mkdir(parents=True)
    (pages_dir / "connect-id-home.page.ts").write_text(
        "export async function load() {\n"
        "  return fetch('/api/v3/identification/home');\n"
        "}\n",
        encoding="utf-8",
    )
    routes_root = repo_root / "backend" / "api" / "routes" / "v3"
    routes_root.mkdir(parents=True)
    (routes_root / "identification.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(prefix='/api/v3/identification')\n",
        encoding="utf-8",
    )

    payload = analyze(repo_root, load_config(None), top_services=1)
    markdown = build_markdown(payload)

    assert "# Service Boundary Analysis" in markdown
    assert "## Execution plan" in markdown
    assert "## Suggested service components" in markdown
    assert "## Recommended service candidates" in markdown
    assert "connect-id" in markdown


def test_build_module_index_creates_correct_structure():
    """Test _build_module_index helper function."""
    ts_index = {
        "frontend/src/modules/id/page.ts": TsFile(
            path=Path("/repo/frontend/src/modules/id/page.ts"),
            rel="frontend/src/modules/id/page.ts",
            module="id",
            is_page=True,
            imports=("frontend/src/services/id.service.ts",),
            api_groups=(),
        ),
        "frontend/src/services/id.service.ts": TsFile(
            path=Path("/repo/frontend/src/services/id.service.ts"),
            rel="frontend/src/services/id.service.ts",
            module="services",
            is_page=False,
            imports=(),
            api_groups=("/api/v3/identification",),
        ),
    }
    files_by_module, cross_edges = _build_module_index(ts_index)
    
    assert "id" in files_by_module
    assert "services" in files_by_module
    assert len(files_by_module["id"]) == 1
    assert len(files_by_module["services"]) == 1
    assert cross_edges[("id", "services")] == 1


def test_determine_component_action():
    """Test _determine_component_action helper function."""
    # iframe-first case
    action = _determine_component_action([], 90, [], ["identification"])
    assert action == "iframe-first"
    
    # decompose case
    rows = [{"delivery_mode": "decompose-before-extract"}]
    action = _determine_component_action(rows, 50, [], [])
    assert action == "decompose"
    
    # extract-service case
    action = _determine_component_action([], 50, ["other"], [])
    assert action == "extract-service"


def test_default_ignore_dirs_include_reports_and_coverage():
    ignored = set(DEFAULT_CONFIG["ignore_dirs"])

    assert "reports" in ignored
    assert "coverage" in ignored


def test_resolve_ts_import_supports_dotted_basenames(tmp_path: Path):
    workspace_root = tmp_path / "repo"
    frontend_root = workspace_root / "frontend" / "src"
    pages_dir = frontend_root / "pages"
    services_dir = frontend_root / "services"
    pages_dir.mkdir(parents=True)
    services_dir.mkdir(parents=True)

    current_file = pages_dir / "home.page.ts"
    current_file.write_text("export {}\n", encoding="utf-8")
    target_file = services_dir / "id.service.ts"
    target_file.write_text("export const getUsers = () => [];\n", encoding="utf-8")

    resolved = resolve_ts_import(
        current=current_file,
        spec="../services/id.service",
        workspace_root=workspace_root,
        allowed_roots=[frontend_root],
        alias_roots={},
    )

    assert resolved == target_file


def test_iter_files_ignores_reports_and_coverage_dirs(tmp_path: Path):
    root = tmp_path / "frontend" / "src"
    reports_dir = root / "reports"
    coverage_dir = root / "coverage"
    feature_dir = root / "features"
    reports_dir.mkdir(parents=True)
    coverage_dir.mkdir(parents=True)
    feature_dir.mkdir(parents=True)

    ignored_report = reports_dir / "report.page.ts"
    ignored_cov = coverage_dir / "coverage.page.ts"
    kept_file = feature_dir / "home.page.ts"
    ignored_report.write_text("export {}\n", encoding="utf-8")
    ignored_cov.write_text("export {}\n", encoding="utf-8")
    kept_file.write_text("export {}\n", encoding="utf-8")

    files = iter_files(root, suffixes=(".ts",), ignored_names=set(DEFAULT_CONFIG["ignore_dirs"]))

    assert kept_file in files
    assert ignored_report not in files
    assert ignored_cov not in files
