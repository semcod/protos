from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from legacy_bridge.analyze_service_boundaries import analyze, build_markdown, load_config


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
