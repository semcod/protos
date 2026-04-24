from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DelegatedSlice:
    name: str
    phase: str
    backend: str
    frontend: str
    contract_paths: tuple[str, ...] = ()
    command_routes: tuple[str, ...] = ()
    query_routes: tuple[str, ...] = ()
    read_model_paths: tuple[str, ...] = ()
    frontend_paths: tuple[str, ...] = ()
    smoke_checks: tuple[str, ...] = ()
    transports: tuple[str, ...] = ("http",)

    def _path_checks(
        self,
        root: Path,
        rel_paths: tuple[str, ...],
        required: bool,
    ) -> list[dict[str, Any]]:
        return [
            {
                "path": rel_path,
                "required": required,
                "exists": (root / rel_path).exists(),
            }
            for rel_path in rel_paths
        ]

    def health(self, root: Path | None = None) -> dict[str, Any]:
        root_path = root or REPO_ROOT
        frontend_required = self.frontend not in {"none", "planned"}
        contract_checks = self._path_checks(root_path, self.contract_paths, True)
        read_model_checks = self._path_checks(root_path, self.read_model_paths, True)
        frontend_checks = self._path_checks(root_path, self.frontend_paths, frontend_required)
        missing_required = [
            entry["path"]
            for entry in [*contract_checks, *read_model_checks, *frontend_checks]
            if entry["required"] and not entry["exists"]
        ]
        status = "ok" if not missing_required else "degraded"
        return {
            "status": status,
            "missing_required": missing_required,
            "contracts": contract_checks,
            "read_models": read_model_checks,
            "frontend_assets": frontend_checks,
        }

    def summary(self, root: Path | None = None) -> dict[str, Any]:
        health = self.health(root)
        return {
            "name": self.name,
            "phase": self.phase,
            "backend": self.backend,
            "frontend": self.frontend,
            "status": health["status"],
            "missing_required": health["missing_required"],
            "command_count": len(self.command_routes),
            "query_count": len(self.query_routes),
            "smoke_check_count": len(self.smoke_checks),
        }

    def detail(self, root: Path | None = None) -> dict[str, Any]:
        health = self.health(root)
        return {
            "name": self.name,
            "phase": self.phase,
            "backend": self.backend,
            "frontend": self.frontend,
            "transports": list(self.transports),
            "contract_paths": list(self.contract_paths),
            "command_routes": list(self.command_routes),
            "query_routes": list(self.query_routes),
            "read_model_paths": list(self.read_model_paths),
            "frontend_paths": list(self.frontend_paths),
            "smoke_checks": list(self.smoke_checks),
            "health": health,
        }


SLICE_REGISTRY: dict[str, DelegatedSlice] = {
    "search": DelegatedSlice(
        name="search",
        phase="phase-1",
        backend="delegated",
        frontend="static",
        contract_paths=("contracts/search/v1/search.proto",),
        command_routes=("/commands/search/index",),
        query_routes=("/queries/search",),
        read_model_paths=("event_store.db", "search_index.db"),
        frontend_paths=("gateway/static/search_v2.html",),
        smoke_checks=("/health", "/queries/search?q=test", "/commands/search/index"),
        transports=("http", "ws"),
    ),
    "user": DelegatedSlice(
        name="user",
        phase="live",
        backend="delegated",
        frontend="none",
        contract_paths=("contracts/user/v1/user.proto", "contracts/user/v2/user.proto"),
        command_routes=(
            "/commands/user/create",
            "/commands/user/dual-create",
            "/commands/user/{user_id}/change-email",
            "/commands/user/{user_id}/deactivate",
        ),
        query_routes=("/queries/user/{user_id}", "/events"),
        read_model_paths=("event_store.db", "legacy.db", "idempotency.db"),
        smoke_checks=("/health", "/events", "/queries/user/{user_id}"),
        transports=("http", "ws", "sse"),
    ),
}


def get_delegated_slice(name: str) -> DelegatedSlice | None:
    return SLICE_REGISTRY.get(name)


def list_delegated_slices(root: Path | None = None) -> list[dict[str, Any]]:
    return [
        delegated_slice.summary(root)
        for delegated_slice in sorted(SLICE_REGISTRY.values(), key=lambda item: item.name)
    ]


def get_delegation_health(root: Path | None = None) -> dict[str, Any]:
    slices = list_delegated_slices(root)
    ok_count = sum(1 for item in slices if item["status"] == "ok")
    degraded_count = sum(1 for item in slices if item["status"] != "ok")
    status = "ok" if degraded_count == 0 else "degraded"
    return {
        "status": status,
        "module_count": len(slices),
        "ok_count": ok_count,
        "degraded_count": degraded_count,
        "slices": slices,
    }
