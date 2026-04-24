from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from legacy_bridge.run_arch_migration_discovery import run_discovery


def test_run_discovery_writes_expected_artifacts(tmp_path: Path):
    repo_root = tmp_path / "legacy-app"

    module_dir = repo_root / "modules" / "connect-id-user-list"
    (module_dir / "api").mkdir(parents=True)
    (module_dir / "ui").mkdir(parents=True)
    (module_dir / "tests").mkdir(parents=True)
    (module_dir / "module.yaml").write_text("name: connect-id-user-list\n", encoding="utf-8")
    (module_dir / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")
    (module_dir / "api" / "main.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/users')\n"
        "def list_users():\n"
        "    return []\n",
        encoding="utf-8",
    )
    (module_dir / "ui" / "page.ts").write_text("export const page = true\n", encoding="utf-8")
    (module_dir / "tests" / "test_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    frontend_pages = repo_root / "frontend" / "src" / "pages"
    frontend_pages.mkdir(parents=True)
    (frontend_pages / "connect-id-home.page.ts").write_text(
        "import { getUsers } from '../services/id.service';\n"
        "export const page = getUsers;\n",
        encoding="utf-8",
    )

    frontend_services = repo_root / "frontend" / "src" / "services"
    frontend_services.mkdir(parents=True)
    (frontend_services / "id.service.ts").write_text(
        "export async function getUsers() {\n"
        "  return fetch('/api/v3/identification/users');\n"
        "}\n",
        encoding="utf-8",
    )

    backend_routes = repo_root / "backend" / "api" / "routes" / "v3"
    backend_routes.mkdir(parents=True)
    (backend_routes / "identification.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(prefix='/api/v3/identification')\n"
        "@router.get('/users')\n"
        "def users():\n"
        "    return []\n",
        encoding="utf-8",
    )

    output_dir = repo_root / "reports" / "migration-discovery"
    payload = run_discovery(repo_root=repo_root, output_dir=output_dir, delegation_limit=4, top_services=2)

    assert payload["module_candidates"]
    assert payload["service_boundaries"]["frontend_modules"]
    assert payload["cqrs_pattern_clusters"]["rows"] == []
    assert payload["delegation_plan"]

    expected_files = [
        output_dir / "repository-profile.json",
        output_dir / "repository-profile.md",
        output_dir / "module-candidates.json",
        output_dir / "service-boundaries.json",
        output_dir / "cqrs-pattern-clusters.json",
        output_dir / "delegation-plan.generated.json",
        output_dir / "migration-discovery.summary.json",
        output_dir / "migration-discovery.summary.md",
    ]
    for path in expected_files:
        assert path.exists(), f"missing artifact: {path}"

    summary = json.loads((output_dir / "migration-discovery.summary.json").read_text(encoding="utf-8"))
    assert summary["counts"]["candidate_modules"] >= 1
    assert "python" in [row["name"] for row in summary["profile"]["languages"]]
    assert any(name.endswith("summary_md") for name in summary["artifacts"])
    assert "connect-id-user-list" in summary["top_candidates"]
