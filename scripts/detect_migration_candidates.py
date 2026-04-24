from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
TEXT_SUFFIXES = SOURCE_SUFFIXES | {".json", ".yaml", ".yml", ".proto", ".toml", ".ini"}
ENTRYPOINT_FILES = {"main.py", "app.py", "__main__.py", "index.ts", "index.js", "server.ts", "server.js"}
CANDIDATE_MARKERS = {
    "module.yaml",
    "Dockerfile",
    "docker-compose.yml",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
}
IGNORE_DIRS = {
    ".git",
    ".idea",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "archive",
    "artifacts",
    "backups",
    "build",
    "coverage",
    "dist",
    "docs",
    "generated",
    "logs",
    "node_modules",
    "reports",
    "screenshots",
    "static",
    "test-results",
    "tmp",
    "venv",
}
ROOT_EXCLUDES = {
    "admin",
    "api",
    "archive",
    "contracts",
    "db",
    "docs",
    "hardware",
    "home",
    "how-to",
    "infra",
    "local",
    "logs",
    "make",
    "models",
    "modules",
    "monitor",
    "nginx",
    "pendrive",
    "quadlet",
    "redeploy",
    "reports",
    "scripts",
    "shared",
    "static",
    "tests",
    "test",
}
API_ROUTE_PATTERNS = (
    re.compile(r"@(router|app)\.(get|post|put|delete|patch)\b"),
    re.compile(r"\b(router|app)\.(get|post|put|delete|patch)\s*\("),
)
OUTBOUND_API_PATTERNS = (
    re.compile(r"\bfetch\s*\("),
    re.compile(r"\baxios\.(get|post|put|delete|patch)\b"),
    re.compile(r"\brequests\.(get|post|put|delete|patch)\b"),
    re.compile(r"\bhttpx\.(get|post|put|delete|patch)\b"),
)
PY_IMPORT_PATTERN = re.compile(r"^\s*(?:from\s+([A-Za-z0-9_\.]+)\s+import|import\s+([A-Za-z0-9_\.,\s]+))", re.MULTILINE)
TS_IMPORT_PATTERN = re.compile(r"(?:from\s+[\"']([^\"']+)[\"']|require\(\s*[\"']([^\"']+)[\"']\s*\))")
PAGE_IMPORT_PATTERN = re.compile(r"\.page\.(?:[jt]sx?)|/pages?/", re.IGNORECASE)
ENDPOINTS_YAML_PATTERN = re.compile(r"^\s*path\s*:", re.MULTILINE)

try:
    STDLIB_MODULES = set(sys.stdlib_module_names)
except AttributeError:
    STDLIB_MODULES = set()


@dataclass(frozen=True)
class CandidatePath:
    name: str
    path: Path
    kind: str


@dataclass(frozen=True)
class CandidateMetrics:
    module: str
    rel_path: str
    kind: str
    files: int
    lines: int
    cross_module_imports: int
    page_imports: int
    external_imports: int
    api_endpoints_used: int
    own_api_routes: int
    entrypoints: int
    shared_refs: int
    has_module_descriptor: bool
    has_docker: bool
    has_api_dir: bool
    has_ui_dir: bool
    has_tests: bool
    has_db_assets: bool


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def has_candidate_markers(path: Path) -> bool:
    if not path.is_dir():
        return False
    if any((path / marker).exists() for marker in CANDIDATE_MARKERS):
        return True
    return any((path / name).is_dir() for name in ("api", "app", "src", "ui")) or (path / "main.py").exists()


def infer_kind(path: Path) -> str:
    if (path / "module.yaml").exists():
        return "module"
    if "services" in path.parts:
        return "service"
    if (path / "package.json").exists() and not (path / "requirements.txt").exists() and not (path / "pyproject.toml").exists():
        return "frontend"
    if (path / "api").is_dir() or (path / "app").is_dir():
        return "application"
    return "component"


