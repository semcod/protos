# TODO - Protogate Refactor Plan

## Objective

Turn protogate into a reusable delegation platform where any bounded slice from legacy systems can be moved with minimal coupling.

## Current gaps observed

1. Delegated backend exists for selected slices, but frontend delegation is still partially hosted in c2004.
2. Migration workflow is not yet standardized as a repeatable pipeline for arbitrary modules.
3. Shared TypeScript and UI utilities are not extracted into reusable packages.
4. Module readiness scoring and delegation planning were missing automation.

## Recent progress

1. Delegation generator now enriches module rows with CQRS pattern and recommended shared types package from c2004 cluster report.
2. Shared contracts extraction waves implemented in c2004 include: cqrs-data-grid, reports-core, manager-core, scenario-core.

## Target architecture

1. Protogate owns contracts, commands, queries, events, read models, and delegated UI runtime.
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

1. ~~Standardize module slice template in protogate for new delegated modules.~~ ✅ `DelegatedSlice` registry in `gateway/delegation.py`
2. ~~Add strict event and command naming conventions.~~ ✅ Standard routes: `/commands/{slice}/*`, `/queries/{slice}/*`
3. ~~Introduce module-level health endpoints and smoke checks.~~ ✅ `/health/modules`, `/health/modules/{slice}`, `/delegation/slices`
4. ~~Add generated delegation plan workflow from c2004 candidate reports.~~ ✅ `generate_delegation_plan.py` with shared blueprint model

### Phase 2 - Delegated frontend model

1. Move delegated UI pages from static HTML prototypes to TypeScript microfrontends.
2. Define frontend packaging model for delegated slices.
3. Add shared package import policy and versioning rules.
4. Add compatibility contract between host shell and iframe apps.

### Phase 3 - Migration automation

1. Integrate readiness scoring from c2004 into protogate planning scripts.
2. Add scripted checklist generation per module.
3. Add bootstrap validation scripts (data parity and smoke checks).
4. Add archive-ready gate to ensure safe legacy removal.

### Phase 4 - Scale-out

1. Migrate phase-1 low-coupling modules first.
2. Build shared packages from duplicated TypeScript code.
3. Apply same cutover pattern for medium and high complexity modules.

## Required improvements in protogate codebase

1. Create dedicated delegated frontend workspace in protogate for TypeScript apps.
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
2. Run delegation plan generator in protogate with c2004 report path and optional CQRS cluster map.
3. Pick top module from phase-1.
4. Implement full slice in protogate.
5. Switch c2004 module to iframe host only.
6. Validate parity, then archive legacy implementation.

Example command:

python scripts/legacy_bridge/generate_delegation_plan.py \
  --input /home/tom/github/maskservice/c2004/migration/module-candidates.json \
  --clusters /home/tom/github/maskservice/c2004/migration/cqrs-pattern-clusters.json \
  --output-dir /home/tom/github/semcod/protos/docs \
  --limit 12

## Discovered

- Integrate directional subset check and warnings into the delegation/schema registry workflow
- Add documentation and integration tests for the --cross-check-pydantic CLI flag
- Expose and document migration analysis CLI commands in protogate (migration analysis workflow)
- Track schema registry conflict resolution and vector clock support; add v2 proto handling
- Add proto pipeline steps for CQRS event store and incremental generation into workflows and release automation

## Protogen / Protogate - Refactor Plan (na bazie ostatnich zmian)

### Why now

1. Ostatnie poprawki generatora TS pokazały typowe ryzyka: dryf typow (np. brakujace enumy), aliasy DTO niespójne z interfejsami runtime oraz rozjazd wielu kopii wygenerowanych plikow.
2. Te same klasy problemow beda wracac w kolejnych modulach, jesli codegen nie dostanie warstwy kontraktowej i walidacji po generacji.

### Phase A - Stabilize output contract (high priority)

1. Dodac profil generacji (`strict`, `compat`) dla `ts-from-python`:
   - `strict`: bez aliasow legacy, tylko canonical interfaces.
   - `compat`: generuje aliasy/projekcje (`*Dto`) dla starszych frontendow.
2. Dodac jawny manifest wejscia generatora:
   - enumy,
   - DTO,
   - commands/events,
   - custom raw sections.
3. Wymusic walidacje referencji symboli podczas renderu:
   - jesli interfejs uzywa typu, ktory nie jest wygenerowany ani zdefiniowany w raw section, generator zwraca blad.

### Phase B - Multi-target and drift prevention (high priority)

1. Dodac natywne wsparcie wielu targetow w CLI `protogate codegen ts-from-python`:
   - jeden przebieg,
   - ta sama tresc,
   - atomowy zapis do N lokalizacji.
2. Dodac tryb `--check` (bez zapisu):
   - porownuje aktualne pliki z wynikiem generatora,
   - zwraca non-zero gdy jest drift.
3. Dodac tryb `--write-report`:
   - raportuje, ktore symbole zostaly dodane/usuniete/zmienione.

### Phase C - Type safety and compatibility layer (medium priority)

1. Dodac opcjonalna sekcje `DTO projections` jako first-class feature emitera (zamiast recznych blokow stringowych).
2. Dodac mapowanie nazw canonical <-> legacy (np. `Device` <-> `DeviceDto`) w konfigu generatora.
3. Dodac policy checks dla problematycznych wzorcow TS:
   - zakaz `interface X extends SomeType['nested']` w output contracts,
   - preferencja explicit shape dla loading state i podobnych struktur.

