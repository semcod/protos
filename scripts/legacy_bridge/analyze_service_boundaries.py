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
            return rel.parts[idx + 1]
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
    if value.startswith("service-"):
        return value
    if value.startswith("connect-"):
        return value.replace("connect-", "service-", 1)
    return f"service-{value}"


def classify_delivery(iframe_score: int, cross_targets: int, backend_groups: int) -> str:
    if iframe_score >= 70 and cross_targets <= 2 and backend_groups <= 3:
        return "iframe-first"
    if iframe_score >= 50:
        return "shell-first"
    return "decompose-before-extract"


def choose_component_anchor(component_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        component_rows,
        key=lambda row: (row["extraction_priority"], row["page_count"], -len(row["cross_module_targets"]), row["module"]),
    )


def build_service_components(
    module_rows: list[dict[str, Any]],
    merge_hints: list[dict[str, Any]],
    backend_groups: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    eligible = {
        row["module"]: row
        for row in module_rows
        if row["module"] not in {"shared", "shell"} and row["page_count"] > 0
    }
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

    result: list[dict[str, Any]] = []
    for rows in components.values():
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
        if any(row["delivery_mode"] == "decompose-before-extract" for row in rows):
            action = "decompose"
        elif avg_iframe_score >= 85 and not cross_targets and len(route_groups) <= 4:
            action = "iframe-first"
        else:
            action = "extract-service"
        result.append(
            {
                "service_slug": anchor["service_slug"],
                "anchor_module": anchor["module"],
                "members": members,
                "companion_modules": [],
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
        )
    result.sort(key=lambda item: (-item["combined_priority"], item["service_slug"]))
    return result


def select_execution_plan(service_components: list[dict[str, Any]], top_services: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_services: set[str] = set()

    def add(component: dict[str, Any]) -> None:
        if component["service_slug"] not in selected_services:
            selected.append(component)
            selected_services.add(component["service_slug"])

    prep_tracks = [component for component in service_components if component["action"] == "decompose" and component["page_count"] >= 3]
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
                    f"{service_root}/backend/routes",
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


def analyze_frontend_modules(ts_index: dict[str, TsFile], backend_index: dict[str, PyRouteFile], top_services: int, shared_modules: set[str]) -> dict[str, Any]:
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

    backend_groups = backend_group_summary(backend_index)
    module_rows: list[dict[str, Any]] = []
    for module, owned_files in sorted(files_by_module.items()):
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
        module_rows.append(
            {
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
        )

    ranked = [
        row
        for row in sorted(module_rows, key=lambda item: (-item["extraction_priority"], item["module"]))
        if row["module"] not in shared_modules and row["page_count"] > 0
    ]
    recommended = ranked[:top_services]

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


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Service Boundary Analysis",
        "",
        f"Generated at: {payload['meta']['generated_at']}",
        "",
        "## Execution plan",
        "",
        "| Phase | Service | Members | Pages | Action | Backend groups | Cross targets | Avg iframe |",
        "| --- | --- | --- | ---: | --- | --- | --- | ---: |",
    ]
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
    return "\n".join(lines) + "\n"


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
    output_dir.mkdir(parents=True, exist_ok=True)
    out_json = output_dir / f"{args.basename}.json"
    out_md = output_dir / f"{args.basename}.md"
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(build_markdown(payload), encoding="utf-8")
    print(f"[INFO] wrote {out_json}")
    print(f"[INFO] wrote {out_md}")
    print(f"[INFO] modules analyzed: {len(payload['frontend_modules'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