def discover_candidate_paths(repo_root: Path) -> list[CandidatePath]:
    candidates: list[CandidatePath] = []

    modules_dir = repo_root / "modules"
    if modules_dir.is_dir():
        for child in sorted(modules_dir.iterdir()):
            if child.is_dir() and child.name not in IGNORE_DIRS:
                candidates.append(CandidatePath(name=child.name, path=child, kind=infer_kind(child)))

    services_dir = repo_root / "services"
    if services_dir.is_dir():
        for child in sorted(services_dir.iterdir()):
            if not child.is_dir() or child.name in IGNORE_DIRS:
                continue
            if has_candidate_markers(child):
                candidates.append(CandidatePath(name=child.name, path=child, kind=infer_kind(child)))
                continue
            for nested in sorted(child.iterdir()):
                if nested.is_dir() and nested.name not in IGNORE_DIRS and has_candidate_markers(nested):
                    candidates.append(CandidatePath(name=nested.name, path=nested, kind=infer_kind(nested)))

    for child in sorted(repo_root.iterdir()):
        if not child.is_dir() or child.name in IGNORE_DIRS or child.name in ROOT_EXCLUDES:
            continue
        if has_candidate_markers(child):
            candidates.append(CandidatePath(name=child.name, path=child, kind=infer_kind(child)))

    unique: dict[Path, CandidatePath] = {}
    for candidate in candidates:
        unique[candidate.path.resolve()] = candidate
    return sorted(unique.values(), key=lambda item: item.path.as_posix())


def iter_files(path: Path) -> Iterable[Path]:
    for current_root, dir_names, file_names in path.walk():
        dir_names[:] = [name for name in dir_names if name not in IGNORE_DIRS]
        for file_name in file_names:
            file_path = current_root / file_name
            if file_name in CANDIDATE_MARKERS or file_name in ENTRYPOINT_FILES or file_path.suffix in TEXT_SUFFIXES:
                yield file_path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def extract_python_imports(content: str) -> list[str]:
    imports: list[str] = []
    for match in PY_IMPORT_PATTERN.finditer(content):
        from_import = match.group(1)
        plain_import = match.group(2)
        if from_import:
            imports.append(from_import)
            continue
        if plain_import:
            parts = [part.strip() for part in plain_import.split(",") if part.strip()]
            imports.extend(parts)
    return imports


def extract_ts_imports(content: str) -> list[str]:
    imports: list[str] = []
    for match in TS_IMPORT_PATTERN.finditer(content):
        value = match.group(1) or match.group(2)
        if value:
            imports.append(value)
    return imports


def import_tokens(specifier: str) -> set[str]:
    pieces = re.split(r"[^A-Za-z0-9]+", specifier)
    return {normalize_token(piece) for piece in pieces if piece}


def count_api_routes(path: Path, content: str) -> int:
    if path.name == "endpoints.yaml":
        return len(ENDPOINTS_YAML_PATTERN.findall(content))
    return sum(len(pattern.findall(content)) for pattern in API_ROUTE_PATTERNS)


def count_outbound_api_calls(content: str) -> int:
    return sum(len(pattern.findall(content)) for pattern in OUTBOUND_API_PATTERNS)


