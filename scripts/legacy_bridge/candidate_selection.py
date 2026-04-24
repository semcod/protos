from __future__ import annotations

from typing import Any


NON_DELEGABLE_MODULE_NAMES = {
    "backend",
    "frontend",
    "project",
    "site",
    "env",
    "shared",
    "shell",
}


def parse_score(row: dict[str, Any]) -> float:
    try:
        return float(row.get("score", 0.0))
    except (TypeError, ValueError):
        return 0.0


def get_candidate_exclusion_reasons(row: dict[str, Any]) -> list[str]:
    module = str(row.get("module", "")).strip()
    path = str(row.get("path", "")).strip()
    kind = str(row.get("kind", "")).strip().lower()
    extraction_target = str(row.get("extraction_target", "")).strip().lower()
    recommended_owner = str(row.get("recommended_owner", "")).strip().lower()
    service_candidate = row.get("service_candidate")

    reasons: list[str] = []
    if not module:
        reasons.append("missing module name")
    if module.startswith("."):
        reasons.append("hidden or temporary module name")
    if module in NON_DELEGABLE_MODULE_NAMES:
        reasons.append("technical or container-level module")
    if path.startswith("."):
        reasons.append("hidden or temporary path")
    if path in NON_DELEGABLE_MODULE_NAMES:
        reasons.append("technical or container-level path")
    if recommended_owner == "legacy-host":
        reasons.append("recommended owner is legacy-host")
    if extraction_target == "monolith-fragment":
        reasons.append("extraction target is monolith-fragment")
    if kind == "application" and module in {"backend", "frontend"}:
        reasons.append("top-level application should not be delegated as a slice")
    if isinstance(service_candidate, bool) and not service_candidate:
        if not (module.startswith("connect-") or path.startswith("modules/connect-")):
            reasons.append("not marked as service candidate and lacks delegated slice naming")

    return reasons


def is_delegable_candidate(row: dict[str, Any]) -> bool:
    return not get_candidate_exclusion_reasons(row)