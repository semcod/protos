# Delegation Plan (Generated)

This file is generated from c2004 migration candidate report.

## Top modules to delegate first

| module | score | phase | effort | cqrs pattern | shared types package |
|---|---:|---|---|---|---|
| connect-template | 98.81 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| identification | 98.78 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| template | 97.80 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| connect-menu-tree | 95.14 | phase-1 | low | menu-tree-cqrs | @semcod/contracts-types:menu-tree-core |
| connect-live-protocol | 93.91 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| connect-scenario | 91.69 | phase-1 | low | scenario-builder-cqrs | @semcod/contracts-types:scenario-core |
| connect-devtools | 88.01 | phase-1 | low | devtools-ops-cqrs | @semcod/contracts-types:devtools-core |
| connect-router | 86.75 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| connect-reports | 84.82 | phase-1 | low | reports-filtering-cqrs | @semcod/contracts-types:reports-core |
| connect-manager | 78.38 | phase-1 | low | manager-library-workflow-cqrs | @semcod/contracts-types:manager-core |
| connect-template2 | 77.30 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| connect-id | 74.64 | phase-1 | low | id-user-admin-cqrs | @semcod/contracts-types:id-core |
| connect-workshop | 60.03 | phase-2 | medium | data-grid-cqrs | @semcod/contracts-types:cqrs-data-grid |
| connect-menu-editor | 59.33 | phase-2 | medium | menu-editor-snapshots-cqrs | @semcod/contracts-types:menu-editor-core |
| connect-config | 55.53 | phase-2 | medium | config-admin-cqrs | @semcod/contracts-types:config-admin |
| connect-data | 0.00 | phase-3 | high | data-grid-cqrs | @semcod/contracts-types:cqrs-data-grid |
| connect-test | 0.00 | phase-3 | high | test-orchestration-cqrs | @semcod/contracts-types:test-orchestration-core |
| connect-test-device | 0.00 | phase-3 | high | n/a | @semcod/contracts-types:custom-per-module |
| connect-test-full | 0.00 | phase-3 | high | n/a | @semcod/contracts-types:custom-per-module |
| connect-test-protocol | 0.00 | phase-3 | high | n/a | @semcod/contracts-types:custom-per-module |

## Slice blueprints

### connect-template

- Slice: `connect-template`
- Contract dir: `contracts/connect-template/v1`
- Commands: `/commands/connect-template/*`
- Queries: `/queries/connect-template/*`
- Health: `/health/modules/connect-template`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 2
  - lines: 77

### identification

- Slice: `identification`
- Contract dir: `contracts/identification/v1`
- Commands: `/commands/identification/*`
- Queries: `/queries/identification/*`
- Health: `/health/modules/identification`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 2
  - lines: 90

### template

- Slice: `template`
- Contract dir: `contracts/template/v1`
- Commands: `/commands/template/*`
- Queries: `/queries/template/*`
- Health: `/health/modules/template`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 2
  - lines: 481

### connect-menu-tree

- Slice: `connect-menu-tree`
- Contract dir: `contracts/connect-menu-tree/v1`
- Commands: `/commands/connect-menu-tree/*`
- Queries: `/queries/connect-menu-tree/*`
- Health: `/health/modules/connect-menu-tree`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `menu-tree-cqrs`
- Shared types package: `@semcod/contracts-types:menu-tree-core`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 6
  - lines: 744

### connect-live-protocol

- Slice: `connect-live-protocol`
- Contract dir: `contracts/connect-live-protocol/v1`
- Commands: `/commands/connect-live-protocol/*`
- Queries: `/queries/connect-live-protocol/*`
- Health: `/health/modules/connect-live-protocol`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 5
  - lines: 1438

### connect-scenario

- Slice: `connect-scenario`
- Contract dir: `contracts/connect-scenario/v1`
- Commands: `/commands/connect-scenario/*`
- Queries: `/queries/connect-scenario/*`
- Health: `/health/modules/connect-scenario`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `scenario-builder-cqrs`
- Shared types package: `@semcod/contracts-types:scenario-core`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 1
  - api endpoints used: 0
  - files: 11
  - lines: 726