def analyze_candidate(candidate: CandidatePath, all_candidates: list[CandidatePath], top_level_names: set[str]) -> CandidateMetrics:
    current_alias = normalize_token(candidate.name)
    other_aliases = {normalize_token(item.name) for item in all_candidates if item.name != candidate.name}
    normalized_top_level_names = {normalize_token(name) for name in top_level_names}
    files = 0
    lines = 0
    cross_module_imports = 0
    page_imports = 0
    external_imports = 0
    api_endpoints_used = 0
    own_api_routes = 0
    entrypoints = 0
    shared_refs = 0

    has_module_descriptor = (candidate.path / "module.yaml").exists()
    has_docker = (candidate.path / "Dockerfile").exists() or (candidate.path / "docker-compose.yml").exists()
    has_api_dir = any((candidate.path / name).is_dir() for name in ("api", "app"))
    has_ui_dir = any((candidate.path / name).is_dir() for name in ("ui", "src", "frontend"))
    has_tests = any((candidate.path / name).is_dir() for name in ("tests", "test"))
    has_db_assets = any((candidate.path / name).is_dir() for name in ("db", "alembic", "migrations"))

    for file_path in iter_files(candidate.path):
        content = read_text(file_path)
        if not content:
            continue
        files += 1
        lines += sum(1 for _ in content.splitlines())
        if file_path.name in ENTRYPOINT_FILES:
            entrypoints += 1
        if file_path.suffix in SOURCE_SUFFIXES or file_path.name == "endpoints.yaml":
            own_api_routes += count_api_routes(file_path, content)
            api_endpoints_used += count_outbound_api_calls(content)
            page_imports += len(PAGE_IMPORT_PATTERN.findall(content))
        imports: list[str] = []
        if file_path.suffix == ".py":
            imports = extract_python_imports(content)
        elif file_path.suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            imports = extract_ts_imports(content)
        for specifier in imports:
            tokens = import_tokens(specifier)
            if not tokens:
                continue
            if any(token in {"shared", "common", "core", "utils"} for token in tokens):
                shared_refs += 1
            if any(token in other_aliases for token in tokens):
                cross_module_imports += 1
                continue
            if specifier.startswith((".", "/", "@/", "~/")):
                continue
            first = specifier.split(".", 1)[0].split("/", 1)[0]
            first_token = normalize_token(first)
            if first_token == current_alias or first_token in normalized_top_level_names:
                continue
            if file_path.suffix == ".py" and first in STDLIB_MODULES:
                continue
            external_imports += 1

    return CandidateMetrics(
        module=candidate.name,
        rel_path=candidate.path.name,
        kind=candidate.kind,
        files=files,
        lines=lines,
        cross_module_imports=cross_module_imports,
        page_imports=page_imports,
        external_imports=external_imports,
        api_endpoints_used=api_endpoints_used,
        own_api_routes=own_api_routes,
        entrypoints=entrypoints,
        shared_refs=shared_refs,
        has_module_descriptor=has_module_descriptor,
        has_docker=has_docker,
        has_api_dir=has_api_dir,
        has_ui_dir=has_ui_dir,
        has_tests=has_tests,
        has_db_assets=has_db_assets,
    )


def score_migration_candidate(metrics: CandidateMetrics) -> tuple[float, str, str, list[str]]:
    score = 55.0
    if metrics.has_module_descriptor:
        score += 14.0
    if metrics.has_api_dir:
        score += 8.0
    if metrics.has_ui_dir:
        score += 8.0
    if metrics.has_tests:
        score += 5.0
    if metrics.has_docker:
        score += 4.0
    if metrics.entrypoints == 1:
        score += 2.0
    elif metrics.entrypoints > 1:
        score -= min(6.0, float(metrics.entrypoints - 1))
    score -= min(28.0, metrics.cross_module_imports * 8.0)
    score -= min(18.0, metrics.api_endpoints_used * 4.0)
    score -= min(16.0, metrics.shared_refs * 3.0)
    score -= min(18.0, metrics.external_imports * 1.5)
    score -= min(12.0, max(0, metrics.files - 12) * 1.0)
    score -= min(20.0, max(0, metrics.lines - 1200) / 120.0)
    score = round(max(0.0, min(100.0, score)), 2)

    if metrics.lines <= 1200 and metrics.cross_module_imports <= 1 and metrics.api_endpoints_used <= 1:
        effort = "low"
    elif metrics.lines <= 3500 and metrics.cross_module_imports <= 4:
        effort = "medium"
    else:
        effort = "high"

    if score >= 75.0:
        phase = "phase-1"
    elif score >= 55.0:
        phase = "phase-2"
    else:
        phase = "phase-3"

    reasons = [
        f"cross-module imports: {metrics.cross_module_imports}",
        f"page imports: {metrics.page_imports}",
        f"external imports: {metrics.external_imports}",
        f"api endpoints used: {metrics.api_endpoints_used}",
        f"files: {metrics.files}",
        f"lines: {metrics.lines}",
    ]
    return score, phase, effort, reasons


