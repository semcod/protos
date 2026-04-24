# Delegation Plan (Generated)

This file is generated from c2004 migration candidate report.

## Top modules to delegate first

- connect-reports-month: score=82.00, phase=phase-1, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-config-network: score=71.17, phase=phase-2, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-manager-library: score=67.35, phase=phase-2, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- .swop: score=55.00, phase=phase-2, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- project: score=55.00, phase=phase-2, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- testql-scenarios: score=55.00, phase=phase-2, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- site: score=46.65, phase=phase-3, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-id-user-list: score=40.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- env: score=40.00, phase=phase-3, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- encoder-control: score=39.00, phase=phase-3, effort=low, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- desktop: score=35.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- fleet-workshop-manager: score=27.50, phase=phase-3, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-template: score=7.56, phase=phase-3, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- connect-display: score=4.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- backend: score=0.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- fleet-data-manager: score=0.00, phase=phase-3, effort=medium, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module
- frontend: score=0.00, phase=phase-3, effort=high, pattern=n/a, cmds=0, evts=0, shared=@semcod/contracts-types:custom-per-module

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

### Slice blueprint: .swop

- Slice: `.swop`
- Contract dir: `contracts/.swop/v1`
- Commands: `/commands/.swop/*`
- Queries: `/queries/.swop/*`
- Health: `/health/modules/.swop`
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
  - files: 1
  - lines: 114

### Slice blueprint: project

- Slice: `project`
- Contract dir: `contracts/project/v1`
- Commands: `/commands/project/*`
- Queries: `/queries/project/*`
- Health: `/health/modules/project`
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
  - files: 0
  - lines: 0

### Slice blueprint: testql-scenarios

- Slice: `testql-scenarios`
- Contract dir: `contracts/testql-scenarios/v1`
- Commands: `/commands/testql-scenarios/*`
- Queries: `/queries/testql-scenarios/*`
- Health: `/health/modules/testql-scenarios`
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
  - files: 1
  - lines: 17

### Slice blueprint: site

- Slice: `site`
- Contract dir: `contracts/site/v1`
- Commands: `/commands/site/*`
- Queries: `/queries/site/*`
- Health: `/health/modules/site`
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
  - external imports: 7
  - api endpoints used: 2
  - files: 8
  - lines: 2022

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

### Slice blueprint: env

- Slice: `env`
- Contract dir: `contracts/env/v1`
- Commands: `/commands/env/*`
- Queries: `/queries/env/*`
- Health: `/health/modules/env`
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
  - api endpoints used: 2
  - files: 1
  - lines: 255

### Slice blueprint: encoder-control

- Slice: `encoder-control`
- Contract dir: `contracts/encoder-control/v1`
- Commands: `/commands/encoder-control/*`
- Queries: `/queries/encoder-control/*`
- Health: `/health/modules/encoder-control`
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
  - external imports: 21
  - api endpoints used: 0
  - files: 11
  - lines: 1027

### Slice blueprint: desktop

- Slice: `desktop`
- Contract dir: `contracts/desktop/v1`
- Commands: `/commands/desktop/*`
- Queries: `/queries/desktop/*`
- Health: `/health/modules/desktop`
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
  - files: 8
  - lines: 4729

### Slice blueprint: fleet-workshop-manager

- Slice: `fleet-workshop-manager`
- Contract dir: `contracts/fleet-workshop-manager/v1`
- Commands: `/commands/fleet-workshop-manager/*`
- Queries: `/queries/fleet-workshop-manager/*`
- Health: `/health/modules/fleet-workshop-manager`
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
  - external imports: 11
  - api endpoints used: 0
  - files: 7
  - lines: 353

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

### Slice blueprint: backend

- Slice: `backend`
- Contract dir: `contracts/backend/v1`
- Commands: `/commands/backend/*`
- Queries: `/queries/backend/*`
- Health: `/health/modules/backend`
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
  - external imports: 1336
  - api endpoints used: 36
  - files: 592
  - lines: 90810

### Slice blueprint: fleet-data-manager

- Slice: `fleet-data-manager`
- Contract dir: `contracts/fleet-data-manager/v1`
- Commands: `/commands/fleet-data-manager/*`
- Queries: `/queries/fleet-data-manager/*`
- Health: `/health/modules/fleet-data-manager`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 4
  - page imports: 0
  - external imports: 35
  - api endpoints used: 0
  - files: 22
  - lines: 892

### Slice blueprint: frontend