### connect-devtools

- Slice: `connect-devtools`
- Contract dir: `contracts/connect-devtools/v1`
- Commands: `/commands/connect-devtools/*`
- Queries: `/queries/connect-devtools/*`
- Health: `/health/modules/connect-devtools`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `devtools-ops-cqrs`
- Shared types package: `@semcod/contracts-types:devtools-core`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 0
  - api endpoints used: 2
  - files: 11
  - lines: 1397

### connect-router

- Slice: `connect-router`
- Contract dir: `contracts/connect-router/v1`
- Commands: `/commands/connect-router/*`
- Queries: `/queries/connect-router/*`
- Health: `/health/modules/connect-router`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 1
  - files: 4
  - lines: 699

### connect-reports

- Slice: `connect-reports`
- Contract dir: `contracts/connect-reports/v1`
- Commands: `/commands/connect-reports/*`
- Queries: `/queries/connect-reports/*`
- Health: `/health/modules/connect-reports`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `reports-filtering-cqrs`
- Shared types package: `@semcod/contracts-types:reports-core`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 0
  - files: 10
  - lines: 873

### connect-manager

- Slice: `connect-manager`
- Contract dir: `contracts/connect-manager/v1`
- Commands: `/commands/connect-manager/*`
- Queries: `/queries/connect-manager/*`
- Health: `/health/modules/connect-manager`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `manager-library-workflow-cqrs`
- Shared types package: `@semcod/contracts-types:manager-core`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 3
  - files: 11
  - lines: 1448

### connect-template2

- Slice: `connect-template2`
- Contract dir: `contracts/connect-template2/v1`
- Commands: `/commands/connect-template2/*`
- Queries: `/queries/connect-template2/*`
- Health: `/health/modules/connect-template2`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 0
  - external imports: 4
  - api endpoints used: 1
  - files: 15
  - lines: 3881

### connect-id

- Slice: `connect-id`
- Contract dir: `contracts/connect-id/v1`
- Commands: `/commands/connect-id/*`
- Queries: `/queries/connect-id/*`
- Health: `/health/modules/connect-id`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `id-user-admin-cqrs`
- Shared types package: `@semcod/contracts-types:id-core`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 3
  - files: 15
  - lines: 2146

### connect-workshop

- Slice: `connect-workshop`
- Contract dir: `contracts/connect-workshop/v1`
- Commands: `/commands/connect-workshop/*`
- Queries: `/queries/connect-workshop/*`
- Health: `/health/modules/connect-workshop`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `data-grid-cqrs`
- Shared types package: `@semcod/contracts-types:cqrs-data-grid`
- Readiness reasons:
  - cross-module imports: 4
  - page imports: 0
  - external imports: 1
  - api endpoints used: 0
  - files: 9
  - lines: 989

### connect-menu-editor

- Slice: `connect-menu-editor`
- Contract dir: `contracts/connect-menu-editor/v1`
- Commands: `/commands/connect-menu-editor/*`
- Queries: `/queries/connect-menu-editor/*`
- Health: `/health/modules/connect-menu-editor`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `menu-editor-snapshots-cqrs`
- Shared types package: `@semcod/contracts-types:menu-editor-core`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 0
  - api endpoints used: 4
  - files: 28
  - lines: 5069

### connect-config

- Slice: `connect-config`
- Contract dir: `contracts/connect-config/v1`
- Commands: `/commands/connect-config/*`
- Queries: `/queries/connect-config/*`
- Health: `/health/modules/connect-config`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `config-admin-cqrs`
- Shared types package: `@semcod/contracts-types:config-admin`
- Readiness reasons:
  - cross-module imports: 1
  - page imports: 0
  - external imports: 2
  - api endpoints used: 16
  - files: 13
  - lines: 1586

### connect-data

