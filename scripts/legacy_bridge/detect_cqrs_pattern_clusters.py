from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

TYPE_TOKEN_RE = re.compile(r"type:\s*'([^']+)'")
EVENT_SUFFIXES = (
    "Loaded",
    "Set",
    "Saved",
    "Deleted",
    "Completed",
    "Created",
    "Updated",
    "Filtered",
    "Toggled",
    "Tested",
    "Failed",
)

# Mapping of modules to their already-extracted shared type files
# This allows detection of CQRS patterns even in modules that have been partially refactored
SHARED_TYPE_FILE_BY_MODULE: dict[str, list[str]] = {
    "connect-config": [
        "connect-config.ts",
        "config-admin.ts",
        "config-system-core.ts",
        "config-flags-core.ts",
        "config-nav-core.ts",
        "config-template-core.ts",
        "config-access-core.ts",
        "config-module-core.ts",
    ],
    "connect-data": ["cqrs-data-grid.ts"],
    "connect-workshop": ["cqrs-data-grid.ts"],
    "connect-reports": ["reports-core.ts"],
    "connect-manager": ["manager-core.ts"],
    "connect-scenario": ["scenario-core.ts"],
    "connect-menu-tree": ["menu-tree-core.ts", "menu-tree-structure-core.ts", "menu-tree-mutation-core.ts"],
    "connect-devtools": ["devtools-core.ts", "devtools-panel-core.ts", "devtools-runs-core.ts"],
    "connect-id": ["id-core.ts", "id-navigation-core.ts", "id-users-core.ts"],
    "connect-menu-editor": ["menu-editor-core.ts", "menu-editor-storage-core.ts", "menu-editor-ops-core.ts"],
    "connect-test": [
        "test-orchestration-core.ts",
        "test-device-customer-core.ts",
        "test-assignment-core.ts",
        "test-protocol-core.ts",
    ],
}

