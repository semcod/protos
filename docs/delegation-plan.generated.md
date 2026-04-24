# Delegation Plan (Generated)

This file is generated from c2004 migration candidate report.

## Top modules to delegate first

- connect-template: score=98.81, phase=phase-1, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- identification: score=98.78, phase=phase-1, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- template: score=97.80, phase=phase-1, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-menu-tree: score=95.14, phase=phase-1, effort=low, pattern=menu-tree-cqrs, cmds=12, evts=3, shared=@semcod/contracts-types:menu-tree-core
- connect-live-protocol: score=93.91, phase=phase-1, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-scenario: score=91.69, phase=phase-1, effort=low, pattern=scenario-builder-cqrs, cmds=19, evts=8, shared=@semcod/contracts-types:scenario-core
- connect-devtools: score=88.01, phase=phase-1, effort=low, pattern=devtools-ops-cqrs, cmds=8, evts=6, shared=@semcod/contracts-types:devtools-core
- connect-router: score=86.75, phase=phase-1, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-reports: score=84.82, phase=phase-1, effort=low, pattern=reports-filtering-cqrs, cmds=5, evts=5, shared=@semcod/contracts-types:reports-core
- connect-manager: score=78.38, phase=phase-1, effort=low, pattern=manager-library-workflow-cqrs, cmds=20, evts=16, shared=@semcod/contracts-types:manager-core
- connect-template2: score=77.30, phase=phase-1, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-id: score=74.64, phase=phase-1, effort=low, pattern=id-user-admin-cqrs, cmds=8, evts=4, shared=@semcod/contracts-types:id-core
- connect-workshop: score=60.03, phase=phase-2, effort=medium, pattern=data-grid-cqrs, cmds=9, evts=9, shared=@semcod/contracts-types:cqrs-data-grid
- connect-menu-editor: score=59.33, phase=phase-2, effort=medium, pattern=menu-editor-snapshots-cqrs, cmds=5, evts=3, shared=@semcod/contracts-types:menu-editor-core
- connect-config: score=55.53, phase=phase-2, effort=medium, pattern=config-admin-cqrs, cmds=31, evts=25, shared=@semcod/contracts-types:config-admin
- connect-data: score=0.00, phase=phase-3, effort=high, pattern=data-grid-cqrs, cmds=13, evts=11, shared=@semcod/contracts-types:cqrs-data-grid
- connect-test: score=0.00, phase=phase-3, effort=high, pattern=test-orchestration-cqrs, cmds=57, evts=19, shared=@semcod/contracts-types:test-orchestration-core
- connect-test-device: score=0.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-test-full: score=0.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-test-protocol: score=0.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module

## Slice blueprints

### Slice blueprint: connect-template

- Slice: `connect-template`
- Contract dir: `contracts/connect-template/v1`
- Commands: `/commands/connect-template/*`
- Queries: `/queries/connect-template/*`
- Health: `/health/modules/connect-template`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 2
  - lines: 77

### Slice blueprint: identification

- Slice: `identification`
- Contract dir: `contracts/identification/v1`
- Commands: `/commands/identification/*`
- Queries: `/queries/identification/*`
- Health: `/health/modules/identification`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 2
  - lines: 90

### Slice blueprint: template

- Slice: `template`
- Contract dir: `contracts/template/v1`
- Commands: `/commands/template/*`
- Queries: `/queries/template/*`
- Health: `/health/modules/template`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 2
  - lines: 481

### Slice blueprint: connect-menu-tree

