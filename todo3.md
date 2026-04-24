# Plan wdrozenia: CQRS i Proto Migration (c2004-first)

## 1. Cel i zasady

1. c2004 jest source-of-truth dla migracji CQRS/proto.
2. Protogate pelni role warstwy delegujacej i wykonawczej.
3. Migracja idzie falami, bez big-bang.
4. Granice modeli: Request DTO -> Command/Query -> Read Model -> Response DTO.

## 2. Architektura docelowa

### c2004

- trzyma kontrakty proto, generatory, registry, CQRS handlers, migration discovery
- trzyma artefakty raportowe i planistyczne
- utrzymuje shell, auth/session bridge, iframe routing

### protogate

- nie trzyma logiki decyzyjnej discovery (tylko delegacja)
- nie trzyma kontraktow proto, generatorow, registry, CQRS handlers, migration discovery
- nie trzyma artefaktow raportowych i planistycznych
- zostaje runtime/delegate tooling

## 3. Fazy (8-12 tygodni)

1. Faza A (T1-2): potwierdzenie ownership i porzadki dokumentacyjne/ADR.
2. Faza B (T2-4): jeden pipeline migracyjny w c2004 + walidacja artefaktow.
3. Faza C (T3-7): fale migracji CQRS/proto:
- Wave 1: connect-data, connect-workshop
- Wave 2: connect-reports
- Wave 3: connect-manager
- Wave 4: connect-scenario
- Wave 5: connect-menu-tree
4. Faza D (T6-10): dekompozycja i twarde granice modeli CQRS.
5. Faza E (T10-12): hardening, governance, rollback policy, dashboard.

## 4. Backlog per repo

### c2004

- utrzymanie kontraktow proto i generatorow
- utrzymanie registry/compatibility checks
- utrzymanie CQRS handlers i migration discovery
- utrzymanie raportow i planow
- CI gates: walidacja artefaktow, smoke/contract/parity tests

### protogate

- cienka warstwa delegacji i wykonania
- brak ownership domeny migracyjnej
- stabilnosc API/CLI jako bridge do c2004

## 5. Definition of Done (na fale)

1. Kontrakty proto v1 zatwierdzone.
2. Generacja artefaktow bez bledow.
3. Publiczne boundary bez raw dict.
4. Parity + regresja na zielono.
5. Rollback runbook gotowy i sprawdzony.

## 6. Metryki

1. Lead time fali.
2. % endpointow z explicit DTO boundary.
3. % modulow z contract/smoke tests.
4. Trend cross-module imports.
5. Rollbacki/incydenty per fala.
6. Drift artefaktow planistycznych vs kod.

## 7. Ryzyka i mitigacje

1. Przeciek modeli wewnetrznych -> whitelist public contracts.
2. Niestabilny pipeline -> contract tests + semver.
3. Za duze fale -> max 1-2 moduly na iteracje.
4. Szum artefaktow -> generated/reviewed split + CI checks.

## 8. Kolejnosc startu od jutra

1. Finalizacja ADR ownership (c2004-first).
2. Stabilizacja full discovery pipeline w c2004.
3. Start Wave 1 z pelnym DoD.
4. Retrospekcja po Wave 1 i dopiero skala Wave 2-5.