DEFAULT_CONFIG: dict[str, Any] = {
    "cqrs": {
        "module_roots": ["frontend/src/modules"],
        "types_glob": "*/cqrs/types.ts",
        "patterns": [
            {
                "name": "data-grid-cqrs",
                "extraction_target": "@semcod/contracts-types:cqrs-data-grid",
                "commands": ["LoadSchema", "LoadRows", "SaveRow", "DeleteRow", "CreateRow", "BulkSave", "BulkDelete"],
                "events": ["SchemaLoaded", "RowsLoaded", "RowSaved", "RowDeleted", "RowCreated", "BulkSaveCompleted", "BulkDeleteCompleted"],
                "min_command_matches": 4,
                "min_event_matches": 4,
            },
            {
                "name": "config-admin-cqrs",
                "extraction_target": "@semcod/contracts-types:config-admin",
                "commands": ["LoadFlags", "LoadFlagCategories", "SaveFlag", "LoadNavOptions", "SaveNavOption", "LoadRoles", "LoadModules"],
                "events": ["FlagsLoaded", "FlagCategoriesLoaded", "FlagSaved", "NavOptionsLoaded", "NavOptionSaved", "RolesLoaded", "ModulesLoaded"],
                "min_command_matches": 3,
                "min_event_matches": 3,
            },
            {
                "name": "reports-filtering-cqrs",
                "extraction_target": "@semcod/contracts-types:reports-core",
                "commands": ["LoadProtocols", "LoadProtocolById", "FilterProtocols"],
                "events": ["ProtocolsLoaded", "ProtocolsFiltered", "ProtocolLoaded"],
                "min_command_matches": 2,
                "min_event_matches": 2,
            },
            {
                "name": "manager-library-workflow-cqrs",
                "extraction_target": "@semcod/contracts-types:manager-core",
                "commands": ["LoadLibrary", "LibraryAddItem", "LibraryDeleteItem", "LoadScenarios", "CreateScenario", "UpdateScenario", "DeleteScenario"],
                "events": ["LibraryLoaded", "LibraryItemAdded", "LibraryItemDeleted", "ScenariosLoaded", "ScenarioCreated", "ScenarioUpdated", "ScenarioDeleted"],
                "min_command_matches": 3,
                "min_event_matches": 3,
            },
            {
                "name": "scenario-builder-cqrs",
                "extraction_target": "@semcod/contracts-types:scenario-core",
                "commands": ["AddGoal", "DeleteGoal", "AddTask", "DeleteTask", "LoadScenarioById", "LoadScenarioByTitle", "UpdateScenarioDSL", "UpdateScenarioDEF", "UpdateScenarioContent", "SaveScenario"],
                "events": ["GoalAdded", "GoalDeleted", "TaskAdded", "TaskDeleted", "ScenarioLoaded", "ScenarioSaved", "ScenarioDSLUpdated", "ScenarioDEFUpdated", "ScenarioContentUpdated"],
                "min_command_matches": 4,
                "min_event_matches": 4,
            },
            {
                "name": "menu-tree-cqrs",
                "extraction_target": "@semcod/contracts-types:menu-tree-core",
                "commands": ["LoadMenus", "UpsertItem", "DeleteItem", "AddModulesToMenu", "EnsureModulesMenus", "ExportMigration"],
                "events": ["MenusRequested", "MenusLoaded", "MenusLoadFailed", "ItemUpserted", "ItemDeleted", "ModulesAdded", "ConfigCreated", "RouteMapped", "MigrationGenerated"],
                "min_command_matches": 4,
                "min_event_matches": 4,
            },
            {
                "name": "devtools-ops-cqrs",
                "extraction_target": "@semcod/contracts-types:devtools-core",
                "commands": ["SetDevtoolsPanel", "SetDevtoolsLogLevel", "LoadScripts", "RunScript", "GetRun", "GetRunLogs", "LoadRuns"],
                "events": ["DevtoolsPanelSet", "DevtoolsLogLevelSet", "ScriptsLoaded", "ScriptRunStarted", "RunStatusUpdated", "RunLogsLoaded", "RunsLoaded"],
                "min_command_matches": 5,
                "min_event_matches": 5,
            },
            {
                "name": "id-user-admin-cqrs",
                "extraction_target": "@semcod/contracts-types:id-core",
                "commands": ["SetIdSection", "SetIdMethod", "LoadUsers", "AddUser", "RemoveUser", "FilterUsers"],
                "events": ["IdSectionSet", "IdMethodSet", "UsersLoaded", "UserAdded", "UserRemoved", "UsersFiltered"],
                "min_command_matches": 4,
                "min_event_matches": 4,
            },
            {
                "name": "menu-editor-snapshots-cqrs",
                "extraction_target": "@semcod/contracts-types:menu-editor-core",
                "commands": ["SaveScreenshot", "LoadScreenshots", "DeleteScreenshot", "ClearAllScreenshots"],
                "events": ["ScreenshotSaved", "ScreenshotsLoaded", "ScreenshotDeleted", "ScreenshotsCleared"],
                "min_command_matches": 3,
                "min_event_matches": 3,
            },
            {
                "name": "test-orchestration-cqrs",
                "extraction_target": "@semcod/contracts-types:test-orchestration-core",
                "commands": ["SetTestMethod", "LoadDevices", "LoadCustomers", "LoadAssignments", "LoadScenarioById", "LoadScenarioByTitle", "LoadProtocols", "StartProtocol", "FinalizeProtocol", "LoadAuthUsers", "LoadTestScenarios", "LoadDslParamValues"],
                "events": ["TestMethodSet", "DevicesLoaded", "CustomersLoaded", "AssignmentsLoaded", "ScenarioLoaded", "ProtocolsLoaded", "ProtocolCreated", "ProtocolFinalized", "AuthUsersLoaded", "TestScenariosLoaded", "DslParamValuesLoaded"],
                "min_command_matches": 7,
                "min_event_matches": 7,
            },
        ],
        "custom_extraction_target": "@semcod/contracts-types:custom-per-module",
        "cluster_similarity_threshold": 0.5,
    }
}


@dataclass
class ModulePattern:
    module: str
    commands: list[str]
    events: list[str]
    command_count: int
    event_count: int
    pattern: str
    extraction_target: str
    priority_hint: str
    score: float | None
    phase: str | None
    cluster_members: list[str]


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