def classify_extraction_target(metrics: CandidateMetrics) -> tuple[str, float, list[str]]:
    service_score = 35.0
    reasons: list[str] = []

    if metrics.has_docker:
        service_score += 15.0
        reasons.append("has docker packaging")
    if metrics.has_api_dir:
        service_score += 15.0
        reasons.append("has dedicated api/app directory")
    if metrics.has_ui_dir and metrics.has_api_dir:
        service_score += 10.0
        reasons.append("has vertical api+ui structure")
    if metrics.has_db_assets:
        service_score += 10.0
        reasons.append("owns db or migration assets")
    if metrics.own_api_routes > 0:
        service_score += 10.0
        reasons.append("exposes own API routes")
    if metrics.has_tests:
        service_score += 5.0
        reasons.append("has local tests")
    if metrics.entrypoints > 0:
        service_score += 5.0
        reasons.append("has executable entrypoint")

    service_score -= min(25.0, metrics.cross_module_imports * 7.0)
    service_score -= min(12.0, metrics.shared_refs * 3.0)
    service_score = round(max(0.0, min(100.0, service_score)), 2)

    if metrics.kind == "module" and metrics.has_api_dir and metrics.has_ui_dir:
        target = "delegated-slice"
    elif metrics.kind in {"service", "application"} and metrics.has_api_dir and metrics.own_api_routes > 0:
        target = "standalone-service"
    elif metrics.has_ui_dir and not metrics.has_api_dir:
        target = "frontend-microfrontend"
    elif metrics.shared_refs >= 3 and metrics.entrypoints == 0:
        target = "shared-package"
    else:
        target = "monolith-fragment"

    return target, service_score, reasons


def build_output_row(metrics: CandidateMetrics) -> dict[str, object]:
    score, phase, effort, reasons = score_migration_candidate(metrics)
    extraction_target, service_score, service_reasons = classify_extraction_target(metrics)
    return {
        "module": metrics.module,
        "path": metrics.rel_path,
        "kind": metrics.kind,
        "files": metrics.files,
        "lines": metrics.lines,
        "cross_module_imports": metrics.cross_module_imports,
        "page_imports": metrics.page_imports,
        "external_imports": metrics.external_imports,
        "api_endpoints_used": metrics.api_endpoints_used,
        "own_api_routes": metrics.own_api_routes,
        "entrypoints": metrics.entrypoints,
        "shared_refs": metrics.shared_refs,
        "score": score,
        "phase": phase,
        "effort": effort,
        "reasons": reasons,
        "service_candidate": service_score >= 70.0,
        "service_score": service_score,
        "extraction_target": extraction_target,
        "service_reasons": service_reasons,
        "has_module_descriptor": metrics.has_module_descriptor,
        "has_docker": metrics.has_docker,
        "has_api_dir": metrics.has_api_dir,
        "has_ui_dir": metrics.has_ui_dir,
        "has_tests": metrics.has_tests,
        "has_db_assets": metrics.has_db_assets,
        "recommended_owner": "protos" if extraction_target in {"delegated-slice", "standalone-service", "frontend-microfrontend"} else "legacy-host",
    }


def analyze_repository(repo_root: Path) -> list[dict[str, object]]:
    repo_root = repo_root.resolve()
    candidates = discover_candidate_paths(repo_root)
    top_level_names = {path.name for path in repo_root.iterdir() if path.is_dir()}
    outputs = []
    for candidate in candidates:
        metrics = analyze_candidate(candidate, candidates, top_level_names)
        metrics = CandidateMetrics(
            **{**metrics.__dict__, "rel_path": candidate.path.relative_to(repo_root).as_posix()},
        )
        outputs.append(build_output_row(metrics))
    outputs.sort(key=lambda row: (float(row["score"]), float(row["service_score"])), reverse=True)
    return outputs


def get_service_candidates(rows: list[dict[str, object]], min_service_score: float = 70.0) -> list[dict[str, object]]:
    filtered = [
        row
        for row in rows
        if bool(row.get("service_candidate")) or float(row.get("service_score", 0.0)) >= min_service_score
    ]
    filtered.sort(key=lambda row: (float(row["service_score"]), float(row["score"])), reverse=True)
    return filtered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect migration and service extraction candidates in a legacy project")
    parser.add_argument("--repo-root", required=True, help="path to the project root to analyze")
    parser.add_argument("--output", default="-", help="output JSON file path or '-' for stdout")
    parser.add_argument("--limit", type=int, default=20, help="limit number of returned candidates")
    parser.add_argument("--services-only", action="store_true", help="return only candidates suitable for service extraction")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"[ERROR] repo root not found: {repo_root}")
        return 1

    rows = analyze_repository(repo_root)
    if args.services_only:
        rows = get_service_candidates(rows)
    rows = rows[: args.limit]
    payload = json.dumps(rows, indent=2, ensure_ascii=False) + "\n"
    if args.output == "-":
        print(payload, end="")
        return 0

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload, encoding="utf-8")
    print(f"[INFO] wrote {output_path}")
    print(f"[INFO] candidates: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
