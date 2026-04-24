from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")
_IGNORED_NAME_TOKENS = {"connect", "service", "module", "page", "pages", "frontend", "backend", "src", "app", "api", "v1", "v2", "v3", "ts", "py"}
_TOKEN_ALIASES = {
    "id": {"identification"},
    "identification": {"id"},
}


def infer_contexts_from_service_boundaries(
    service_boundaries: dict[str, Any],
    repo_root: Path,
    cqrs_root: str,
) -> list[str]:
    base_dir = repo_root / cqrs_root
    scored_contexts: dict[str, int] = {}

    for row in service_boundaries.get("frontend_modules", []):
        if not isinstance(row, dict):
            continue
        for group in _eligible_groups(row, base_dir):
            if _group_match_score(group, row) <= 0:
                continue
            score = _context_score(row, group, source="frontend")
            if score >= 55:
                scored_contexts[group] = max(scored_contexts.get(group, score), score)

    for row in service_boundaries.get("recommended_service_candidates", []):
        if not isinstance(row, dict):
            continue
        for group in _eligible_groups(row, base_dir):
            score = _context_score(row, group, source="recommended")
            if score >= 45:
                scored_contexts[group] = max(scored_contexts.get(group, score), score)

    if scored_contexts:
        return [
            name
            for name, _ in sorted(
                scored_contexts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]

    contexts: set[str] = set()
    for row in service_boundaries.get("recommended_service_candidates", []):
        if not isinstance(row, dict):
            continue
        for group in _eligible_groups(row, base_dir):
            contexts.add(group)
    return sorted(contexts)


def _eligible_groups(row: dict[str, Any], base_dir: Path) -> list[str]:
    groups = row.get("backend_route_groups", [])
    if not isinstance(groups, list):
        return []
    out: list[str] = []
    for group in groups:
        if not isinstance(group, str) or not group:
            continue
        if (base_dir / group).is_dir():
            out.append(group)
    return out


def _context_score(row: dict[str, Any], group: str, *, source: str) -> int:
    groups = row.get("backend_route_groups", [])
    route_group_count = len(groups) if isinstance(groups, list) and groups else 1
    cross_targets = row.get("cross_module_targets", [])
    cross_target_count = len(cross_targets) if isinstance(cross_targets, list) else 0
    page_count = int(row.get("page_count", 0) or 0)
    extraction_priority = int(row.get("extraction_priority", 0) or 0)

    score = 0
    if route_group_count == 1:
        score += 40
    elif route_group_count <= 3:
        score += 20
    elif route_group_count <= 6:
        score += 5
    else:
        score -= (route_group_count - 6) * 4

    if source == "frontend":
        if row.get("iframe_candidate") is True:
            score += 40
        delivery_mode = str(row.get("delivery_mode", ""))
        if delivery_mode == "iframe-first":
            score += 25
        elif delivery_mode == "extract-service":
            score += 5
    else:
        delivery_mode = str(row.get("delivery_mode", ""))
        if delivery_mode == "iframe-first":
            score += 10
        elif delivery_mode == "extract-service":
            score += 5
        score += min(15, extraction_priority // 40)

    if cross_target_count == 0:
        score += 10
    elif cross_target_count <= 2:
        score += 5
    else:
        score -= min(20, (cross_target_count - 2) * 5)

    if page_count > 0:
        score += min(10, page_count)

    score += _group_match_score(group, row)

    return score


def _group_match_score(group: str, row: dict[str, Any]) -> int:
    group_token = _normalize_token(group)
    tokens = _name_tokens(
        row.get("module"),
        row.get("service_slug"),
        row.get("anchor_module"),
        row.get("members"),
        row.get("companion_modules"),
    )
    if group_token in tokens:
        return 60
    for alias in _TOKEN_ALIASES.get(group_token, set()):
        if alias in tokens:
            return 60
    for token in tokens:
        if group_token in _TOKEN_ALIASES.get(token, set()):
            return 60
    if len(group_token) < 4:
        return 0
    for token in tokens:
        if len(token) < 4:
            continue
        if group_token in token or token in group_token:
            return 25
    return 0


def _name_tokens(*values: object) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        if isinstance(value, str):
            raw_values = [value]
        elif isinstance(value, (list, tuple, set)):
            raw_values = [item for item in value if isinstance(item, str)]
        else:
            continue
        for raw in raw_values:
            for part in _TOKEN_SPLIT_RE.split(raw.lower()):
                token = _normalize_token(part)
                if not token or token in _IGNORED_NAME_TOKENS:
                    continue
                tokens.add(token)
    return tokens


def _normalize_token(value: str) -> str:
    token = value.strip().lower()
    if not token:
        return ""
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and not token.endswith("ss") and len(token) > 4:
        return token[:-1]
    return token


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _default_swop_python(swop_repo: Path) -> Path:
    venv_python = swop_repo / "venv" / "bin" / "python"
    if venv_python.exists():
        return venv_python
    return Path(sys.executable)


def _swop_subprocess_script() -> str:
    return """
from __future__ import annotations
import json
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
output_dir = Path(sys.argv[2]).resolve()
swop_repo = Path(sys.argv[3]).resolve()
cqrs_root = sys.argv[4]
requested_contexts = json.loads(sys.argv[5])

sys.path.insert(0, str(swop_repo))

from swop.config import BoundedContextConfig, SwopConfig
from swop.manifests import generate_manifests
from swop.proto.generator import generate_proto_from_manifests
from swop.scan.scanner import scan_project

base_dir = repo_root / cqrs_root
resolved_contexts = []
missing_contexts = []
bounded_contexts = []

for context in requested_contexts:
    source_dir = base_dir / context
    if not source_dir.is_dir():
        missing_contexts.append(context)
        continue
    bounded_contexts.append(
        BoundedContextConfig(
            name=context,
            source=(Path(cqrs_root) / context).as_posix(),
        )
    )
    resolved_contexts.append(context)

manifests_dir = output_dir / "swop" / "manifests"
proto_dir = output_dir / "swop" / "proto"
manifests_dir.mkdir(parents=True, exist_ok=True)
proto_dir.mkdir(parents=True, exist_ok=True)

manifest_files = []
proto_files = []
warnings = []

def rel(path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)

if bounded_contexts:
    cfg = SwopConfig(
        project=f"{repo_root.name}-swop",
        source_roots=[cqrs_root],
        exclude=["**/__pycache__/**", "**/tests/**"],
        bounded_contexts=bounded_contexts,
        state_dir=".swop",
        config_path=repo_root / ".swop.generated.yaml",
    )
    report = scan_project(cfg, incremental=False, cache=None)
    manifest_result = generate_manifests(report, cfg, out_dir=manifests_dir)
    proto_result = generate_proto_from_manifests(manifests_dir, proto_dir)
    manifest_files = [rel(item.path) for item in getattr(manifest_result, "files", [])]
    proto_files = [rel(item.path) for item in getattr(proto_result, "files", [])]
    warnings = [str(item) for item in getattr(proto_result, "warnings", [])]

payload = {
    "cqrs_root": cqrs_root,
    "requested_contexts": requested_contexts,
    "resolved_contexts": resolved_contexts,
    "missing_contexts": missing_contexts,
    "manifests_dir": rel(output_dir / "swop" / "manifests"),
    "proto_dir": rel(output_dir / "swop" / "proto"),
    "manifest_files": manifest_files,
    "proto_files": proto_files,
    "warnings": warnings,
}
payload["summary"] = {
    "requested": len(requested_contexts),
    "resolved": len(resolved_contexts),
    "missing": len(missing_contexts),
    "manifest_files": len(manifest_files),
    "proto_files": len(proto_files),
    "warnings": len(warnings),
}
print(json.dumps(payload))
""".strip()


def run_swop_pipeline(
    repo_root: Path,
    output_dir: Path,
    swop_repo: Path,
    service_boundaries: dict[str, Any],
    cqrs_root: str = "backend/app/cqrs",
    contexts: Sequence[str] | None = None,
    swop_python: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    swop_repo = swop_repo.resolve()
    if not swop_repo.exists() or not swop_repo.is_dir():
        raise ValueError(f"swop repo not found: {swop_repo}")

    requested_contexts = sorted({item for item in (contexts or []) if item})
    if not requested_contexts:
        requested_contexts = infer_contexts_from_service_boundaries(service_boundaries, repo_root, cqrs_root)
    swop_python = (swop_python or _default_swop_python(swop_repo)).resolve()
    if not swop_python.exists():
        raise ValueError(f"swop python not found: {swop_python}")

    command = [
        str(swop_python),
        "-c",
        _swop_subprocess_script(),
        str(repo_root),
        str(output_dir),
        str(swop_repo),
        cqrs_root,
        json.dumps(requested_contexts),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "unknown swop integration failure").strip()
        raise RuntimeError(f"swop integration failed: {message}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"swop integration returned invalid JSON: {result.stdout!r}") from exc
    payload["swop_repo"] = str(swop_repo)
    payload["swop_python"] = str(swop_python)
    return payload


def render_swop_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Swop Integration",
        "",
        f"- CQRS root: `{payload.get('cqrs_root', '-')}`",
        f"- Requested contexts: `{', '.join(payload.get('requested_contexts', [])) or '-'}`",
        f"- Resolved contexts: `{', '.join(payload.get('resolved_contexts', [])) or '-'}`",
        f"- Missing contexts: `{', '.join(payload.get('missing_contexts', [])) or '-'}`",
        f"- Manifest dir: `{payload.get('manifests_dir', '-')}`",
        f"- Proto dir: `{payload.get('proto_dir', '-')}`",
        "",
        "## Generated manifest files",
        "",
    ]
    for item in payload.get("manifest_files", []):
        lines.append(f"- `{item}`")
    if not payload.get("manifest_files"):
        lines.append("- `none`")
    lines.extend([
        "",
        "## Generated proto files",
        "",
    ])
    for item in payload.get("proto_files", []):
        lines.append(f"- `{item}`")
    if not payload.get("proto_files"):
        lines.append("- `none`")
    lines.extend([
        "",
        "## Warnings",
        "",
    ])
    for item in payload.get("warnings", []):
        lines.append(f"- `{item}`")
    if not payload.get("warnings"):
        lines.append("- `none`")
    return "\n".join(lines) + "\n"


def render_swop_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