- Slice: `connect-data`
- Contract dir: `contracts/connect-data/v1`
- Commands: `/commands/connect-data/*`
- Queries: `/queries/connect-data/*`
- Health: `/health/modules/connect-data`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `data-grid-cqrs`
- Shared types package: `@semcod/contracts-types:cqrs-data-grid`
- Readiness reasons:
  - cross-module imports: 14
  - page imports: 0
  - external imports: 1
  - api endpoints used: 2
  - files: 17
  - lines: 2404

### connect-test

- Slice: `connect-test`
- Contract dir: `contracts/connect-test/v1`
- Commands: `/commands/connect-test/*`
- Queries: `/queries/connect-test/*`
- Health: `/health/modules/connect-test`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `test-orchestration-cqrs`
- Shared types package: `@semcod/contracts-types:test-orchestration-core`
- Readiness reasons:
  - cross-module imports: 16
  - page imports: 0
  - external imports: 1
  - api endpoints used: 8
  - files: 56
  - lines: 9977

### connect-test-device

- Slice: `connect-test-device`
- Contract dir: `contracts/connect-test-device/v1`
- Commands: `/commands/connect-test-device/*`
- Queries: `/queries/connect-test-device/*`
- Health: `/health/modules/connect-test-device`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 21
  - page imports: 0
  - external imports: 0
  - api endpoints used: 1
  - files: 20
  - lines: 3590

### connect-test-full

- Slice: `connect-test-full`
- Contract dir: `contracts/connect-test-full/v1`
- Commands: `/commands/connect-test-full/*`
- Queries: `/queries/connect-test-full/*`
- Health: `/health/modules/connect-test-full`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 18
  - page imports: 0
  - external imports: 0
  - api endpoints used: 2
  - files: 26
  - lines: 3326

### connect-test-protocol

- Slice: `connect-test-protocol`
- Contract dir: `contracts/connect-test-protocol/v1`
- Commands: `/commands/connect-test-protocol/*`
- Queries: `/queries/connect-test-protocol/*`
- Health: `/health/modules/connect-test-protocol`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 10
  - page imports: 0
  - external imports: 0
  - api endpoints used: 1
  - files: 39
  - lines: 6683

## Per-module execution checklist

### connect-template

1. Create contract under contracts/connect-template/v1
2. Implement gateway handler for connect-template commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-template
4. Create delegated UI entrypoint for connect-template
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-template
7. Run data bootstrap and smoke checks
8. Archive legacy connect-template implementation in c2004

### identification

1. Create contract under contracts/identification/v1
2. Implement gateway handler for identification commands and queries
3. Add read model storage and replay/bootstrap adapter for identification
4. Create delegated UI entrypoint for identification
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for identification
7. Run data bootstrap and smoke checks
8. Archive legacy identification implementation in c2004

### template

1. Create contract under contracts/template/v1
2. Implement gateway handler for template commands and queries
3. Add read model storage and replay/bootstrap adapter for template
4. Create delegated UI entrypoint for template
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for template
7. Run data bootstrap and smoke checks
8. Archive legacy template implementation in c2004

### connect-menu-tree

1. Create contract under contracts/connect-menu-tree/v1
2. Implement gateway handler for connect-menu-tree commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-menu-tree
4. Create delegated UI entrypoint for connect-menu-tree
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-menu-tree
7. Run data bootstrap and smoke checks
8. Archive legacy connect-menu-tree implementation in c2004

### connect-live-protocol

1. Create contract under contracts/connect-live-protocol/v1
2. Implement gateway handler for connect-live-protocol commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-live-protocol
4. Create delegated UI entrypoint for connect-live-protocol
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-live-protocol
7. Run data bootstrap and smoke checks
8. Archive legacy connect-live-protocol implementation in c2004

### connect-scenario

1. Create contract under contracts/connect-scenario/v1
2. Implement gateway handler for connect-scenario commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-scenario
4. Create delegated UI entrypoint for connect-scenario
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-scenario
7. Run data bootstrap and smoke checks
8. Archive legacy connect-scenario implementation in c2004

### connect-devtools

