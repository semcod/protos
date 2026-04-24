from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from legacy_bridge.run_arch_migration_discovery import run_discovery
from legacy_bridge.swop_integration import infer_contexts_from_service_boundaries, run_swop_pipeline


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_stub_swop_repo(root: Path) -> Path:
    swop_root = root / "stub-swop"
    _write(swop_root / "swop" / "__init__.py", "")
    _write(
        swop_root / "swop" / "config.py",
        "from dataclasses import dataclass\n"
        "from pathlib import Path\n"
        "\n"
        "@dataclass\n"
        "class BoundedContextConfig:\n"
        "    name: str\n"
        "    source: str\n"
        "\n"
        "@dataclass\n"
        "class SwopConfig:\n"
        "    project: str\n"
        "    source_roots: list[str]\n"
        "    exclude: list[str]\n"
        "    bounded_contexts: list[BoundedContextConfig]\n"
        "    state_dir: str\n"
        "    config_path: Path\n",
    )
    _write(
        swop_root / "swop" / "scan" / "__init__.py",
        "",
    )
    _write(
        swop_root / "swop" / "scan" / "scanner.py",
        "def scan_project(cfg, incremental=False, cache=None):\n"
        "    return {'contexts': [ctx.name for ctx in cfg.bounded_contexts]}\n",
    )
    _write(
        swop_root / "swop" / "manifests.py",
        "from dataclasses import dataclass\n"
        "from pathlib import Path\n"
        "\n"
        "@dataclass\n"
        "class _ManifestFile:\n"
        "    path: Path\n"
        "\n"
        "@dataclass\n"
        "class _ManifestResult:\n"
        "    files: list[_ManifestFile]\n"
        "\n"
        "def generate_manifests(report, cfg, out_dir):\n"
        "    files = []\n"
        "    for ctx in cfg.bounded_contexts:\n"
        "        target = Path(out_dir) / ctx.name / 'queries.yml'\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        target.write_text('queries: []\\n', encoding='utf-8')\n"
        "        files.append(_ManifestFile(path=target))\n"
        "    return _ManifestResult(files=files)\n",
    )
    _write(
        swop_root / "swop" / "proto" / "__init__.py",
        "",
    )
    _write(
        swop_root / "swop" / "proto" / "generator.py",
        "from dataclasses import dataclass\n"
        "from pathlib import Path\n"
        "\n"
        "@dataclass\n"
        "class _ProtoFile:\n"
        "    path: Path\n"
        "\n"
        "@dataclass\n"
        "class _ProtoResult:\n"
        "    files: list[_ProtoFile]\n"
        "    warnings: list[str]\n"
        "\n"
        "def generate_proto_from_manifests(manifests_dir, out_dir):\n"
        "    files = []\n"
        "    base = Path(manifests_dir)\n"
        "    for context_dir in sorted(path for path in base.iterdir() if path.is_dir()):\n"
        "        target = Path(out_dir) / context_dir.name / 'v1' / f'{context_dir.name}.proto'\n"
        "        target.parent.mkdir(parents=True, exist_ok=True)\n"
        "        target.write_text('syntax = \"proto3\";\\n', encoding='utf-8')\n"
        "        files.append(_ProtoFile(path=target))\n"
        "    return _ProtoResult(files=files, warnings=[])\n",
    )
    return swop_root


