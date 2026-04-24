from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from detect_migration_candidates import analyze_repository, get_service_candidates


def test_analyze_repository_identifies_delegated_slice_candidate(tmp_path: Path):
    repo_root = tmp_path / "c2004"
    module_dir = repo_root / "modules" / "connect-id-user-list"
    (module_dir / "api").mkdir(parents=True)
    (module_dir / "ui").mkdir(parents=True)
    (module_dir / "tests").mkdir(parents=True)
    (module_dir / "db").mkdir(parents=True)

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
    (module_dir / "ui" / "connect-id-user-list.page.ts").write_text(
        "import { renderPage } from './internal';\n"
        "export const page = renderPage();\n",
        encoding="utf-8",
    )
    (module_dir / "tests" / "test_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    rows = analyze_repository(repo_root)

    assert rows
    top = rows[0]
    assert top["module"] == "connect-id-user-list"
    assert top["path"] == "modules/connect-id-user-list"
    assert top["phase"] == "phase-1"
    assert top["service_candidate"] is True
    assert top["extraction_target"] == "delegated-slice"
    assert top["recommended_owner"] == "protos"


def test_get_service_candidates_filters_out_monolith_fragments(tmp_path: Path):
    repo_root = tmp_path / "c2004"

    strong = repo_root / "services" / "backend" / "fleet-data-manager"
    (strong / "app").mkdir(parents=True)
    (strong / "tests").mkdir(parents=True)
    (strong / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")
    (strong / "app" / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'ok': True}\n",
        encoding="utf-8",
    )
    (strong / "tests" / "test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    weak = repo_root / "backend"
    (weak / "src").mkdir(parents=True)
    (weak / "src" / "legacy.py").write_text(
        "import shared.utils\n"
        "import shared.core\n"
        "import shared.common\n"
        "def legacy():\n"
        "    return 1\n",
        encoding="utf-8",
    )

    rows = analyze_repository(repo_root)
    service_rows = get_service_candidates(rows)

    names = [row["module"] for row in service_rows]
    assert "fleet-data-manager" in names
    assert "backend" not in names