1. Create contract under contracts/connect-devtools/v1
2. Implement gateway handler for connect-devtools commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-devtools
4. Create delegated UI entrypoint for connect-devtools
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-devtools
7. Run data bootstrap and smoke checks
8. Archive legacy connect-devtools implementation in c2004

### connect-router

1. Create contract under contracts/connect-router/v1
2. Implement gateway handler for connect-router commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-router
4. Create delegated UI entrypoint for connect-router
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-router
7. Run data bootstrap and smoke checks
8. Archive legacy connect-router implementation in c2004

### connect-reports

1. Create contract under contracts/connect-reports/v1
2. Implement gateway handler for connect-reports commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-reports
4. Create delegated UI entrypoint for connect-reports
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-reports
7. Run data bootstrap and smoke checks
8. Archive legacy connect-reports implementation in c2004

### connect-manager

1. Create contract under contracts/connect-manager/v1
2. Implement gateway handler for connect-manager commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-manager
4. Create delegated UI entrypoint for connect-manager
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-manager
7. Run data bootstrap and smoke checks
8. Archive legacy connect-manager implementation in c2004

### connect-template2

1. Create contract under contracts/connect-template2/v1
2. Implement gateway handler for connect-template2 commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-template2
4. Create delegated UI entrypoint for connect-template2
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-template2
7. Run data bootstrap and smoke checks
8. Archive legacy connect-template2 implementation in c2004

### connect-id

1. Create contract under contracts/connect-id/v1
2. Implement gateway handler for connect-id commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-id
4. Create delegated UI entrypoint for connect-id
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-id
7. Run data bootstrap and smoke checks
8. Archive legacy connect-id implementation in c2004

### connect-workshop

1. Create contract under contracts/connect-workshop/v1
2. Implement gateway handler for connect-workshop commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-workshop
4. Create delegated UI entrypoint for connect-workshop
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-workshop
7. Run data bootstrap and smoke checks
8. Archive legacy connect-workshop implementation in c2004

### connect-menu-editor

1. Create contract under contracts/connect-menu-editor/v1
2. Implement gateway handler for connect-menu-editor commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-menu-editor
4. Create delegated UI entrypoint for connect-menu-editor
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-menu-editor
7. Run data bootstrap and smoke checks
8. Archive legacy connect-menu-editor implementation in c2004

### connect-config

1. Create contract under contracts/connect-config/v1
2. Implement gateway handler for connect-config commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-config
4. Create delegated UI entrypoint for connect-config
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-config
7. Run data bootstrap and smoke checks
8. Archive legacy connect-config implementation in c2004

### connect-data

1. Create contract under contracts/connect-data/v1
2. Implement gateway handler for connect-data commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-data
4. Create delegated UI entrypoint for connect-data
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-data
7. Run data bootstrap and smoke checks
8. Archive legacy connect-data implementation in c2004

### connect-test

1. Create contract under contracts/connect-test/v1
2. Implement gateway handler for connect-test commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-test
4. Create delegated UI entrypoint for connect-test
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-test
7. Run data bootstrap and smoke checks
8. Archive legacy connect-test implementation in c2004

### connect-test-device

1. Create contract under contracts/connect-test-device/v1
2. Implement gateway handler for connect-test-device commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-test-device
4. Create delegated UI entrypoint for connect-test-device
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-test-device
7. Run data bootstrap and smoke checks
8. Archive legacy connect-test-device implementation in c2004

### connect-test-full

1. Create contract under contracts/connect-test-full/v1
2. Implement gateway handler for connect-test-full commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-test-full
4. Create delegated UI entrypoint for connect-test-full
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-test-full
7. Run data bootstrap and smoke checks
8. Archive legacy connect-test-full implementation in c2004

### connect-test-protocol

1. Create contract under contracts/connect-test-protocol/v1
2. Implement gateway handler for connect-test-protocol commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-test-protocol
4. Create delegated UI entrypoint for connect-test-protocol
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-test-protocol
7. Run data bootstrap and smoke checks
8. Archive legacy connect-test-protocol implementation in c2004