### Phase D - Verification gates in workflow (high priority)

1. Dodac `make codegen-verify` w protos:
   - uruchamia generator w `--check`,
   - odpala minimalny `tsc --noEmit` na fixture workspace.
2. Dodac testy snapshot/golden dla `protogate/codegen/typescript.py`:
   - enumy,
   - optional/nullable,
   - union,
   - dataclass defaults,
   - alias/projection generation.
3. Dodac test e2e: Python models -> generated TS -> compile check.

### Phase E - CLI and DX cleanup (medium priority)

1. Ujednolicic komendy codegen pod jednym namespace (np. `protogate codegen ts`).
2. Dodac `--verbose` i czytelne summary (ile enums/interfaces/targets).
3. Dodac dokument `docs/protogate-codegen-hardening.md`:
   - profile,
   - check mode,
   - typowe bledy i ich naprawa,
   - rekomendowany pipeline CI.

### Definition of Done

1. Brak dryfu miedzy targetami TS przy uruchomieniu `--check`.
2. Wykrywanie brakujacych symboli na etapie generatora, nie dopiero w `tsc`.
3. Minimum 1 workflow CI, ktory blokuje merge przy niespojnym codegen.
4. Testy golden dla TypeScriptEmitter przechodza lokalnie i w CI.

### Proposed execution order

1. Phase A
2. Phase B
3. Phase D
4. Phase C
5. Phase E

## Execution Backlog (P1/P2/P3 + estymacja)

### P1 - Must have (blokuje stabilny rollout)

1. P1-01: Symbol resolution guard in TypeScriptEmitter ✅
   - Scope: wykrywanie niezdefiniowanych typow/interfejsow jeszcze w generatorze.
   - Deliverable: fail-fast z lista brakujacych symboli i sekcja/symbol zrodlowy.
   - Estimate: 1.5 dnia.

2. P1-02: `--check` mode dla `protogate codegen ts-from-python` ✅
   - Scope: porownanie in-memory output vs plik docelowy bez zapisu.
   - Deliverable: exit code 1 przy drift, czytelny diff summary.
   - Estimate: 1 dzien.

3. P1-03: Multi-target write (single run -> N targetow) ✅
   - Scope: atomowy zapis tego samego output do wielu sciezek.
   - Deliverable: jedna komenda codegen synchronizuje wszystkie frontend targety.
   - Estimate: 1 dzien.

4. P1-04: `make codegen-verify` ✅
   - Scope: spiecie `--check` + minimalny compile gate.
   - Deliverable: jeden target make do lokalnego i CI verify.
   - Estimate: 0.5 dnia.

5. P1-05: Golden tests dla `protogate/codegen/typescript.py`
   - Scope: enum, optional/nullable, union, defaults, alias/projections.
   - Deliverable: zestaw snapshotow + test runner.
   - Estimate: 2 dni.

### P2 - Should have (mocna redukcja regresji i debt)

1. P2-01: Profile output `strict` / `compat`
   - Scope: explicit mode switch na poziomie CLI.
   - Deliverable: profile konfigurujace aliasy legacy i sekcje kompatybilnosci.
   - Estimate: 1.5 dnia.

2. P2-02: First-class `DTO projections` API
   - Scope: eliminacja recznych raw-string blokow w wrapperach.
   - Deliverable: emitter API typu `.add_dto_projections(...)`.
   - Estimate: 1.5 dnia.

3. P2-03: Mapping canonical <-> legacy names
   - Scope: mapowanie np. `Device` <-> `DeviceDto`, `TestSession` <-> `TestSessionDto`.
   - Deliverable: deklaratywna mapa + walidacja konfliktow nazw.
   - Estimate: 1 dzien.

4. P2-04: Codegen change report (`--write-report`)
   - Scope: raport add/remove/change symboli i sekcji.
   - Deliverable: JSON + markdown summary po generacji.
   - Estimate: 1 dzien.

### P3 - Nice to have (DX i skalowanie)

1. P3-01: Namespace cleanup komend codegen
   - Scope: skroty i aliasy, np. `protogate codegen ts`.
   - Deliverable: kompatybilne aliasy + update help.
   - Estimate: 0.5 dnia.

2. P3-02: `--verbose` and diagnostics UX
   - Scope: statystyki output (enumy, interfejsy, targety, warnings).
   - Deliverable: czytelny summary + debug trace mode.
   - Estimate: 0.5 dnia.

3. P3-03: Hardening runbook
   - Scope: dokument procesu i troubleshooting.
   - Deliverable: `docs/protogate-codegen-hardening.md`.
   - Estimate: 0.5 dnia.

### Sprint proposal (2 tygodnie)

1. Sprint-1 (P1): P1-01, P1-02, P1-03, P1-04.
2. Sprint-2 (P1/P2): P1-05, P2-01, P2-02.
3. Sprint-3 (P2/P3): P2-03, P2-04, P3-01..03.

### Critical path

1. Najpierw: P1-01 + P1-02.
2. Potem: P1-03 + P1-04.
3. Dopiero potem: P1-05 i rozszerzenia kompatybilnosci (P2).
