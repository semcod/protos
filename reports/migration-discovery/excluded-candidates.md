# Excluded Delegation Candidates

Total excluded candidates: 11

## Exclusion reasons

- `not marked as service candidate and lacks delegated slice naming`: 11
- `recommended owner is legacy-host`: 6
- `extraction target is monolith-fragment`: 6
- `technical or container-level module`: 5
- `technical or container-level path`: 4
- `hidden or temporary module name`: 1
- `top-level application should not be delegated as a slice`: 1

## Excluded candidates

### Excluded: .swop

- Path: `modules/.swop`
- Kind: `component`
- Score: `55.00`
- Phase: `phase-2`
- Reasons:
  - hidden or temporary module name
  - recommended owner is legacy-host
  - extraction target is monolith-fragment
  - not marked as service candidate and lacks delegated slice naming

### Excluded: project

- Path: `modules/project`
- Kind: `component`
- Score: `55.00`
- Phase: `phase-2`
- Reasons:
  - technical or container-level module
  - recommended owner is legacy-host
  - extraction target is monolith-fragment
  - not marked as service candidate and lacks delegated slice naming

### Excluded: testql-scenarios

- Path: `modules/testql-scenarios`
- Kind: `component`
- Score: `55.00`
- Phase: `phase-2`
- Reasons:
  - recommended owner is legacy-host
  - extraction target is monolith-fragment
  - not marked as service candidate and lacks delegated slice naming

### Excluded: site

- Path: `site`
- Kind: `frontend`
- Score: `46.65`
- Phase: `phase-3`
- Reasons:
  - technical or container-level module
  - technical or container-level path
  - not marked as service candidate and lacks delegated slice naming

### Excluded: env

- Path: `env`
- Kind: `component`
- Score: `40.00`
- Phase: `phase-3`
- Reasons:
  - technical or container-level module
  - technical or container-level path
  - recommended owner is legacy-host
  - extraction target is monolith-fragment
  - not marked as service candidate and lacks delegated slice naming

### Excluded: encoder-control

- Path: `services/encoder-control`
- Kind: `service`
- Score: `39.00`
- Phase: `phase-3`
- Reasons:
  - recommended owner is legacy-host
  - extraction target is monolith-fragment
  - not marked as service candidate and lacks delegated slice naming

### Excluded: desktop

- Path: `desktop`
- Kind: `frontend`
- Score: `35.00`
- Phase: `phase-3`
- Reasons:
  - recommended owner is legacy-host
  - extraction target is monolith-fragment
  - not marked as service candidate and lacks delegated slice naming

### Excluded: fleet-workshop-manager

- Path: `services/backend/fleet-workshop-manager`
- Kind: `service`
- Score: `27.50`
- Phase: `phase-3`
- Reasons:
  - not marked as service candidate and lacks delegated slice naming

### Excluded: backend

- Path: `backend`
- Kind: `application`
- Score: `0.00`
- Phase: `phase-3`
- Reasons:
  - technical or container-level module
  - technical or container-level path
  - top-level application should not be delegated as a slice
  - not marked as service candidate and lacks delegated slice naming

### Excluded: fleet-data-manager

- Path: `services/backend/fleet-data-manager`
- Kind: `service`
- Score: `0.00`
- Phase: `phase-3`
- Reasons:
  - not marked as service candidate and lacks delegated slice naming

### Excluded: frontend

- Path: `frontend`
- Kind: `frontend`
- Score: `0.00`
- Phase: `phase-3`
- Reasons:
  - technical or container-level module
  - technical or container-level path
  - not marked as service candidate and lacks delegated slice naming
