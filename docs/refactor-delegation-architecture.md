# Protogate Delegation Architecture - Refactor Notes

## Why previous migration felt incomplete

1. c2004 still contained too much module logic after iframe cutover.
2. Delegated frontend was not yet standardized as a TypeScript module model in protogate.
3. Migration steps were not automated from candidate detection to execution plan.

## Design principles for better delegation

1. One bounded module, one vertical slice in protogate.
2. Stable contracts first, handlers second, UI third.
3. Host app keeps navigation and auth/session bridge only.
4. Data ownership moves with the module.
5. Legacy code is archived only after parity gates pass.

## Dependency strategy

### Backend dependencies

1. Keep protogate runtime dependencies minimal and explicit in gateway requirements.
2. Isolate module-specific persistence/read model dependencies per slice.
3. Avoid importing legacy app internals directly into protogate handlers.

### Frontend dependencies

1. Keep delegated frontend dependencies inside protogate delegated apps.
2. Move duplicated cross-app TypeScript helpers to shared packages.
3. Version shared packages independently from app release cadence.

## Shared TypeScript package extraction model

1. Candidate discovery is produced in c2004 migration reports.
2. Shared package scaffolding is generated under c2004/packages.
3. Recommended initial package taxonomy:

- @semcod/ts-utils
- @semcod/ui-components
- @semcod/contracts-types

1. Current extracted CQRS modules in contracts-types:

- @semcod/contracts-types:cqrs-data-grid
- @semcod/contracts-types:reports-core
- @semcod/contracts-types:manager-core
- @semcod/contracts-types:scenario-core

1. Once stable, mirror or publish packages for protogate delegated frontend use.

## Delegation execution flow

1. Generate c2004 module candidates.
2. Generate protogate delegation plan from candidate report.
3. Pick top phase-1 module.
4. Implement contract, CQRS handlers, read model, delegated UI.
5. Flip c2004 route to iframe host.
6. Run bootstrap and smoke tests.
7. Archive legacy implementation.

## Operational scripts

1. c2004 side:

- scripts/detect_migration_candidates.py
- scripts/detect_shared_ts_packages.py
- scripts/run_arch_migration_discovery.sh
- scripts/scaffold_shared_ts_packages.py

1. protogate side:

- `scripts/legacy_bridge/generate_delegation_plan.py` – generates delegation plan from c2004 reports
- `scripts/legacy_bridge/delegation_plan.py` – shared blueprint model (runtime + docs)
- `gateway/delegation.py` – `DelegatedSlice` registry with health checks

## Runtime Slice Model

Each delegated slice is registered in `gateway/delegation.SLICE_REGISTRY`:

```python
DelegatedSlice(
    name="search",
    phase="phase-1",              # phase-1 | phase-2 | live
    backend="delegated",          # delegated | planned | legacy
    frontend="static",            # none | static | planned
    contract_paths=("contracts/search/v1/search.proto",),
    command_routes=("/commands/search/index",),
    query_routes=("/queries/search",),
    read_model_paths=("event_store.db", "search_index.db"),
    frontend_paths=("gateway/static/search_v2.html",),
    smoke_checks=("/health", "/queries/search?q=test"),
    transports=("http", "ws"),
)
```

### Health Endpoint Contract

Per-slice health available at `GET /health/modules/{slice}`:

```json
{
  "status": "ok | degraded",
  "missing_required": ["path1", "path2"],
  "contracts": [{"path": "...", "required": true, "exists": true}],
  "read_models": [...],
  "frontend_assets": [...]
}
```

## Governance checklist per module

1. Contract reviewed and versioned.
2. CQRS command and query paths defined.
3. Read model schema and rebuild strategy documented.
4. Data bootstrap script idempotent and logged.
5. Smoke test and rollback path validated.
6. Legacy module archived with traceable commit history.