- Slice: `connect-menu-tree`
- Contract dir: `contracts/connect-menu-tree/v1`
- Commands: `/commands/connect-menu-tree/*`
- Queries: `/queries/connect-menu-tree/*`
- Health: `/health/modules/connect-menu-tree`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `menu-tree-cqrs`
- CQRS command tokens: `12`
- CQRS event tokens: `3`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:menu-tree-core`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 6
  - lines: 744

### Slice blueprint: connect-live-protocol

- Slice: `connect-live-protocol`
- Contract dir: `contracts/connect-live-protocol/v1`
- Commands: `/commands/connect-live-protocol/*`
- Queries: `/queries/connect-live-protocol/*`
- Health: `/health/modules/connect-live-protocol`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 5
  - lines: 1438

### Slice blueprint: connect-scenario

- Slice: `connect-scenario`
- Contract dir: `contracts/connect-scenario/v1`
- Commands: `/commands/connect-scenario/*`
- Queries: `/queries/connect-scenario/*`
- Health: `/health/modules/connect-scenario`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `scenario-builder-cqrs`
- CQRS command tokens: `19`
- CQRS event tokens: `8`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:scenario-core`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 1
  - api endpoints used: 0
  - files: 11
  - lines: 726

### Slice blueprint: connect-devtools

- Slice: `connect-devtools`
- Contract dir: `contracts/connect-devtools/v1`
- Commands: `/commands/connect-devtools/*`
- Queries: `/queries/connect-devtools/*`
- Health: `/health/modules/connect-devtools`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `devtools-ops-cqrs`
- CQRS command tokens: `8`
- CQRS event tokens: `6`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:devtools-core`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 2
  - files: 11
  - lines: 1397

### Slice blueprint: connect-router

- Slice: `connect-router`
- Contract dir: `contracts/connect-router/v1`
- Commands: `/commands/connect-router/*`
- Queries: `/queries/connect-router/*`
- Health: `/health/modules/connect-router`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 1
  - files: 4
  - lines: 699

### Slice blueprint: connect-reports

- Slice: `connect-reports`
- Contract dir: `contracts/connect-reports/v1`
- Commands: `/commands/connect-reports/*`
- Queries: `/queries/connect-reports/*`
- Health: `/health/modules/connect-reports`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `reports-filtering-cqrs`
- CQRS command tokens: `5`
- CQRS event tokens: `5`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:reports-core`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 10
  - lines: 873

### Slice blueprint: connect-manager

- Slice: `connect-manager`
- Contract dir: `contracts/connect-manager/v1`
- Commands: `/commands/connect-manager/*`
- Queries: `/queries/connect-manager/*`
- Health: `/health/modules/connect-manager`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `manager-library-workflow-cqrs`
- CQRS command tokens: `20`
- CQRS event tokens: `16`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:manager-core`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 3
  - files: 11
  - lines: 1448

### Slice blueprint: connect-template2

- Slice: `connect-template2`
- Contract dir: `contracts/connect-template2/v1`
- Commands: `/commands/connect-template2/*`
- Queries: `/queries/connect-template2/*`
- Health: `/health/modules/connect-template2`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 4
  - api endpoints used: 1
  - files: 15
  - lines: 3881

### Slice blueprint: connect-id

- Slice: `connect-id`
- Contract dir: `contracts/connect-id/v1`
- Commands: `/commands/connect-id/*`
- Queries: `/queries/connect-id/*`
- Health: `/health/modules/connect-id`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `id-user-admin-cqrs`
- CQRS command tokens: `8`
- CQRS event tokens: `4`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:id-core`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 3
  - files: 15
  - lines: 2146

### Slice blueprint: connect-workshop

- Slice: `connect-workshop`
- Contract dir: `contracts/connect-workshop/v1`
- Commands: `/commands/connect-workshop/*`
- Queries: `/queries/connect-workshop/*`
- Health: `/health/modules/connect-workshop`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `data-grid-cqrs`
- CQRS command tokens: `9`
- CQRS event tokens: `9`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:cqrs-data-grid`
- Readiness reasons:
  - cross-module imports: 4
  - page imports: 0
  - external imports: 1
  - api endpoints used: 0
  - files: 9
  - lines: 989

### Slice blueprint: connect-menu-editor

- Slice: `connect-menu-editor`
- Contract dir: `contracts/connect-menu-editor/v1`
- Commands: `/commands/connect-menu-editor/*`
- Queries: `/queries/connect-menu-editor/*`
- Health: `/health/modules/connect-menu-editor`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `menu-editor-snapshots-cqrs`
- CQRS command tokens: `5`
- CQRS event tokens: `3`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:menu-editor-core`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 4
  - files: 28
  - lines: 5069

### Slice blueprint: connect-config

- Slice: `connect-config`
- Contract dir: `contracts/connect-config/v1`
- Commands: `/commands/connect-config/*`
- Queries: `/queries/connect-config/*`
- Health: `/health/modules/connect-config`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `config-admin-cqrs`
- CQRS command tokens: `31`
- CQRS event tokens: `25`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:config-admin`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 2
  - api endpoints used: 16
  - files: 13
  - lines: 1586

### Slice blueprint: connect-data

- Slice: `connect-data`
- Contract dir: `contracts/connect-data/v1`
- Commands: `/commands/connect-data/*`
- Queries: `/queries/connect-data/*`
- Health: `/health/modules/connect-data`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `data-grid-cqrs`
- CQRS command tokens: `13`
- CQRS event tokens: `11`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:cqrs-data-grid`
- Readiness reasons:
  - cross-module imports: 14
  - page imports: 0
  - external imports: 1
  - api endpoints used: 2
  - files: 17
  - lines: 2404

### Slice blueprint: connect-test

- Slice: `connect-test`
- Contract dir: `contracts/connect-test/v1`
- Commands: `/commands/connect-test/*`
- Queries: `/queries/connect-test/*`
- Health: `/health/modules/connect-test`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `test-orchestration-cqrs`
- CQRS command tokens: `57`
- CQRS event tokens: `19`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:test-orchestration-core`
- Readiness reasons:
  - cross-module imports: 16
  - page imports: 0
  - external imports: 1
  - api endpoints used: 8
  - files: 56
  - lines: 9977

### Slice blueprint: connect-test-device

- Slice: `connect-test-device`
- Contract dir: `contracts/connect-test-device/v1`
- Commands: `/commands/connect-test-device/*`
- Queries: `/queries/connect-test-device/*`
- Health: `/health/modules/connect-test-device`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 21
  - page imports: 0
  - external imports: 0
  - api endpoints used: 1
  - files: 20
  - lines: 3590

### Slice blueprint: connect-test-full

- Slice: `connect-test-full`
- Contract dir: `contracts/connect-test-full/v1`
- Commands: `/commands/connect-test-full/*`
- Queries: `/queries/connect-test-full/*`
- Health: `/health/modules/connect-test-full`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 18
  - page imports: 0
  - external imports: 0
  - api endpoints used: 2
  - files: 26
  - lines: 3326

### Slice blueprint: connect-test-protocol

- Slice: `connect-test-protocol`
- Contract dir: `contracts/connect-test-protocol/v1`
- Commands: `/commands/connect-test-protocol/*`
- Queries: `/queries/connect-test-protocol/*`
- Health: `/health/modules/connect-test-protocol`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 10
  - page imports: 0
  - external imports: 0
  - api endpoints used: 1
  - files: 39
  - lines: 6683

## Per-module execution checklist

### Checklist: connect-template

1. Create contract under contracts/connect-template/v1
2. Implement gateway handler for connect-template commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-template
4. Create delegated UI entrypoint for connect-template
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-template
7. Run data bootstrap and smoke checks
8. Archive legacy connect-template implementation in c2004

### Checklist: identification

1. Create contract under contracts/identification/v1
2. Implement gateway handler for identification commands and queries
3. Add read model storage and replay/bootstrap adapter for identification
4. Create delegated UI entrypoint for identification
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for identification
7. Run data bootstrap and smoke checks
8. Archive legacy identification implementation in c2004

### Checklist: template

1. Create contract under contracts/template/v1
2. Implement gateway handler for template commands and queries
3. Add read model storage and replay/bootstrap adapter for template
4. Create delegated UI entrypoint for template
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for template
7. Run data bootstrap and smoke checks
8. Archive legacy template implementation in c2004

### Checklist: connect-menu-tree

1. Create contract under contracts/connect-menu-tree/v1
2. Implement gateway handler for connect-menu-tree commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-menu-tree
4. Create delegated UI entrypoint for connect-menu-tree
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-menu-tree
7. Run data bootstrap and smoke checks
8. Archive legacy connect-menu-tree implementation in c2004

### Checklist: connect-live-protocol

1. Create contract under contracts/connect-live-protocol/v1
2. Implement gateway handler for connect-live-protocol commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-live-protocol
4. Create delegated UI entrypoint for connect-live-protocol
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-live-protocol
7. Run data bootstrap and smoke checks
8. Archive legacy connect-live-protocol implementation in c2004

### Checklist: connect-scenario

1. Create contract under contracts/connect-scenario/v1
2. Implement gateway handler for connect-scenario commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-scenario
4. Create delegated UI entrypoint for connect-scenario
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-scenario
7. Run data bootstrap and smoke checks
8. Archive legacy connect-scenario implementation in c2004

### Checklist: connect-devtools

1. Create contract under contracts/connect-devtools/v1
2. Implement gateway handler for connect-devtools commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-devtools
4. Create delegated UI entrypoint for connect-devtools
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-devtools
7. Run data bootstrap and smoke checks
8. Archive legacy connect-devtools implementation in c2004

### Checklist: connect-router

1. Create contract under contracts/connect-router/v1
2. Implement gateway handler for connect-router commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-router
4. Create delegated UI entrypoint for connect-router
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-router
7. Run data bootstrap and smoke checks
8. Archive legacy connect-router implementation in c2004

### Checklist: connect-reports

1. Create contract under contracts/connect-reports/v1
2. Implement gateway handler for connect-reports commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-reports
4. Create delegated UI entrypoint for connect-reports
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-reports
7. Run data bootstrap and smoke checks
8. Archive legacy connect-reports implementation in c2004

### Checklist: connect-manager

1. Create contract under contracts/connect-manager/v1
2. Implement gateway handler for connect-manager commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-manager
4. Create delegated UI entrypoint for connect-manager
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-manager
7. Run data bootstrap and smoke checks
8. Archive legacy connect-manager implementation in c2004

### Checklist: connect-template2

1. Create contract under contracts/connect-template2/v1
2. Implement gateway handler for connect-template2 commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-template2
4. Create delegated UI entrypoint for connect-template2
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-template2
7. Run data bootstrap and smoke checks
8. Archive legacy connect-template2 implementation in c2004

### Checklist: connect-id

1. Create contract under contracts/connect-id/v1
2. Implement gateway handler for connect-id commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-id
4. Create delegated UI entrypoint for connect-id
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-id
7. Run data bootstrap and smoke checks
8. Archive legacy connect-id implementation in c2004

### Checklist: connect-workshop

1. Create contract under contracts/connect-workshop/v1
2. Implement gateway handler for connect-workshop commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-workshop
4. Create delegated UI entrypoint for connect-workshop
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-workshop
7. Run data bootstrap and smoke checks
8. Archive legacy connect-workshop implementation in c2004

### Checklist: connect-menu-editor

1. Create contract under contracts/connect-menu-editor/v1
2. Implement gateway handler for connect-menu-editor commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-menu-editor
4. Create delegated UI entrypoint for connect-menu-editor
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-menu-editor
7. Run data bootstrap and smoke checks
8. Archive legacy connect-menu-editor implementation in c2004

### Checklist: connect-config

1. Create contract under contracts/connect-config/v1
2. Implement gateway handler for connect-config commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-config
4. Create delegated UI entrypoint for connect-config
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-config
7. Run data bootstrap and smoke checks
8. Archive legacy connect-config implementation in c2004

### Checklist: connect-data

1. Create contract under contracts/connect-data/v1
2. Implement gateway handler for connect-data commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-data
4. Create delegated UI entrypoint for connect-data
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-data
7. Run data bootstrap and smoke checks
8. Archive legacy connect-data implementation in c2004

### Checklist: connect-test

1. Create contract under contracts/connect-test/v1
2. Implement gateway handler for connect-test commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-test
4. Create delegated UI entrypoint for connect-test
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-test
7. Run data bootstrap and smoke checks
8. Archive legacy connect-test implementation in c2004

### Checklist: connect-test-device

1. Create contract under contracts/connect-test-device/v1
2. Implement gateway handler for connect-test-device commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-test-device
4. Create delegated UI entrypoint for connect-test-device
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-test-device
7. Run data bootstrap and smoke checks
8. Archive legacy connect-test-device implementation in c2004

### Checklist: connect-test-full

1. Create contract under contracts/connect-test-full/v1
2. Implement gateway handler for connect-test-full commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-test-full
4. Create delegated UI entrypoint for connect-test-full
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-test-full
7. Run data bootstrap and smoke checks
8. Archive legacy connect-test-full implementation in c2004

### Checklist: connect-test-protocol

1. Create contract under contracts/connect-test-protocol/v1
2. Implement gateway handler for connect-test-protocol commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-test-protocol
4. Create delegated UI entrypoint for connect-test-protocol
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-test-protocol
7. Run data bootstrap and smoke checks
8. Archive legacy connect-test-protocol implementation in c2004
