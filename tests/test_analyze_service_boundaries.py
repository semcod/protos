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
    _compute_cross_stats,
    _compute_api_coverage,
    _compute_iframe_score,
    _is_iframe_candidate,
    _is_test_file,
    _build_single_ts_file,
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


# ── helpers extracted from _calculate_module_stats ───────────────────────────

def _make_ts_file(path: Path, workspace_root: Path, module: str, is_page: bool, api_groups: tuple[str, ...] = (), imports: tuple[str, ...] = ()) -> TsFile:
    return TsFile(
        path=path,
        rel=path.relative_to(workspace_root).as_posix(),
        module=module,
        is_page=is_page,
        imports=imports,
        api_groups=api_groups,
    )


def test_compute_iframe_score_clamped_at_100():
    score = _compute_iframe_score(page_count=20, api_groups=["/api/v3/foo", "/api/v3/bar"], cross_targets=[], cross_outgoing=0, shared_count=0)
    assert score == 100


def test_compute_iframe_score_clamped_at_0():
    score = _compute_iframe_score(page_count=0, api_groups=[], cross_targets=["a"] * 10, cross_outgoing=50, shared_count=100)
    assert score == 0


def test_compute_iframe_score_midrange():
    # Baseline: 62 + 0 + 0 - 0 - 0 - 0 = 62
    score = _compute_iframe_score(page_count=0, api_groups=[], cross_targets=[], cross_outgoing=0, shared_count=0)
    assert score == 62


def test_is_iframe_candidate_true():
    assert _is_iframe_candidate(iframe_score=75, cross_targets=["x"], route_group_hits=["id"]) is True


def test_is_iframe_candidate_false_when_too_many_cross_targets():
    assert _is_iframe_candidate(iframe_score=75, cross_targets=["a", "b", "c"], route_group_hits=["id"]) is False


def test_is_iframe_candidate_false_when_score_low():
    assert _is_iframe_candidate(iframe_score=55, cross_targets=[], route_group_hits=[]) is False


def test_compute_cross_stats_counts_correctly(tmp_path: Path):
    from collections import Counter

    workspace = tmp_path / "repo"
    frontend = workspace / "frontend" / "src"
    frontend.mkdir(parents=True)

    a = _make_ts_file(frontend / "page-a.ts", workspace, module="a", is_page=True)
    b = _make_ts_file(frontend / "page-b.ts", workspace, module="b", is_page=False)
    shared = _make_ts_file(frontend / "shared.ts", workspace, module="shared", is_page=False)

    a_with_import = TsFile(
        path=a.path,
        rel=a.rel,
        module="a",
        is_page=True,
        imports=(b.rel, shared.rel),
        api_groups=(),
    )

    ts_index = {a_with_import.rel: a_with_import, b.rel: b, shared.rel: shared}
    cross_edges: Counter[tuple[str, str]] = Counter({("a", "b"): 2, ("a", "shared"): 1})

    closure, cross_targets, shared_count, cross_outgoing = _compute_cross_stats(
        module="a",
        owned_files=[a_with_import.rel],
        ts_index=ts_index,
        cross_edges=cross_edges,
        shared_modules={"shared"},
    )

    assert a_with_import.rel in closure
    assert b.rel in closure
    assert "b" in cross_targets
    assert "shared" not in cross_targets
    assert shared_count == 1
    assert cross_outgoing == 2


def test_compute_api_coverage_extracts_groups(tmp_path: Path):
    workspace = tmp_path / "repo"
    frontend = workspace / "frontend" / "src"
    frontend.mkdir(parents=True)

    f = _make_ts_file(frontend / "page.ts", workspace, module="id", is_page=True, api_groups=("/api/v3/identification",))
    ts_index = {f.rel: f}

    api_groups, direct_api_groups, route_group_hits, matched = _compute_api_coverage(
        closure={f.rel},
        owned_files=[f.rel],
        ts_index=ts_index,
        backend_groups={},
    )

    assert "/api/v3/identification" in api_groups
    assert "/api/v3/identification" in direct_api_groups
    assert "identification" in route_group_hits
    assert matched == []


# ── _is_test_file / _build_single_ts_file ────────────────────────────────────

def test_is_test_file_detects_spec_and_test_suffixes():
    for name in ["foo.test.ts", "bar.spec.ts", "baz.test.tsx", "qux.spec.js"]:
        assert _is_test_file(name) is True


def test_is_test_file_passes_normal_files():
    for name in ["home.page.ts", "id.service.ts", "utils.ts", "index.tsx"]:
        assert _is_test_file(name) is False


def test_build_single_ts_file_skips_test_files(tmp_path: Path):
    workspace = tmp_path / "repo"
    frontend = workspace / "frontend" / "src"
    frontend.mkdir(parents=True)
    test_file = frontend / "home.test.ts"
    test_file.write_text("describe('x', () => {});\n", encoding="utf-8")

    import re
    api_pattern = re.compile(r"/api/v\d+(?:/[A-Za-z0-9._{}\\-]+)+")
    config = DEFAULT_CONFIG

    result = _build_single_ts_file(
        path=test_file,
        root=frontend,
        workspace_root=workspace,
        frontend_roots=[frontend],
        alias_roots={},
        api_pattern=api_pattern,
        group_depth=3,
        config=config,
    )

    assert result is None


def test_build_single_ts_file_parses_page(tmp_path: Path):
    workspace = tmp_path / "repo"
    frontend = workspace / "frontend" / "src" / "pages" / "id"
    frontend.mkdir(parents=True)
    page = frontend / "connect-id-home.page.ts"
    page.write_text("export async function load() { return fetch('/api/v3/identification/home'); }\n", encoding="utf-8")

    import re
    api_pattern = re.compile(r"/api/v\d+(?:/[A-Za-z0-9._{}\\-]+)+")
    config = DEFAULT_CONFIG

    frontend_root = workspace / "frontend" / "src"
    result = _build_single_ts_file(
        path=page,
        root=frontend_root,
        workspace_root=workspace,
        frontend_roots=[frontend_root],
        alias_roots={},
        api_pattern=api_pattern,
        group_depth=3,
        config=config,
    )

    assert result is not None
    assert result.is_page is True
    assert result.module == "connect-id"
    assert "/api/v3/identification" in result.api_groups