def normalize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if config is None:
        return DEFAULT_CONFIG
    return deep_merge(DEFAULT_CONFIG, config)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect CQRS pattern clusters across frontend modules")
    parser.add_argument("--repo-root", required=True, help="repository root to analyze")
    parser.add_argument("--config", help="optional JSON config path")
    parser.add_argument("--output-dir", default="reports/cqrs-pattern-clusters", help="output directory, relative to repo root if not absolute")
    parser.add_argument("--basename", default="cqrs-pattern-clusters", help="basename for generated artifacts")
    parser.add_argument("--candidates", help="optional path to module-candidates.json to enrich with score/phase")
    parser.add_argument("--stdout", action="store_true", help="print JSON to stdout")
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")
    except OSError:
        return ""


def load_candidate_scores(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in raw:
        if isinstance(row, dict) and isinstance(row.get("module"), str):
            out[str(row["module"])] = row
    return out


def module_from_types_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    parts = rel.parts
    try:
        idx = parts.index("modules")
        return parts[idx + 1]
    except Exception:
        return path.parent.parent.name


def split_tokens(tokens: list[str]) -> tuple[list[str], list[str]]:
    command_tokens = sorted({token for token in tokens if not token.endswith(EVENT_SUFFIXES)})
    event_tokens = sorted({token for token in tokens if token.endswith(EVENT_SUFFIXES) or token not in command_tokens})
    return command_tokens, event_tokens


def classify_pattern(commands: set[str], events: set[str], config: dict[str, Any]) -> tuple[str, str]:
    all_tokens = commands | events
    for pattern in config["cqrs"]["patterns"]:
        cmd_required = int(pattern.get("min_command_matches", 1))
        evt_required = int(pattern.get("min_event_matches", 1))
        command_matches = len(commands & set(pattern.get("commands", [])))
        event_matches = len(events & set(pattern.get("events", [])))

        # Some modules are now split into multiple shared files and re-export hubs.
        # In these cases token suffix heuristics can undercount command/event buckets,
        # so we also allow matching against the union token set.
        all_command_matches = len(all_tokens & set(pattern.get("commands", [])))
        all_event_matches = len(all_tokens & set(pattern.get("events", [])))

        if command_matches >= cmd_required and event_matches >= evt_required:
            return str(pattern["name"]), str(pattern["extraction_target"])
        if all_command_matches >= cmd_required and all_event_matches >= evt_required:
            return str(pattern["name"]), str(pattern["extraction_target"])
    return "custom-cqrs", str(config["cqrs"]["custom_extraction_target"])


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def assign_clusters(
    signature_map: dict[str, tuple[set[str], set[str]]],
    pattern_map: dict[str, str],
    threshold: float,
) -> dict[str, list[str]]:
    parent = {name: name for name in signature_map}

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

    names = sorted(signature_map)
    for idx, left in enumerate(names):
        left_tokens = signature_map[left][0] | signature_map[left][1]
        for right in names[idx + 1 :]:
            right_tokens = signature_map[right][0] | signature_map[right][1]
            same_pattern = pattern_map.get(left) == pattern_map.get(right) and pattern_map.get(left) != "custom-cqrs"
            if same_pattern or jaccard(left_tokens, right_tokens) >= threshold:
                union(left, right)

    grouped: dict[str, list[str]] = defaultdict(list)
    for name in names:
        grouped[find(name)].append(name)
    return {root: sorted(members) for root, members in grouped.items()}


def shared_tokens_for_module(repo_root: Path, module: str) -> list[str]:
    """Extract tokens from already-extracted shared type files for a module."""
    shared_files = SHARED_TYPE_FILE_BY_MODULE.get(module, [])
    if not shared_files:
        return []

    tokens: list[str] = []
    for shared_file in shared_files:
        shared_path = repo_root / "packages" / "contracts-types" / "src" / shared_file
        if not shared_path.exists():
            continue
        tokens.extend(TYPE_TOKEN_RE.findall(read_text(shared_path)))
    return tokens


def analyze_repository(repo_root: Path, config: dict[str, Any], candidate_scores: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    config = normalize_config(config)
    candidate_scores = candidate_scores or {}
    roots = [(repo_root / raw).resolve() for raw in config["cqrs"]["module_roots"]]
    roots = [root for root in roots if root.exists()]
    pattern = str(config["cqrs"]["types_glob"])
    signature_map: dict[str, tuple[set[str], set[str]]] = {}
    pattern_map: dict[str, str] = {}
    rows: list[ModulePattern] = []

    for root in roots:
        for types_path in sorted(root.glob(pattern)):
            module = module_from_types_path(types_path, repo_root)
            text = read_text(types_path)
            tokens = TYPE_TOKEN_RE.findall(text)
            # If module imports from shared types, extend tokens with shared type tokens
            if "@semcod/contracts-types" in text:
                tokens.extend(shared_tokens_for_module(repo_root, module))
            commands, events = split_tokens(tokens)
            command_set = set(commands)
            event_set = set(events)
            pattern_name, extraction_target = classify_pattern(command_set, event_set, config)

            score = None
            phase = None
            priority = "later"
            if module in candidate_scores:
                cand = candidate_scores[module]
                raw_score = cand.get("score")
                if isinstance(raw_score, (int, float)):
                    score = float(raw_score)
                raw_phase = cand.get("phase")
                if isinstance(raw_phase, str):
                    phase = raw_phase
                if phase == "phase-1":
                    priority = "early"
                elif phase == "phase-2":
                    priority = "middle"

            signature_map[module] = (command_set, event_set)
            pattern_map[module] = pattern_name
            rows.append(
                ModulePattern(
                    module=module,
                    commands=commands,
                    events=events,
                    command_count=len(commands),
                    event_count=len(events),
                    pattern=pattern_name,
                    extraction_target=extraction_target,
                    priority_hint=priority,
                    score=score,
                    phase=phase,
                    cluster_members=[],
                )
            )

    clusters = assign_clusters(signature_map, pattern_map, float(config["cqrs"]["cluster_similarity_threshold"]))
    by_module: dict[str, list[str]] = {}
    for members in clusters.values():
        for name in members:
            by_module[name] = members

    for row in rows:
        row.cluster_members = by_module.get(row.module, [row.module])

    rows.sort(key=lambda row: (row.priority_hint != "early", -(row.score or 0.0), row.module))
    return {
        "meta": {
            "tool": "detect-cqrs-pattern-clusters",
            "repo_root": str(repo_root),
            "module_roots": [str(root.relative_to(repo_root)) for root in roots],
            "config": config,
        },
        "rows": [asdict(row) for row in rows],
        "clusters": [
            {
                "cluster_id": root,
                "members": members,
                "size": len(members),
            }
            for root, members in sorted(clusters.items(), key=lambda item: (-len(item[1]), item[0]))
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    rows = payload["rows"]
    lines = [
        "# CQRS Pattern Clusters",
        "",
        "Generated by scripts/legacy_bridge/detect_cqrs_pattern_clusters.py.",
        "",
        "| module | pattern | extraction target | commands | events | score | phase | cluster |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        score_text = f"{float(row['score']):.2f}" if isinstance(row.get("score"), (float, int)) else "n/a"
        phase_text = str(row.get("phase") or "n/a")
        cluster = ", ".join(row.get("cluster_members", [])) or row["module"]
        lines.append(
            f"| {row['module']} | {row['pattern']} | {row['extraction_target']} | {row['command_count']} | {row['event_count']} | {score_text} | {phase_text} | {cluster} |"
        )
    lines.extend([
        "",
        "## Cluster Summary",
        "",
    ])
    for cluster in payload["clusters"]:
        lines.append(f"- {cluster['cluster_id']}: {', '.join(cluster['members'])}")
    if not payload["clusters"]:
        lines.append("- no cqrs clusters detected")
    lines.extend([
        "",
        "## Usage",
        "",
        "Use this report to choose the right shared CQRS type package or per-module extraction path before delegation.",
        "",
    ])
    return "\n".join(lines)


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

    candidates_path = Path(args.candidates).resolve() if args.candidates and Path(args.candidates).is_absolute() else repo_root / args.candidates if args.candidates else None
    payload = analyze_repository(repo_root, config, load_candidate_scores(candidates_path))

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
    out_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"[INFO] wrote {out_json}")
    print(f"[INFO] wrote {out_md}")
    print(f"[INFO] modules analyzed: {len(payload['rows'])}")
    print(f"[INFO] clusters detected: {len(payload['clusters'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
