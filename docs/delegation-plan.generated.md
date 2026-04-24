# Delegation Plan (Generated)

This file is generated from c2004 migration candidate report.

## Top modules to delegate first

| module | score | phase | effort | cqrs pattern | shared types package |
|---|---:|---|---|---|---|
| connect-template | 98.81 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| identification | 98.78 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| template | 97.80 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| connect-menu-tree | 95.14 | phase-1 | low | custom-cqrs | @semcod/contracts-types:custom-per-module |
| connect-live-protocol | 93.91 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| connect-scenario | 91.69 | phase-1 | low | custom-cqrs | @semcod/contracts-types:custom-per-module |
| connect-devtools | 88.01 | phase-1 | low | custom-cqrs | @semcod/contracts-types:custom-per-module |
| connect-router | 86.75 | phase-1 | low | n/a | @semcod/contracts-types:custom-per-module |
| connect-reports | 84.82 | phase-1 | low | reports-filtering-cqrs | @semcod/contracts-types:reports-core |
| connect-manager | 78.38 | phase-1 | low | manager-library-workflow-cqrs | @semcod/contracts-types:manager-core |

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
- CQRS pattern: `custom-cqrs`
- Shared types package: `@semcod/contracts-types:custom-per-module`
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
- CQRS pattern: `custom-cqrs`
- Shared types package: `@semcod/contracts-types:custom-per-module`
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
- CQRS pattern: `custom-cqrs`
- Shared types package: `@semcod/contracts-types:custom-per-module`
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
