# Delegation Plan (Generated)

This file is generated from c2004 migration candidate report.

## Top modules to delegate first

- connect-reports-month: score=82.00, phase=phase-1, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-config-network: score=71.17, phase=phase-2, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-manager-library: score=67.35, phase=phase-2, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-id-user-list: score=40.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-template: score=7.56, phase=phase-3, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-display: score=4.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module

## Slice blueprints

### Slice blueprint: connect-reports-month

- Slice: `connect-reports-month`
- Contract dir: `contracts/connect-reports-month/v1`
- Commands: `/commands/connect-reports-month/*`
- Queries: `/queries/connect-reports-month/*`
- Health: `/health/modules/connect-reports-month`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 2
  - external imports: 4
  - api endpoints used: 0
  - files: 7
  - lines: 380

### Slice blueprint: connect-config-network

- Slice: `connect-config-network`
- Contract dir: `contracts/connect-config-network/v1`
- Commands: `/commands/connect-config-network/*`
- Queries: `/queries/connect-config-network/*`
- Health: `/health/modules/connect-config-network`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 20
  - external imports: 4
  - api endpoints used: 0
  - files: 17
  - lines: 2259

### Slice blueprint: connect-manager-library

- Slice: `connect-manager-library`
- Contract dir: `contracts/connect-manager-library/v1`
- Commands: `/commands/connect-manager-library/*`
- Queries: `/queries/connect-manager-library/*`
- Health: `/health/modules/connect-manager-library`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 6
  - external imports: 4
  - api endpoints used: 0
  - files: 10
  - lines: 1518

### Slice blueprint: connect-id-user-list

- Slice: `connect-id-user-list`
- Contract dir: `contracts/connect-id-user-list/v1`
- Commands: `/commands/connect-id-user-list/*`
- Queries: `/queries/connect-id-user-list/*`
- Health: `/health/modules/connect-id-user-list`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 0
  - page imports: 23
  - external imports: 4
  - api endpoints used: 0
  - files: 21
  - lines: 4508

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
  - cross-module imports: 2
  - page imports: 0
  - external imports: 15
  - api endpoints used: 1
  - files: 27
  - lines: 1493

### Slice blueprint: connect-display

- Slice: `connect-display`
- Contract dir: `contracts/connect-display/v1`
- Commands: `/commands/connect-display/*`
- Queries: `/queries/connect-display/*`
- Health: `/health/modules/connect-display`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 6
  - page imports: 0
  - external imports: 4
  - api endpoints used: 0
  - files: 23
  - lines: 4284

## Per-module execution checklist

### Checklist: connect-reports-month

1. Create contract under contracts/connect-reports-month/v1
2. Implement gateway handler for connect-reports-month commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-reports-month
4. Create delegated UI entrypoint for connect-reports-month
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-reports-month
7. Run data bootstrap and smoke checks
8. Archive legacy connect-reports-month implementation in c2004

### Checklist: connect-config-network

1. Create contract under contracts/connect-config-network/v1
2. Implement gateway handler for connect-config-network commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-config-network
4. Create delegated UI entrypoint for connect-config-network
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-config-network
7. Run data bootstrap and smoke checks
8. Archive legacy connect-config-network implementation in c2004

### Checklist: connect-manager-library

1. Create contract under contracts/connect-manager-library/v1
2. Implement gateway handler for connect-manager-library commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-manager-library
4. Create delegated UI entrypoint for connect-manager-library
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-manager-library
7. Run data bootstrap and smoke checks
8. Archive legacy connect-manager-library implementation in c2004

### Checklist: connect-id-user-list

1. Create contract under contracts/connect-id-user-list/v1
2. Implement gateway handler for connect-id-user-list commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-id-user-list
4. Create delegated UI entrypoint for connect-id-user-list
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-id-user-list
7. Run data bootstrap and smoke checks
8. Archive legacy connect-id-user-list implementation in c2004

### Checklist: connect-template

1. Create contract under contracts/connect-template/v1
2. Implement gateway handler for connect-template commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-template
4. Create delegated UI entrypoint for connect-template
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-template
7. Run data bootstrap and smoke checks
8. Archive legacy connect-template implementation in c2004

### Checklist: connect-display

1. Create contract under contracts/connect-display/v1
2. Implement gateway handler for connect-display commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-display
4. Create delegated UI entrypoint for connect-display
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-display
7. Run data bootstrap and smoke checks
8. Archive legacy connect-display implementation in c2004