- Slice: `frontend`
- Contract dir: `contracts/frontend/v1`
- Commands: `/commands/frontend/*`
- Queries: `/queries/frontend/*`
- Health: `/health/modules/frontend`
- Frontend strategy: `gateway-static-or-dedicated-frontend-service`
- Host mode: `iframe`
- CQRS pattern: `n/a`
- CQRS command tokens: `0`
- CQRS event tokens: `0`
- CQRS cluster size: `1`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Readiness reasons:
  - cross-module imports: 7
  - page imports: 402
  - external imports: 283
  - api endpoints used: 41
  - files: 875
  - lines: 219896

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

### Checklist: .swop

1. Create contract under contracts/.swop/v1
2. Implement gateway handler for .swop commands and queries
3. Add read model storage and replay/bootstrap adapter for .swop
4. Create delegated UI entrypoint for .swop
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for .swop
7. Run data bootstrap and smoke checks
8. Archive legacy .swop implementation in c2004

### Checklist: project

1. Create contract under contracts/project/v1
2. Implement gateway handler for project commands and queries
3. Add read model storage and replay/bootstrap adapter for project
4. Create delegated UI entrypoint for project
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for project
7. Run data bootstrap and smoke checks
8. Archive legacy project implementation in c2004

### Checklist: testql-scenarios

1. Create contract under contracts/testql-scenarios/v1
2. Implement gateway handler for testql-scenarios commands and queries
3. Add read model storage and replay/bootstrap adapter for testql-scenarios
4. Create delegated UI entrypoint for testql-scenarios
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for testql-scenarios
7. Run data bootstrap and smoke checks
8. Archive legacy testql-scenarios implementation in c2004

### Checklist: site

1. Create contract under contracts/site/v1
2. Implement gateway handler for site commands and queries
3. Add read model storage and replay/bootstrap adapter for site
4. Create delegated UI entrypoint for site
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for site
7. Run data bootstrap and smoke checks
8. Archive legacy site implementation in c2004

### Checklist: connect-id-user-list

1. Create contract under contracts/connect-id-user-list/v1
2. Implement gateway handler for connect-id-user-list commands and queries
3. Add read model storage and replay/bootstrap adapter for connect-id-user-list
4. Create delegated UI entrypoint for connect-id-user-list
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for connect-id-user-list
7. Run data bootstrap and smoke checks
8. Archive legacy connect-id-user-list implementation in c2004

### Checklist: env

1. Create contract under contracts/env/v1
2. Implement gateway handler for env commands and queries
3. Add read model storage and replay/bootstrap adapter for env
4. Create delegated UI entrypoint for env
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for env
7. Run data bootstrap and smoke checks
8. Archive legacy env implementation in c2004

### Checklist: encoder-control

1. Create contract under contracts/encoder-control/v1
2. Implement gateway handler for encoder-control commands and queries
3. Add read model storage and replay/bootstrap adapter for encoder-control
4. Create delegated UI entrypoint for encoder-control
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for encoder-control
7. Run data bootstrap and smoke checks
8. Archive legacy encoder-control implementation in c2004

### Checklist: desktop

1. Create contract under contracts/desktop/v1
2. Implement gateway handler for desktop commands and queries
3. Add read model storage and replay/bootstrap adapter for desktop
4. Create delegated UI entrypoint for desktop
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for desktop
7. Run data bootstrap and smoke checks
8. Archive legacy desktop implementation in c2004

### Checklist: fleet-workshop-manager

1. Create contract under contracts/fleet-workshop-manager/v1
2. Implement gateway handler for fleet-workshop-manager commands and queries
3. Add read model storage and replay/bootstrap adapter for fleet-workshop-manager
4. Create delegated UI entrypoint for fleet-workshop-manager
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for fleet-workshop-manager
7. Run data bootstrap and smoke checks
8. Archive legacy fleet-workshop-manager implementation in c2004

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

### Checklist: backend

1. Create contract under contracts/backend/v1
2. Implement gateway handler for backend commands and queries
3. Add read model storage and replay/bootstrap adapter for backend
4. Create delegated UI entrypoint for backend
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for backend
7. Run data bootstrap and smoke checks
8. Archive legacy backend implementation in c2004

### Checklist: fleet-data-manager

1. Create contract under contracts/fleet-data-manager/v1
2. Implement gateway handler for fleet-data-manager commands and queries
3. Add read model storage and replay/bootstrap adapter for fleet-data-manager
4. Create delegated UI entrypoint for fleet-data-manager
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for fleet-data-manager
7. Run data bootstrap and smoke checks
8. Archive legacy fleet-data-manager implementation in c2004

### Checklist: frontend

1. Create contract under contracts/frontend/v1
2. Implement gateway handler for frontend commands and queries
3. Add read model storage and replay/bootstrap adapter for frontend
4. Create delegated UI entrypoint for frontend
5. Expose delegated UI through gateway static or dedicated frontend service
6. Switch c2004 route to iframe host for frontend
7. Run data bootstrap and smoke checks
8. Archive legacy frontend implementation in c2004
