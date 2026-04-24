from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "ignore_dirs": [
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "coverage",
        "reports",
    ],
    "frontend": {
        "roots": ["frontend/src"],
        "extensions": [".ts", ".tsx", ".js", ".jsx"],
        "page_patterns": [
            "pages/**/*.page.ts",
            "pages/**/*.page.tsx",
            "**/*.page.ts",
            "**/*.page.tsx",
        ],
        "module_dir_names": ["modules"],
        "shared_dir_names": ["services", "utils", "shared", "components", "registry", "config"],
        "module_prefix_rules": [
            {"prefix": "connect-", "segments": 2},
        ],
        "alias_roots": {},
    },
    "backend": {
        "route_roots": ["backend/api/routes/v3"],
        "extensions": [".py"],
    },
    "api": {
        "path_regex": r"/api/v\d+(?:/[A-Za-z0-9._{}\-]+)+",
        "group_depth": 3,
    },
    "analysis": {
        "top_services": 4,
        "shared_modules": ["shared", "shell"],
    },
}
TS_IMPORT_RE = re.compile(
    r"(?:import|export)\s+(?:type\s+)?(?:[^;]*?\s+from\s+)?['\"](?P<spec>[^'\"]+)['\"]|import\(\s*['\"](?P<dynamic>[^'\"]+)['\"]\s*\)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class TsFile:
    path: Path
    rel: str
    module: str
    is_page: bool
    imports: tuple[str, ...]
    api_groups: tuple[str, ...]


@dataclass(frozen=True)
class PyRouteFile:
    path: Path
    rel: str
    route_group: str
    imports: tuple[str, ...]
    prefixes: tuple[str, ...]


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None:
        return DEFAULT_CONFIG
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config must be a JSON object")
    return deep_merge(DEFAULT_CONFIG, raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze service boundaries in a legacy repository")
    parser.add_argument("--repo-root", required=True, help="path to the project root to analyze")
    parser.add_argument("--config", help="optional JSON config path overriding discovery defaults")
    parser.add_argument("--output-dir", default="reports/service-boundaries", help="output directory, relative to repo root if not absolute")
    parser.add_argument("--basename", default="service-boundaries", help="basename for generated files")
    parser.add_argument("--top-services", type=int, help="override number of top service candidates to recommend")
    parser.add_argument("--stdout", action="store_true", help="print JSON payload to stdout instead of writing files")
    return parser.parse_args()


def is_ignored(path: Path, ignored_names: set[str]) -> bool:
    return any(part in ignored_names for part in path.parts)


def iter_files(root: Path, suffixes: tuple[str, ...], ignored_names: set[str]) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in suffixes and not is_ignored(path.relative_to(root), ignored_names)
    )


def strip_source_suffix(name: str) -> str:
    value = name
    for suffix in (".page.tsx", ".page.ts", ".test.tsx", ".test.ts", ".spec.tsx", ".spec.ts", ".tsx", ".ts", ".jsx", ".js"):
        if value.endswith(suffix):
            return value[: -len(suffix)]
    return value


def extract_prefixed_module(name: str, rules: list[dict[str, Any]]) -> str | None:
    normalized = strip_source_suffix(name).replace(".", "-")
    tokens = [token for token in normalized.split("-") if token]
    for rule in rules:
        prefix = str(rule.get("prefix", "")).strip()
        prefix_tokens = [token for token in prefix.strip("-").split("-") if token]
        if not prefix_tokens:
            continue
        if tokens[: len(prefix_tokens)] != prefix_tokens:
            continue
        segments = int(rule.get("segments", len(prefix_tokens) + 1))
        if len(tokens) >= segments:
            return "-".join(tokens[:segments])
    return None


def matches_page_pattern(rel: str, patterns: list[str]) -> bool:
    rel_path = PurePosixPath(rel)
    return any(rel_path.match(pattern) for pattern in patterns)


def detect_frontend_module(path: Path, root: Path, config: dict[str, Any]) -> str:
    rel = path.relative_to(root)
    module_dir_names = set(config["frontend"]["module_dir_names"])
    shared_dir_names = set(config["frontend"]["shared_dir_names"])
    for idx, part in enumerate(rel.parts):
        if part in module_dir_names and idx + 1 < len(rel.parts):
            candidate = rel.parts[idx + 1]
            if candidate.startswith("connect-"):
                return candidate
    from_name = extract_prefixed_module(rel.name, config["frontend"]["module_prefix_rules"])
    if from_name:
        return from_name
    if rel.parts and rel.parts[0] in shared_dir_names:
        return "shared"
    return "shell"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def resolve_candidate_file(path: Path, allowed_roots: list[Path]) -> Path | None:
    candidates = [
        path,
        path.with_suffix(".ts"),
        path.with_suffix(".tsx"),
        path.with_suffix(".js"),
        path.with_suffix(".jsx"),
        Path(str(path) + ".ts"),
        Path(str(path) + ".tsx"),
        Path(str(path) + ".js"),
        Path(str(path) + ".jsx"),
        path / "index.ts",
        path / "index.tsx",
        path / "index.js",
        path / "index.jsx",
    ]
    for candidate in candidates:
        if not candidate.exists() or not candidate.is_file():
            continue
        if any(candidate.is_relative_to(root) for root in allowed_roots):
            return candidate
    return None


def resolve_ts_import(current: Path, spec: str, workspace_root: Path, allowed_roots: list[Path], alias_roots: dict[str, str]) -> Path | None:
    if spec.startswith(("./", "../")):
        return resolve_candidate_file((current.parent / spec).resolve(), allowed_roots)
    for alias, target_root in sorted(alias_roots.items(), key=lambda item: len(item[0]), reverse=True):
        if spec == alias or spec.startswith(alias):
            suffix = spec[len(alias):].lstrip("/")
            return resolve_candidate_file((workspace_root / target_root / suffix).resolve(), allowed_roots)
    return None


def parse_ts_import_specs(source: str) -> list[str]:
    specs: list[str] = []
    for match in TS_IMPORT_RE.finditer(source):
        spec = match.group("spec") or match.group("dynamic")
        if spec:
            specs.append(spec)
    return specs


def normalize_api_group(path: str, group_depth: int) -> str:
    parts = [part for part in path.split("/") if part]
    if len(parts) >= group_depth:
        return "/" + "/".join(parts[:group_depth])
    return path


def extract_api_groups(source: str, api_pattern: re.Pattern[str], group_depth: int) -> set[str]:
    return {normalize_api_group(match, group_depth) for match in api_pattern.findall(source)}


def build_ts_index(workspace_root: Path, config: dict[str, Any], api_pattern: re.Pattern[str]) -> dict[str, TsFile]:
    frontend_roots = [(workspace_root / root).resolve() for root in config["frontend"]["roots"]]
    frontend_roots = [root for root in frontend_roots if root.exists()]
    ignored_names = set(config["ignore_dirs"])
    suffixes = tuple(config["frontend"]["extensions"])
    alias_roots = {str(alias): str(target) for alias, target in config["frontend"].get("alias_roots", {}).items()}
    result: dict[str, TsFile] = {}

    for root in frontend_roots:
        for path in iter_files(root, suffixes, ignored_names):
            rel_to_root = path.relative_to(root).as_posix()
            if rel_to_root.endswith((".test.ts", ".spec.ts", ".test.tsx", ".spec.tsx", ".test.js", ".spec.js")):
                continue
            source = read_text(path)
            imports = []
            for spec in parse_ts_import_specs(source):
                target = resolve_ts_import(path, spec, workspace_root, frontend_roots, alias_roots)
                if target is not None:
                    imports.append(target.relative_to(workspace_root).as_posix())
            rel = path.relative_to(workspace_root).as_posix()
            result[rel] = TsFile(
                path=path,
                rel=rel,
                module=detect_frontend_module(path, root, config),
                is_page=matches_page_pattern(rel_to_root, config["frontend"]["page_patterns"]),
                imports=tuple(sorted(set(imports))),
                api_groups=tuple(sorted(extract_api_groups(source, api_pattern, int(config["api"]["group_depth"])))),
            )
    return result


def const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def parse_router_prefixes(tree: ast.AST) -> list[str]:
    prefixes: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "APIRouter":
            for keyword in node.keywords:
                if keyword.arg == "prefix":
                    value = const_str(keyword.value)
                    if value is not None:
                        prefixes.append(value)
    return prefixes


def parse_python_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                imports.add("." * node.level + module)
            else:
                imports.add(module)
    return imports


def route_group_from_prefixes(rel_path: Path, prefixes: list[str]) -> str:
    for prefix in prefixes:
        parts = [part for part in prefix.split("/") if part]
        if len(parts) >= 3 and parts[0] == "api" and re.fullmatch(r"v\d+", parts[1]):
            return parts[2]
        if parts:
            return parts[0]
    if len(rel_path.parts) > 1:
        return rel_path.parts[0]
    return rel_path.stem.replace("_", "-")


def counter_rows(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(limit)]


def merge_named_rows(groups: list[dict[str, Any]], field: str, limit: int = 10) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for group in groups:
        for item in group.get(field, []):
            counter[item["name"]] += item["count"]
    return counter_rows(counter, limit)


def build_backend_index(workspace_root: Path, config: dict[str, Any]) -> dict[str, PyRouteFile]:
    route_roots = [(workspace_root / root).resolve() for root in config["backend"]["route_roots"]]
    route_roots = [root for root in route_roots if root.exists()]
    ignored_names = set(config["ignore_dirs"])
    suffixes = tuple(config["backend"]["extensions"])
    result: dict[str, PyRouteFile] = {}

    for root in route_roots:
        for path in iter_files(root, suffixes, ignored_names):
            source = read_text(path)
            try:
                tree = ast.parse(source)
            except SyntaxError:
                tree = ast.parse("")
            prefixes = parse_router_prefixes(tree)
            rel_path = path.relative_to(root)
            rel = path.relative_to(workspace_root).as_posix()
            result[rel] = PyRouteFile(
                path=path,
                rel=rel,
                route_group=route_group_from_prefixes(rel_path, prefixes),
                imports=tuple(sorted(parse_python_imports(tree))),
                prefixes=tuple(sorted(prefixes)),
            )
    return result


def backend_group_summary(index: dict[str, PyRouteFile]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    buckets: dict[str, list[PyRouteFile]] = defaultdict(list)
    for file in index.values():
        buckets[file.route_group].append(file)
    for group, files in sorted(buckets.items()):
        import_roots: Counter[str] = Counter()
        for file in files:
            for item in file.imports:
                clean = item.lstrip(".")
                if not clean:
                    continue
                import_roots[clean.split(".")[0]] += 1
        grouped[group] = {
            "group": group,
            "file_count": len(files),
            "files": [file.rel for file in files],
            "prefixes": sorted({prefix for file in files for prefix in file.prefixes}),
            "top_import_roots": counter_rows(import_roots),
        }
    return grouped


def transitive_closure(start: list[str], index: dict[str, TsFile]) -> set[str]:
    seen: set[str] = set()
    queue = deque(start)
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        for target in index[current].imports:
            if target in index and target not in seen:
                queue.append(target)
    return seen


def route_group_from_api_group(api_group: str) -> str | None:
    parts = [part for part in api_group.split("/") if part]
    if len(parts) >= 3 and parts[0] == "api" and re.fullmatch(r"v\d+", parts[1]):
        return parts[2]
    if parts:
        return parts[-1]
    return None


def service_slug(module: str) -> str:
    value = module.strip().replace("_", "-")
    if value.startswith("connect-"):
        return value.replace("connect-", "service-", 1)
    return value


def classify_delivery(iframe_score: int, cross_targets: int, backend_groups: int) -> str:
    if iframe_score >= 70 and cross_targets <= 2 and backend_groups <= 3:
        return "iframe-first"
    if iframe_score >= 50:
        return "shell-first"
    return "decompose-before-extract"


def companion_modules(module: str, module_rows: list[dict[str, Any]]) -> list[str]:
    companions = []
    prefix = f"{module}-"
    for row in module_rows:
        if row["module"] == module or row["module"] in {"shared", "shell"}:
            continue
        if row["module"].startswith(prefix) and row["module"] not in companions:
            companions.append(row["module"])
    return sorted(companions)


def choose_component_anchor(component_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {row["module"]: row for row in component_rows}
    route_groups = {group for row in component_rows for group in row["backend_route_groups"]}
    preferred_names = [
        "connect-config",
        "connect-data",
        "connect-id",
        "connect-scenario",
        "connect-test",
    ]
    for name in preferred_names:
        if name in by_name:
            if name == "connect-config" and "config" in route_groups:
                return by_name[name]
            if name == "connect-data" and "data" in route_groups:
                return by_name[name]
            if name == "connect-id" and ("identification" in route_groups or "auth" in route_groups):
                return by_name[name]
            if name == "connect-scenario":
                return by_name[name]
            if name == "connect-test":
                return by_name[name]
    return max(
        component_rows,
        key=lambda row: (row["extraction_priority"], row["page_count"], -len(row["cross_module_targets"]), row["module"]),
    )


def _build_eligible_modules(module_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Filter and index eligible modules for service component building."""
    return {
        row["module"]: row
        for row in module_rows
        if row["module"] not in {"shared", "shell"} and row["page_count"] > 0
    }


def _apply_merge_hints(
    eligible: dict[str, dict[str, Any]],
    merge_hints: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Apply union-find to merge modules based on hints."""
    parent = {name: name for name in eligible}

    def find(name: str) -> str:
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    def union(left: str, right: str) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for hint in merge_hints:
        if hint["left"] not in eligible or hint["right"] not in eligible:
            continue
        if hint["jaccard"] >= 0.65 and hint["cross_edges"] <= 2:
            union(hint["left"], hint["right"])

    components: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for name, row in eligible.items():
        components[find(name)].append(row)
    return components


def _determine_component_action(rows: list[dict[str, Any]], avg_iframe_score: int, cross_targets: list[str], route_groups: list[str]) -> str:
    """Determine the recommended action for a component."""
    if any(row["delivery_mode"] == "decompose-before-extract" for row in rows):
        return "decompose"
    elif avg_iframe_score >= 85 and not cross_targets and len(route_groups) <= 4:
        return "iframe-first"
    else:
        return "extract-service"


def _build_component_row(
    rows: list[dict[str, Any]],
    backend_groups: dict[str, dict[str, Any]],
    module_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a single service component row from module rows."""
    rows = sorted(rows, key=lambda row: row["module"])
    anchor = choose_component_anchor(rows)
    members = sorted(row["module"] for row in rows)
    route_groups = sorted({group for row in rows for group in row["backend_route_groups"]})
    backend_group_rows = [backend_groups[group] for group in route_groups if group in backend_groups]
    frontend_files = sorted({path for row in rows for path in row["owned_files"]})
    guardrail_files = sorted({path for row in rows for path in row["shared_dependency_files"]})
    backend_files = sorted({path for group in backend_group_rows for path in group["files"]})
    cross_targets = sorted({target for row in rows for target in row["cross_module_targets"] if target not in members})
    avg_iframe_score = round(sum(row["iframe_score"] for row in rows) / len(rows))
    action = _determine_component_action(rows, avg_iframe_score, cross_targets, route_groups)
    return {
        "service_slug": anchor["service_slug"],
        "anchor_module": anchor["module"],
        "members": members,
        "companion_modules": sorted({item for member in members for item in companion_modules(member, module_rows)} - set(members)),
        "member_count": len(members),
        "page_count": sum(row["page_count"] for row in rows),
        "frontend_file_count": len(frontend_files),
        "backend_route_groups": route_groups,
        "backend_route_file_count": len(backend_files),
        "cross_module_targets": cross_targets,
        "avg_iframe_score": avg_iframe_score,
        "delivery_mode": classify_delivery(avg_iframe_score, len(cross_targets), len(route_groups)),
        "action": action,
        "combined_priority": sum(row["extraction_priority"] for row in rows),
        "frontend_files": frontend_files,
        "frontend_guardrail_files": guardrail_files,
        "backend_files": backend_files,
        "backend_import_roots": merge_named_rows(backend_group_rows, "top_import_roots"),
    }


def build_service_components(
    module_rows: list[dict[str, Any]],
    merge_hints: list[dict[str, Any]],
    backend_groups: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    eligible = _build_eligible_modules(module_rows)
    components = _apply_merge_hints(eligible, merge_hints)

    result: list[dict[str, Any]] = []
    for rows in components.values():
        component_row = _build_component_row(rows, backend_groups, module_rows)
        result.append(component_row)
    result.sort(key=lambda item: (-item["combined_priority"], item["service_slug"]))
    return result


def select_execution_plan(service_components: list[dict[str, Any]], top_services: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_services: set[str] = set()

    def add(component: dict[str, Any]) -> None:
        if component["service_slug"] not in selected_services:
            selected.append(component)
            selected_services.add(component["service_slug"])

    prep_tracks = [component for component in service_components if component["action"] == "decompose" and component["page_count"] >= 5]
    prep_tracks.sort(key=lambda item: (-item["combined_priority"], item["service_slug"]))
    for component in prep_tracks[:1]:
        add(component)

    pilot_tracks = [
        component
        for component in service_components
        if component["action"] != "decompose" and component["avg_iframe_score"] >= 85 and not component["cross_module_targets"]
    ]
    pilot_tracks.sort(key=lambda item: (-item["combined_priority"], item["service_slug"]))
    for component in pilot_tracks[:2]:
        add(component)

    config_tracks = [
        component
        for component in service_components
        if "config" in component["backend_route_groups"]
    ]
    config_tracks.sort(key=lambda item: (-item["combined_priority"], item["service_slug"]))
    if config_tracks:
        add(config_tracks[0])

    data_tracks = [
        component
        for component in service_components
        if "data" in component["backend_route_groups"] and "config" not in component["backend_route_groups"]
    ]
    data_tracks.sort(key=lambda item: (-item["combined_priority"], item["service_slug"]))
    if data_tracks:
        add(data_tracks[0])

    fallback_tracks = [component for component in service_components if component["action"] != "decompose"]
    fallback_tracks.sort(key=lambda item: (-item["combined_priority"], item["service_slug"]))
    for component in fallback_tracks:
        if len([item for item in selected if item["action"] != "decompose"]) >= top_services:
            break
        add(component)

    plan: list[dict[str, Any]] = []
    service_phase = 1
    for component in selected:
        if component["action"] == "decompose":
            phase = "phase-0"
            goal = "decompose-before-extract"
        else:
            phase = f"phase-{service_phase}"
            service_phase += 1
            if component["action"] == "iframe-first":
                goal = "pilot-iframe-service"
            elif len(component["members"]) > 1:
                goal = "clustered-service-extraction"
            else:
                goal = "single-service-extraction"
        plan.append({"phase": phase, "goal": goal, **component})
    return plan


def build_target_structure(execution_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for track in execution_plan:
        service_root = f"services/{track['service_slug']}"
        result.append(
            {
                "service_slug": track["service_slug"],
                "phase": track["phase"],
                "paths": [
                    service_root,
                    f"{service_root}/frontend",
                    f"{service_root}/frontend/src",
                    f"{service_root}/backend",
                    f"{service_root}/backend/api/routes/v3",
                    f"{service_root}/docker",
                    f"{service_root}/migration",
                ],
                "legacy_frontend_sources": track["frontend_files"],
                "legacy_backend_sources": track["backend_files"],
            }
        )
    return result


def build_cleanup_checklist(execution_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for track in execution_plan:
        result.append(
            {
                "service_slug": track["service_slug"],
                "phase": track["phase"],
                "frontend_files_to_archive": track["frontend_files"],
                "backend_files_to_archive": track["backend_files"],
                "shared_guardrail_files": track["frontend_guardrail_files"],
                "companion_modules_to_review": track["companion_modules"],
            }
        )
    return result


def _build_module_index(ts_index: dict[str, TsFile]) -> tuple[dict[str, list[str]], Counter[tuple[str, str]]]:
    """Build module file index and cross-module edge counter."""
    files_by_module: dict[str, list[str]] = defaultdict(list)
    cross_edges: Counter[tuple[str, str]] = Counter()
    for rel, file in ts_index.items():
        files_by_module[file.module].append(rel)
        for target in file.imports:
            if target not in ts_index:
                continue
            target_module = ts_index[target].module
            if target_module != file.module:
                cross_edges[(file.module, target_module)] += 1
    return files_by_module, cross_edges


def _calculate_module_stats(
    module: str,
    owned_files: list[str],
    ts_index: dict[str, TsFile],
    backend_groups: dict[str, dict[str, Any]],
    cross_edges: Counter[tuple[str, str]],
    shared_modules: set[str],
) -> dict[str, Any]:
    """Calculate statistics for a single module."""
    closure = transitive_closure(owned_files, ts_index)
    reached_modules = Counter(ts_index[path].module for path in closure if ts_index[path].module != module)
    cross_targets = sorted(name for name in reached_modules if name not in shared_modules)
    shared_count = sum(count for name, count in reached_modules.items() if name in shared_modules)
    api_groups = sorted({group for path in closure for group in ts_index[path].api_groups if group.startswith("/api/")})
    direct_api_groups = sorted({group for path in owned_files for group in ts_index[path].api_groups if group.startswith("/api/")})
    route_group_hits = sorted({group for api_group in api_groups if (group := route_group_from_api_group(api_group))})
    matched_backend_groups = [backend_groups[group] for group in route_group_hits if group in backend_groups]
    page_count = sum(1 for path in owned_files if ts_index[path].is_page)
    cross_outgoing = sum(cross_edges[(module, target)] for target in cross_targets)
    iframe_score = max(
        0,
        min(
            100,
            62 + page_count * 3 + min(12, len(api_groups) * 4) - len(cross_targets) * 12 - cross_outgoing * 2 - max(0, shared_count - 20),
        ),
    )
    extraction_priority = max(0, page_count * 8 + len(route_group_hits) * 6 + iframe_score - len(cross_targets) * 10)
    delivery = classify_delivery(iframe_score, len(cross_targets), len(route_group_hits))
    return {
        "module": module,
        "service_slug": service_slug(module),
        "owned_file_count": len(owned_files),
        "page_count": page_count,
        "closure_file_count": len(closure),
        "direct_api_groups": direct_api_groups,
        "api_groups": api_groups,
        "backend_route_groups": route_group_hits,
        "backend_route_files": sorted({path for group in matched_backend_groups for path in group["files"]}),
        "backend_import_roots": merge_named_rows(matched_backend_groups, "top_import_roots"),
        "cross_module_targets": cross_targets,
        "cross_module_outgoing_edges": cross_outgoing,
        "shared_shell_dependency_count": shared_count,
        "iframe_score": iframe_score,
        "iframe_candidate": iframe_score >= 60 and len(cross_targets) <= 2 and len(route_group_hits) <= 3,
        "delivery_mode": delivery,
        "extraction_priority": extraction_priority,
        "owned_files": sorted(owned_files),
        "closure_files": sorted(closure),
        "shared_dependency_files": sorted(path for path in closure if ts_index[path].module in shared_modules),
    }


def _generate_merge_hints(
    ranked: list[dict[str, Any]],
    cross_edges: Counter[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Generate merge hints based on backend group overlap and cross edges."""
    merge_hints = []
    for left in ranked:
        for right in ranked:
            if left["module"] >= right["module"]:
                continue
            overlap = set(left["backend_route_groups"]) & set(right["backend_route_groups"])
            union = set(left["backend_route_groups"]) | set(right["backend_route_groups"])
            if not union:
                continue
            similarity = len(overlap) / len(union)
            cross = cross_edges[(left["module"], right["module"])] + cross_edges[(right["module"], left["module"])]
            if similarity >= 0.5 or cross >= 3:
                merge_hints.append(
                    {
                        "left": left["module"],
                        "right": right["module"],
                        "backend_group_overlap": sorted(overlap),
                        "jaccard": round(similarity, 3),
                        "cross_edges": cross,
                    }
                )
    merge_hints.sort(key=lambda item: (-item["jaccard"], -item["cross_edges"], item["left"], item["right"]))
    return merge_hints


def analyze_frontend_modules(ts_index: dict[str, TsFile], backend_index: dict[str, PyRouteFile], top_services: int, shared_modules: set[str]) -> dict[str, Any]:
    files_by_module, cross_edges = _build_module_index(ts_index)
    backend_groups = backend_group_summary(backend_index)
    
    module_rows: list[dict[str, Any]] = []
    for module, owned_files in sorted(files_by_module.items()):
        row = _calculate_module_stats(module, owned_files, ts_index, backend_groups, cross_edges, shared_modules)
        module_rows.append(row)

    ranked = [
        row
        for row in sorted(module_rows, key=lambda item: (-item["extraction_priority"], item["module"]))
        if row["module"] not in shared_modules and row["page_count"] > 0
    ]
    recommended = ranked[:top_services]

    merge_hints = _generate_merge_hints(ranked, cross_edges)

    service_components = build_service_components(module_rows, merge_hints, backend_groups)
    execution_plan = select_execution_plan(service_components, top_services)
    target_structure = build_target_structure(execution_plan)
    cleanup_checklist = build_cleanup_checklist(execution_plan)
    backend_usage = Counter(group for row in module_rows for group in row["backend_route_groups"])
    return {
        "frontend_modules": module_rows,
        "recommended_service_candidates": recommended,
        "merge_hints": merge_hints[:20],
        "service_components": service_components,
        "execution_plan": execution_plan,
        "target_structure": target_structure,
        "cleanup_checklist": cleanup_checklist,
        "backend_route_groups": list(backend_groups.values()),
        "summary": {
            "frontend_file_count": len(ts_index),
            "frontend_module_count": len(module_rows),
            "backend_route_file_count": len(backend_index),
            "backend_route_group_count": len(backend_groups),
            "top_backend_groups": [{"group": name, "count": count} for name, count in backend_usage.most_common(10)],
        },
    }


def _append_execution_plan_section(lines: list[str], payload: dict[str, Any]) -> None:
    lines.extend([
        "## Execution plan",
        "",
        "| Phase | Service | Members | Pages | Action | Backend groups | Cross targets | Avg iframe |",
        "| --- | --- | --- | ---: | --- | --- | --- | ---: |",
    ])
    for row in payload["execution_plan"]:
        lines.append(
            "| {phase} | {service_slug} | {members} | {page_count} | {action} | {groups} | {targets} | {iframe} |".format(
                phase=row["phase"],
                service_slug=row["service_slug"],
                members=", ".join(row["members"]),
                page_count=row["page_count"],
                action=row["action"],
                groups=", ".join(row["backend_route_groups"]) or "-",
                targets=", ".join(row["cross_module_targets"]) or "-",
                iframe=row["avg_iframe_score"],
            )
        )


def _append_service_components_section(lines: list[str], payload: dict[str, Any]) -> None:
    lines.extend([
        "",
        "## Suggested service components",
        "",
        "| Service | Anchor | Members | Pages | Backend groups | Companions | Priority |",
        "| --- | --- | --- | ---: | --- | --- | ---: |",
    ])
    for row in payload["service_components"]:
        lines.append(
            "| {service_slug} | {anchor} | {members} | {page_count} | {groups} | {companions} | {priority} |".format(
                service_slug=row["service_slug"],
                anchor=row["anchor_module"],
                members=", ".join(row["members"]),
                page_count=row["page_count"],
                groups=", ".join(row["backend_route_groups"]) or "-",
                companions=", ".join(row["companion_modules"]) or "-",
                priority=row["combined_priority"],
            )
        )


def _append_recommended_candidates_section(lines: list[str], payload: dict[str, Any]) -> None:
    lines.extend([
        "",
        "## Recommended service candidates",
        "",
        "| Module | Service | Pages | Backend groups | Cross-module targets | Iframe | Delivery | Priority |",
        "| --- | --- | ---: | --- | --- | ---: | --- | ---: |",
    ])
    for row in payload["recommended_service_candidates"]:
        lines.append(
            "| {module} | {service_slug} | {page_count} | {groups} | {targets} | {iframe_score} | {delivery_mode} | {priority} |".format(
                module=row["module"],
                service_slug=row["service_slug"],
                page_count=row["page_count"],
                groups=", ".join(row["backend_route_groups"]) or "-",
                targets=", ".join(row["cross_module_targets"]) or "-",
                iframe_score=row["iframe_score"],
                delivery_mode=row["delivery_mode"],
                priority=row["extraction_priority"],
            )
        )


def _append_merge_hints_section(lines: list[str], payload: dict[str, Any]) -> None:
    lines.extend([
        "",
        "## Merge hints",
        "",
        "| Left | Right | Backend overlap | Jaccard | Cross edges |",
        "| --- | --- | --- | ---: | ---: |",
    ])
    for row in payload["merge_hints"]:
        lines.append(
            f"| {row['left']} | {row['right']} | {', '.join(row['backend_group_overlap']) or '-'} | {row['jaccard']} | {row['cross_edges']} |"
        )


def _append_frontend_modules_section(lines: list[str], payload: dict[str, Any]) -> None:
    lines.extend([
        "",
        "## All frontend modules",
        "",
        "| Module | Pages | Files | Backend groups | Cross targets | Shared deps | Iframe |",
        "| --- | ---: | ---: | --- | --- | ---: | ---: |",
    ])
    for row in sorted(payload["frontend_modules"], key=lambda item: (-item["page_count"], item["module"])):
        lines.append(
            "| {module} | {page_count} | {owned_file_count} | {groups} | {targets} | {shared} | {iframe} |".format(
                module=row["module"],
                page_count=row["page_count"],
                owned_file_count=row["owned_file_count"],
                groups=", ".join(row["backend_route_groups"]) or "-",
                targets=", ".join(row["cross_module_targets"]) or "-",
                shared=row["shared_shell_dependency_count"],
                iframe=row["iframe_score"],
            )
        )


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Service Boundary Analysis",
        "",
        f"Generated at: {payload['meta']['generated_at']}",
        "",
    ]
    _append_execution_plan_section(lines, payload)
    _append_service_components_section(lines, payload)
    _append_recommended_candidates_section(lines, payload)
    _append_merge_hints_section(lines, payload)
    _append_frontend_modules_section(lines, payload)
    return "\n".join(lines) + "\n"


def build_execution_plan_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Service Extraction Execution Plan",
        "",
        f"Generated at: {payload['meta']['generated_at']}",
        "",
    ]
    for row in payload["execution_plan"]:
        lines.extend([
            f"## {row['phase']} - {row['service_slug']}",
            "",
            f"- Goal: `{row['goal']}`",
            f"- Members: {', '.join(row['members'])}",
            f"- Backend groups: {', '.join(row['backend_route_groups']) or '-'}",
            f"- Companion modules: {', '.join(row['companion_modules']) or '-'}",
            f"- Cross targets to cut: {', '.join(row['cross_module_targets']) or '-'}",
            f"- Avg iframe score: {row['avg_iframe_score']}",
            "",
            "### Frontend scope",
            "",
        ])
        for path in row["frontend_files"]:
            lines.append(f"- `{path}`")
        lines.extend([
            "",
            "### Backend scope",
            "",
        ])
        for path in row["backend_files"]:
            lines.append(f"- `{path}`")
        lines.extend([
            "",
            "### Shared guardrails",
            "",
        ])
        for path in row["frontend_guardrail_files"][:20]:
            lines.append(f"- `{path}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_target_structure_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Suggested Target Structure",
        "",
        f"Generated at: {payload['meta']['generated_at']}",
        "",
    ]
    for row in payload["target_structure"]:
        lines.extend([
            f"## {row['service_slug']} ({row['phase']})",
            "",
            "```text",
        ])
        lines.extend(row["paths"])
        lines.extend([
            "```",
            "",
            "### Legacy frontend sources",
            "",
        ])
        for path in row["legacy_frontend_sources"]:
            lines.append(f"- `{path}`")
        lines.extend([
            "",
            "### Legacy backend sources",
            "",
        ])
        for path in row["legacy_backend_sources"]:
            lines.append(f"- `{path}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_cleanup_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Legacy Cleanup Checklist",
        "",
        f"Generated at: {payload['meta']['generated_at']}",
        "",
    ]
    for row in payload["cleanup_checklist"]:
        lines.extend([
            f"## {row['service_slug']} ({row['phase']})",
            "",
            "### Frontend files to archive/remove after cutover",
            "",
        ])
        for path in row["frontend_files_to_archive"]:
            lines.append(f"- [ ] `{path}`")
        lines.extend([
            "",
            "### Backend files to archive/remove after cutover",
            "",
        ])
        for path in row["backend_files_to_archive"]:
            lines.append(f"- [ ] `{path}`")
        lines.extend([
            "",
            "### Shared guardrail files to audit before deletion",
            "",
        ])
        for path in row["shared_guardrail_files"][:20]:
            lines.append(f"- [ ] `{path}`")
        lines.extend([
            "",
            "### Companion modules to review",
            "",
        ])
        for path in row["companion_modules_to_review"]:
            lines.append(f"- [ ] `{path}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def _build_cqrs_endpoint_templates(service_data: dict[str, Any]) -> list[str]:
    backend_files = service_data.get("backend_files", [])
    route_files = [p for p in backend_files if "routes" in p and p.endswith(".py")]
    if not route_files:
        return []

    lines: list[str] = []
    lines.extend([
        "",
        "## CQRS Endpoint Templates (auto-generated)",
        "",
        "For each route file below, create the following CQRS pipeline components:",
        "",
    ])

    for path in route_files:
        basename = path.split("/")[-1].replace(".py", "")
        endpoint_name = basename.replace("_", " ").title().replace(" ", "")

        lines.extend([
            f"### `{path}`",
            "",
            f"**Endpoint base**: `/{basename}`",
            "",
            "#### CQRS Components to Create",
            "",
            "| Layer | File | Class |",
            "|-------|------|-------|",
            f"| Request DTO | `contracts/api/requests/{basename}.py` | `{endpoint_name}Request` |",
            f"| Response DTO | `contracts/api/responses/{basename}.py` | `{endpoint_name}Response` |",
            f"| Read Model | `contracts/read_models/{basename}.py` | `{endpoint_name}ReadModel` |",
            f"| Query | `application/queries/{basename}.py` | `Get{endpoint_name}Query` |",
            f"| Command | `application/commands/{basename}.py` | `Create{endpoint_name}Command` / `Delete{endpoint_name}Command` |",
            f"| Query Handler | `application/query_handlers/{basename}.py` | `Get{endpoint_name}Handler` |",
            f"| Command Handler | `application/command_handlers/{basename}.py` | `Create{endpoint_name}Handler` / `Delete{endpoint_name}Handler` |",
            "",
            "#### Pipeline Pattern",
            "",
            "```",
            "HTTP Request",
            "    ↓",
            f"{endpoint_name}Request (Pydantic)",
            "    ↓",
            f"Get{endpoint_name}Query / Create{endpoint_name}Command",
            "    ↓",
            "Handler (via bus)",
            "    ↓",
            f"{endpoint_name}ReadModel",
            "    ↓",
            f"{endpoint_name}Response",
            "    ↓",
            "HTTP Response",
            "```",
            "",
        ])

    return lines


def build_service_blueprint_markdown(service_slug: str, payload: dict[str, Any]) -> str:
    service_data = None
    for row in payload.get("execution_plan", []):
        if row.get("service_slug") == service_slug:
            service_data = row
            break
    if not service_data:
        return f"# Service Blueprint: {service_slug}\n\nNo data found in execution plan.\n"

    lines = [
        f"# {service_slug} Blueprint",
        "",
        f"Generated at: {payload['meta']['generated_at']}",
        "",
        "## Scope (from execution plan)",
        "",
        f"- **Phase**: {service_data.get('phase', 'unknown')}",
        f"- **Action**: {service_data.get('action', 'unknown')}",
        f"- **Members**: {', '.join(service_data.get('members', []))}",
        f"- **Backend route groups**: {', '.join(service_data.get('backend_route_groups', []))}",
    ]
    cross_targets = service_data.get("cross_module_targets", [])
    if cross_targets:
        lines.append(f"- **Cross targets to cut**: {', '.join(cross_targets)}")
    lines.extend([
        "",
        "## Target directory structure",
        "",
        "```text",
        f"services/{service_slug}/",
        f"services/{service_slug}/frontend/",
        f"services/{service_slug}/frontend/src/",
        f"services/{service_slug}/backend/",
        f"services/{service_slug}/backend/api/routes/v3/",
        f"services/{service_slug}/backend/application/commands/",
        f"services/{service_slug}/backend/application/queries/",
        f"services/{service_slug}/backend/application/command_handlers/",
        f"services/{service_slug}/backend/application/query_handlers/",
        f"services/{service_slug}/backend/application/events/",
        f"services/{service_slug}/backend/contracts/api/requests/",
        f"services/{service_slug}/backend/contracts/api/responses/",
        f"services/{service_slug}/backend/contracts/read_models/",
        f"services/{service_slug}/backend/domain/entities/",
        f"services/{service_slug}/backend/domain/value_objects/",
        f"services/{service_slug}/backend/domain/events/",
        f"services/{service_slug}/backend/infrastructure/persistence/",
        f"services/{service_slug}/docker/",
        f"services/{service_slug}/migration/",
        "```",
        "",
        "## Migration pattern: Request → Command/Query → Handler → ReadModel → Response",
        "",
        "For each endpoint in backend scope, apply the CQRS pipeline pattern:",
        "",
        "```",
        "HTTP Request",
        "    ↓",
        "Request DTO (Pydantic - transport validation)",
        "    ↓",
        "Command/Query (intent)",
        "    ↓",
        "Handler (via bus)",
        "    ↓",
        "ReadModel (projection)",
        "    ↓",
        "Response DTO (contract)",
        "    ↓",
        "HTTP Response",
        "```",
        "",
        "## Backend scope files to migrate",
        "",
    ])
    for path in service_data.get("backend_files", []):
        lines.append(f"- `{path}`")

    cqrs_templates = _build_cqrs_endpoint_templates(service_data)
    if cqrs_templates:
        lines.extend(cqrs_templates)

    lines.extend([
        "",
        "## Frontend scope files to migrate",
        "",
    ])
    for path in service_data.get("frontend_files", []):
        lines.append(f"- `{path}`")
    lines.extend([
        "",
        "## Priority order",
        "",
        "1. Extract routes to `backend/api/routes/v3/`",
        "2. Create request/response DTOs in `contracts/api/`",
        "3. Create commands/queries in `application/`",
        "4. Create handlers in `application/*_handlers/`",
        "5. Create read models in `contracts/read_models/`",
        "6. Domain entities in `domain/entities/` (if new)",
        "7. Wire everything via CQRS bus",
        "",
        f"## Notes for {service_slug}",
        "",
    ])
    action = service_data.get("action", "extract-service")
    if action == "iframe-first":
        lines.append("This is an iframe-first pilot service. Focus on hardening the API contract and keeping frontend/backend decoupled.")
    elif action == "extract-service":
        lines.append("This is a clustered service extraction. Pay attention to internal boundaries between merged modules.")
    elif action == "decompose":
        lines.append("This service requires internal decomposition first. Do not extract shared libraries until internal coupling is resolved.")
    lines.append("")
    return "\n".join(lines)


def build_cqrs_model_boundaries_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# CQRS Model Boundaries",
        "",
        f"Generated at: {payload['meta']['generated_at']}",
        "",
        "## Recommendation",
        "",
        "Yes — for this repository it is worth separating input and output models, but only at service boundaries and CQRS entry points.",
        "",
        "The current codebase already contains partial CQRS structure (`Command`, `Query`, `Event`, buses, handlers), but many handlers and routes still return raw dictionaries or mix transport models with domain/application models. The next migration steps should make those boundaries explicit.",
        "",
        "## What to separate",
        "",
        "### 1. API request models",
        "",
        "Use dedicated request DTOs for HTTP or iframe entry points. These models should only validate and normalize transport payloads.",
        "",
        "### 2. Command models",
        "",
        "Each write use case should have its own command model. Commands should describe intent, not HTTP shape or database shape.",
        "",
        "### 3. Query models",
        "",
        "Each read use case should have its own query model with explicit filters, pagination, and flags controlling projection depth.",
        "",
        "### 4. Read models / query result models",
        "",
        "Do not return raw `dict[str, Any]` from mature query handlers. Use dedicated read models / projection DTOs per screen, API, or consumer.",
        "",
        "### 5. API response models",
        "",
        "If an endpoint is public between extracted services, define explicit response DTOs instead of leaking internal read models or ORM-like structures.",
        "",
        "## What not to share blindly",
        "",
        "- ORM / SQLAlchemy models",
        "- Aggregate internals",
        "- service-private command payloads",
        "- service-private read projections",
        "- generic `dict[str, Any]` contracts hidden behind helper wrappers",
        "",
        "## What can become a shared library",
        "",
        "Share only stable cross-service primitives:",
        "",
        "- base CQRS abstractions (`BaseCommand`, `BaseQuery`, `BaseEvent`, `Result`, `ApiResponse`)",
        "- value objects and IDs",
        "- enums and small immutable reference DTOs",
        "- cross-service events and public contract DTOs",
        "- generated frontend/backend contract types for extracted services",
        "",
        "## Suggested per-service file layout",
        "",
        "```text",
        "application/commands/<use-case>.py",
        "application/queries/<use-case>.py",
        "application/command_handlers/<use-case>.py",
        "application/query_handlers/<use-case>.py",
        "application/events/<event>.py",
        "contracts/api/requests/<request>.py",
        "contracts/api/responses/<response>.py",
        "contracts/read_models/<projection>.py",
        "domain/entities/<entity>.py",
        "domain/value_objects/<value_object>.py",
        "domain/events/<event>.py",
        "```",
        "",
        "## Extraction rules",
        "",
        "- Map `HTTP request -> Request DTO -> Command/Query -> Handler -> Read model -> Response DTO`",
        "- Allow commands and queries to diverge from response shape",
        "- Keep response DTOs consumer-oriented, not persistence-oriented",
        "- If two services share a model, promote it only when it is versioned and contract-stable",
        "- Prefer generating frontend types from public contracts rather than importing backend internals",
        "",
        "## Service-by-service recommendation",
        "",
        "| Phase | Service | Recommendation | Why |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["execution_plan"]:
        if row["action"] == "decompose":
            recommendation = "Split internally first; do not extract shared model package yet"
            why = "High coupling and many cross-module targets; otherwise shared package would freeze monolith internals"
        elif row["action"] == "iframe-first":
            recommendation = "Strongly split request/command/query/read/response models now"
            why = "Good pilot candidate with low coupling; explicit contracts help iframe and service boundary hardening"
        elif len(row["members"]) > 1:
            recommendation = "Split commands and read models per capability before moving to shared contracts"
            why = "Clustered service will otherwise accumulate mixed payloads across modules"
        else:
            recommendation = "Split command/query from response models for new endpoints"
            why = "Single service extraction benefits from explicit pipelines and contract isolation"
        lines.append(
            "| {phase} | {service} | {recommendation} | {why} |".format(
                phase=row["phase"],
                service=row["service_slug"],
                recommendation=recommendation,
                why=why,
            )
        )
    lines.extend([
        "",
        "## Priority for this repository",
        "",
        "1. Replace raw query-handler dictionaries with named read models in pilot slices first.",
        "2. Keep API request models separate from command models in extracted services.",
        "3. Extract only stable cross-service primitives to shared libraries; keep service-private models local.",
        "4. Delay any shared package for decompose-phase services until internal coupling is reduced.",
        "",
        "## Decision summary",
        "",
        "For this monolith-to-services migration, separate input and output models where they define service contracts or CQRS pipelines. Do not globally split every internal function signature. Use explicit models at module boundaries, generate shared contract types only for stable public APIs, and keep domain-private models inside each extracted service.",
        "",
    ])
    return "\n".join(lines)


def analyze(repo_root: Path, config: dict[str, Any], top_services: int | None = None) -> dict[str, Any]:
    api_pattern = re.compile(str(config["api"]["path_regex"]))
    ts_index = build_ts_index(repo_root, config, api_pattern)
    backend_index = build_backend_index(repo_root, config)
    effective_top_services = top_services if top_services is not None else int(config["analysis"]["top_services"])
    payload = analyze_frontend_modules(ts_index, backend_index, effective_top_services, set(config["analysis"]["shared_modules"]))
    payload["meta"] = {
        "tool": "analyze-service-boundaries",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "config": config,
    }
    return payload


def write_outputs(output_dir: Path, basename: str, payload: dict[str, Any]) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{basename}.json"
    md_path = output_dir / f"{basename}.md"
    execution_md_path = output_dir / f"{basename}.execution-plan.md"
    structure_md_path = output_dir / f"{basename}.target-structure.md"
    cleanup_md_path = output_dir / f"{basename}.cleanup-checklist.md"
    cqrs_models_md_path = output_dir / f"{basename}.cqrs-model-boundaries.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(build_markdown(payload), encoding="utf-8")
    execution_md_path.write_text(build_execution_plan_markdown(payload), encoding="utf-8")
    structure_md_path.write_text(build_target_structure_markdown(payload), encoding="utf-8")
    cleanup_md_path.write_text(build_cleanup_markdown(payload), encoding="utf-8")
    cqrs_models_md_path.write_text(build_cqrs_model_boundaries_markdown(payload), encoding="utf-8")
    blueprint_paths: list[Path] = []
    for row in payload.get("execution_plan", []):
        service_slug = row.get("service_slug")
        if service_slug:
            blueprint_path = output_dir / f"{basename}.{service_slug}-blueprint.md"
            blueprint_path.write_text(build_service_blueprint_markdown(service_slug, payload), encoding="utf-8")
            blueprint_paths.append(blueprint_path)
    return [json_path, md_path, execution_md_path, structure_md_path, cleanup_md_path, cqrs_models_md_path] + blueprint_paths


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"[ERROR] repo root not found: {repo_root}")
        return 1

    config_path = Path(args.config).resolve() if args.config else None
    try:
        config = load_config(config_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] failed to load config: {exc}")
        return 1

    payload = analyze(repo_root, config, top_services=args.top_services)
    if args.stdout:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir
    written = write_outputs(output_dir, args.basename, payload)
    for path in written:
        print(f"[INFO] wrote {path}")
    print(f"[INFO] modules analyzed: {len(payload['frontend_modules'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