def _create_sample_legacy_repo(repo_root: Path) -> None:
    module_dir = repo_root / "modules" / "connect-id-user-list"
    (module_dir / "api").mkdir(parents=True)
    (module_dir / "ui").mkdir(parents=True)
    (module_dir / "module.yaml").write_text("name: connect-id-user-list\n", encoding="utf-8")
    (module_dir / "api" / "main.py").write_text("def list_users():\n    return []\n", encoding="utf-8")
    (module_dir / "ui" / "page.ts").write_text("export const page = true\n", encoding="utf-8")

    frontend_pages = repo_root / "frontend" / "src" / "pages"
    frontend_pages.mkdir(parents=True)
    (frontend_pages / "connect-id-home.page.ts").write_text(
        "export const page = true\n",
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

    cqrs_dir = repo_root / "backend" / "app" / "cqrs" / "identification"
    cqrs_dir.mkdir(parents=True)
    (cqrs_dir / "queries.py").write_text("class IdentifyQuery:\n    value: str\n", encoding="utf-8")


def test_infer_contexts_from_service_boundaries_prefers_focused_matches(tmp_path: Path):
    repo_root = tmp_path / "legacy-app"
    cqrs_root = repo_root / "backend" / "app" / "cqrs"
    for name in ["events", "identification", "logs", "menu", "registry", "sensors"]:
        (cqrs_root / name).mkdir(parents=True, exist_ok=True)

    payload = {
        "frontend_modules": [
            {
                "module": "connect-id",
                "service_slug": "service-id",
                "backend_route_groups": ["identification"],
                "cross_module_targets": [],
                "page_count": 2,
                "iframe_candidate": True,
                "delivery_mode": "iframe-first",
                "extraction_priority": 120,
            },
            {
                "module": "connect-menu",
                "service_slug": "service-menu",
                "backend_route_groups": ["menu", "logs", "events"],
                "cross_module_targets": ["shell"],
                "page_count": 1,
                "iframe_candidate": False,
                "delivery_mode": "extract-service",
                "extraction_priority": 160,
            },
        ],
        "recommended_service_candidates": [
            {
                "module": "connect-config",
                "service_slug": "service-config",
                "backend_route_groups": ["events", "identification", "logs", "menu", "registry", "sensors"],
                "cross_module_targets": ["connect-menu", "connect-id", "connect-font"],
                "page_count": 34,
                "delivery_mode": "decompose-before-extract",
                "extraction_priority": 456,
            },
            {
                "module": "connect-menu",
                "service_slug": "service-menu",
                "backend_route_groups": ["menu", "logs", "events"],
                "cross_module_targets": ["shell"],
                "page_count": 1,
                "delivery_mode": "extract-service",
                "extraction_priority": 160,
            },
        ],
    }

    contexts = infer_contexts_from_service_boundaries(payload, repo_root, "backend/app/cqrs")

    assert contexts == ["identification", "menu"]


def test_run_swop_pipeline_auto_detects_contexts_without_explicit_list(tmp_path: Path):
    repo_root = tmp_path / "legacy-app"
    cqrs_root = repo_root / "backend" / "app" / "cqrs"
    for name in ["events", "identification", "logs", "menu", "registry", "sensors"]:
        context_dir = cqrs_root / name
        context_dir.mkdir(parents=True, exist_ok=True)
        (context_dir / "queries.py").write_text(f"class {name.title()}Query:\n    value: str\n", encoding="utf-8")

    service_boundaries = {
        "frontend_modules": [
            {
                "module": "connect-id",
                "service_slug": "service-id",
                "backend_route_groups": ["identification"],
                "cross_module_targets": [],
                "page_count": 2,
                "iframe_candidate": True,
                "delivery_mode": "iframe-first",
                "extraction_priority": 120,
            },
            {
                "module": "connect-menu",
                "service_slug": "service-menu",
                "backend_route_groups": ["menu", "logs", "events"],
                "cross_module_targets": ["shell"],
                "page_count": 1,
                "iframe_candidate": False,
                "delivery_mode": "extract-service",
                "extraction_priority": 160,
            },
        ],
        "recommended_service_candidates": [
            {
                "module": "connect-config",
                "service_slug": "service-config",
                "backend_route_groups": ["events", "identification", "logs", "menu", "registry", "sensors"],
                "cross_module_targets": ["connect-menu", "connect-id", "connect-font"],
                "page_count": 34,
                "delivery_mode": "decompose-before-extract",
                "extraction_priority": 456,
            },
            {
                "module": "connect-menu",
                "service_slug": "service-menu",
                "backend_route_groups": ["menu", "logs", "events"],
                "cross_module_targets": ["shell"],
                "page_count": 1,
                "delivery_mode": "extract-service",
                "extraction_priority": 160,
            },
        ],
    }

    swop_repo = _create_stub_swop_repo(tmp_path)
    output_dir = repo_root / "reports" / "migration-discovery"

    payload = run_swop_pipeline(
        repo_root=repo_root,
        output_dir=output_dir,
        swop_repo=swop_repo,
        service_boundaries=service_boundaries,
        swop_python=Path(sys.executable),
    )

    assert payload["requested_contexts"] == ["identification", "menu"]
    assert payload["resolved_contexts"] == ["identification", "menu"]
    assert payload["summary"]["proto_files"] == 2
    assert (output_dir / "swop" / "proto" / "identification" / "v1" / "identification.proto").exists()
    assert (output_dir / "swop" / "proto" / "menu" / "v1" / "menu.proto").exists()


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


def test_run_discovery_can_run_optional_swop_pipeline(tmp_path: Path):
    repo_root = tmp_path / "legacy-app"
    _create_sample_legacy_repo(repo_root)

    swop_repo = _create_stub_swop_repo(tmp_path)
    output_dir = repo_root / "reports" / "migration-discovery"

    payload = run_discovery(
        repo_root=repo_root,
        output_dir=output_dir,
        delegation_limit=4,
        top_services=2,
        swop_repo=swop_repo,
        swop_contexts=["identification"],
    )

    assert payload["swop"] is not None
    assert payload["swop"]["resolved_contexts"] == ["identification"]
    assert payload["swop"]["summary"]["proto_files"] == 1
    assert (output_dir / "swop-integration.json").exists()
    assert (output_dir / "swop-integration.md").exists()
    assert (output_dir / "swop" / "proto" / "identification" / "v1" / "identification.proto").exists()

    summary = json.loads((output_dir / "migration-discovery.summary.json").read_text(encoding="utf-8"))
    assert summary["counts"]["swop_contexts"] == 1
    assert summary["counts"]["swop_proto_files"] == 1
    assert summary["top_swop_contexts"] == ["identification"]
    assert "swop_json" in summary["artifacts"]


def test_installed_protogate_cli_runs_discovery_pipeline(tmp_path: Path):
    repo_root = tmp_path / "legacy-app"
    _create_sample_legacy_repo(repo_root)

    swop_repo = _create_stub_swop_repo(tmp_path)
    output_dir = repo_root / "reports" / "cli-discovery"
    project_root = Path(__file__).resolve().parent.parent
    venv_dir = tmp_path / "pkg-venv"

    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    python_bin = venv_dir / "bin" / "python"
    cli_bin = venv_dir / "bin" / "protogate"

    subprocess.run(
        [str(python_bin), "-m", "pip", "install", "--no-deps", "-e", str(project_root)],
        check=True,
    )

    completed = subprocess.run(
        [
            str(cli_bin),
            "discovery",
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--delegation-limit",
            "4",
            "--top-services",
            "2",
            "--swop-repo",
            str(swop_repo),
            "--swop-context",
            "identification",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "[INFO] wrote discovery artifacts" in completed.stdout
    assert (output_dir / "migration-discovery.summary.json").exists()
    assert (output_dir / "swop-integration.json").exists()
    assert (output_dir / "swop" / "proto" / "identification" / "v1" / "identification.proto").exists()

    summary = json.loads((output_dir / "migration-discovery.summary.json").read_text(encoding="utf-8"))
    assert summary["counts"]["swop_contexts"] == 1
    assert summary["counts"]["swop_proto_files"] == 1
    assert summary["top_swop_contexts"] == ["identification"]
