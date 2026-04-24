# TODO - Protos Refactor Plan

## Objective

Turn protos into a reusable delegation platform where any bounded slice from legacy systems can be moved with minimal coupling.

## Current gaps observed

1. Delegated backend exists for selected slices, but frontend delegation is still partially hosted in c2004.
2. Migration workflow is not yet standardized as a repeatable pipeline for arbitrary modules.
3. Shared TypeScript and UI utilities are not extracted into reusable packages.
4. Module readiness scoring and delegation planning were missing automation.

## Recent progress

1. Delegation generator now enriches module rows with CQRS pattern and recommended shared types package from c2004 cluster report.
2. Shared contracts extraction waves implemented in c2004 include: cqrs-data-grid, reports-core, manager-core, scenario-core.

## Target architecture

1. Protos owns contracts, commands, queries, events, read models, and delegated UI runtime.
2. Legacy host (c2004) owns shell, auth/session bridge, and iframe routing only.
3. Each delegated module follows one vertical-slice template:

- contract
- command handlers
- query/read-model handlers
- bootstrap script
- delegated UI app
- smoke tests
- rollback switch

## Refactor roadmap

### Phase 1 - Platform hardening ✅

1. ~~Standardize module slice template in protos for new delegated modules.~~ ✅ `DelegatedSlice` registry in `gateway/delegation.py`
2. ~~Add strict event and command naming conventions.~~ ✅ Standard routes: `/commands/{slice}/*`, `/queries/{slice}/*`
3. ~~Introduce module-level health endpoints and smoke checks.~~ ✅ `/health/modules`, `/health/modules/{slice}`, `/delegation/slices`
4. ~~Add generated delegation plan workflow from c2004 candidate reports.~~ ✅ `generate_delegation_plan.py` with shared blueprint model

### Phase 2 - Delegated frontend model

1. Move delegated UI pages from static HTML prototypes to TypeScript microfrontends.
2. Define frontend packaging model for delegated slices.
3. Add shared package import policy and versioning rules.
4. Add compatibility contract between host shell and iframe apps.

### Phase 3 - Migration automation

1. Integrate readiness scoring from c2004 into protos planning scripts.
2. Add scripted checklist generation per module.
3. Add bootstrap validation scripts (data parity and smoke checks).
4. Add archive-ready gate to ensure safe legacy removal.

### Phase 4 - Scale-out

1. Migrate phase-1 low-coupling modules first.
2. Build shared packages from duplicated TypeScript code.
3. Apply same cutover pattern for medium and high complexity modules.

## Required improvements in protos codebase

1. Create dedicated delegated frontend workspace in protos for TypeScript apps.
2. Keep contracts independent from transport details.
3. Strengthen read model boundaries per module.
4. Add structured migration telemetry for each delegated slice.

## New scripts introduced

1. `scripts/legacy_bridge/delegation_plan.py`
   - Shared blueprint model: `build_slice_blueprint()`, `build_output_row()`, `render_markdown()`
   - Used by generator and available for runtime introspection

2. `scripts/legacy_bridge/generate_delegation_plan.py`
   - Generates `docs/delegation-plan.generated.md` and `.json` from c2004 module scoring report
   - Uses shared blueprint model for consistent runtime/docs alignment

## Runbook

1. Generate candidate report in c2004.
2. Run delegation plan generator in protos with c2004 report path and optional CQRS cluster map.
3. Pick top module from phase-1.
4. Implement full slice in protos.
5. Switch c2004 module to iframe host only.
6. Validate parity, then archive legacy implementation.

Example command:

python scripts/legacy_bridge/generate_delegation_plan.py \
  --input /home/tom/github/maskservice/c2004/migration/module-candidates.json \
  --clusters /home/tom/github/maskservice/c2004/migration/cqrs-pattern-clusters.json \
  --output-dir /home/tom/github/semcod/protos/docs \
  --limit 12
