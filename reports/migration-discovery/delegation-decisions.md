# Delegation Decision Rationale

Total selected delegation candidates: 6

## Repeated decision signals

- `service signal: has docker packaging`: 6
- `cqrs cluster size: 1`: 6
- `service signal: exposes own API routes`: 5
- `service signal: has executable entrypoint`: 5
- `readiness signal: external imports: 4`: 5
- `readiness signal: api endpoints used: 0`: 5
- `service signal: has dedicated api/app directory`: 4
- `service signal: has vertical api+ui structure`: 4
- `readiness signal: cross-module imports: 0`: 4
- `estimated effort is medium`: 3
- `phase target is phase-3`: 3
- `phase target is phase-2`: 2
- `estimated effort is high`: 2
- `readiness signal: page imports: 0`: 2
- `selected as delegable slice with score 82.00`: 1
- `phase target is phase-1`: 1
- `estimated effort is low`: 1
- `readiness signal: page imports: 2`: 1
- `readiness signal: files: 7`: 1
- `readiness signal: lines: 380`: 1

## Selected candidates

### Selected: connect-reports-month

- Score: `82.00`
- Phase: `phase-1`
- Effort: `low`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Why selected:
  - selected as delegable slice with score 82.00
  - phase target is phase-1
  - estimated effort is low
  - service signal: has docker packaging
  - service signal: has dedicated api/app directory
  - service signal: has vertical api+ui structure
  - service signal: exposes own API routes
  - service signal: has executable entrypoint
  - cqrs cluster size: 1
  - readiness signal: cross-module imports: 0
  - readiness signal: page imports: 2
  - readiness signal: external imports: 4
  - readiness signal: api endpoints used: 0
  - readiness signal: files: 7
  - readiness signal: lines: 380

### Selected: connect-config-network

- Score: `71.17`
- Phase: `phase-2`
- Effort: `medium`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Why selected:
  - selected as delegable slice with score 71.17
  - phase target is phase-2
  - estimated effort is medium
  - service signal: has docker packaging
  - service signal: has dedicated api/app directory
  - service signal: has vertical api+ui structure
  - service signal: exposes own API routes
  - service signal: has executable entrypoint
  - cqrs cluster size: 1
  - readiness signal: cross-module imports: 0
  - readiness signal: page imports: 20
  - readiness signal: external imports: 4
  - readiness signal: api endpoints used: 0
  - readiness signal: files: 17
  - readiness signal: lines: 2259

### Selected: connect-manager-library

- Score: `67.35`
- Phase: `phase-2`
- Effort: `medium`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Why selected:
  - selected as delegable slice with score 67.35
  - phase target is phase-2
  - estimated effort is medium
  - service signal: has docker packaging
  - service signal: has dedicated api/app directory
  - service signal: has vertical api+ui structure
  - service signal: exposes own API routes
  - service signal: has executable entrypoint
  - cqrs cluster size: 1
  - readiness signal: cross-module imports: 0
  - readiness signal: page imports: 6
  - readiness signal: external imports: 4
  - readiness signal: api endpoints used: 0
  - readiness signal: files: 10
  - readiness signal: lines: 1518

### Selected: connect-id-user-list

- Score: `40.00`
- Phase: `phase-3`
- Effort: `high`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Why selected:
  - selected as delegable slice with score 40.00
  - phase target is phase-3
  - estimated effort is high
  - service signal: has docker packaging
  - service signal: has dedicated api/app directory
  - service signal: has vertical api+ui structure
  - service signal: owns db or migration assets
  - service signal: exposes own API routes
  - cqrs cluster size: 1
  - readiness signal: cross-module imports: 0
  - readiness signal: page imports: 23
  - readiness signal: external imports: 4
  - readiness signal: api endpoints used: 0
  - readiness signal: files: 21
  - readiness signal: lines: 4508

### Selected: connect-template

- Score: `7.56`
- Phase: `phase-3`
- Effort: `medium`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Why selected:
  - selected as delegable slice with score 7.56
  - phase target is phase-3
  - estimated effort is medium
  - service signal: has docker packaging
  - service signal: exposes own API routes
  - service signal: has executable entrypoint
  - cqrs cluster size: 1
  - readiness signal: cross-module imports: 2
  - readiness signal: page imports: 0
  - readiness signal: external imports: 15
  - readiness signal: api endpoints used: 1
  - readiness signal: files: 27
  - readiness signal: lines: 1493

### Selected: connect-display

- Score: `4.00`
- Phase: `phase-3`
- Effort: `high`
- CQRS pattern: `n/a`
- Shared types package: `@semcod/contracts-types:custom-per-module`
- Why selected:
  - selected as delegable slice with score 4.00
  - phase target is phase-3
  - estimated effort is high
  - service signal: has docker packaging
  - service signal: has executable entrypoint
  - cqrs cluster size: 1
  - readiness signal: cross-module imports: 6
  - readiness signal: page imports: 0
  - readiness signal: external imports: 4
  - readiness signal: api endpoints used: 0
  - readiness signal: files: 23
  - readiness signal: lines: 4284
