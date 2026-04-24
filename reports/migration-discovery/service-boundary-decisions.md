# Service Boundary Decision Rationale

Total recommended service candidates: 4

## Repeated decision signals

- `delivery mode: decompose-before-extract`: 4
- `backend scope: activities`: 4
- `backend scope: assignments`: 4
- `backend scope: auth`: 4
- `backend scope: backups`: 4
- `coordination target: base.module.ts`: 3
- `coordination target: connect-data`: 3
- `backend groups covered: 39`: 2
- `coordination target: connect-config`: 2
- `selected as service-boundary candidate with priority 456`: 1
- `service grouping target: service-config`: 1
- `page coverage: 34`: 1
- `backend groups covered: 40`: 1
- `cross-module targets: 8`: 1
- `shared dependency files: 66`: 1
- `iframe readiness: 24`: 1
- `coordination target: connect-font`: 1
- `coordination target: connect-menu`: 1
- `selected as service-boundary candidate with priority 282`: 1
- `service grouping target: service-scenario`: 1

## Recommended candidates

### Recommended: connect-config

- Service slug: `service-config`
- Priority: `456`
- Delivery mode: `decompose-before-extract`
- Iframe score: `24`
- Pages: `34`
- Why selected:
  - selected as service-boundary candidate with priority 456
  - delivery mode: decompose-before-extract
  - service grouping target: service-config
  - page coverage: 34
  - backend groups covered: 40
  - cross-module targets: 8
  - shared dependency files: 66
  - iframe readiness: 24
  - backend scope: activities
  - backend scope: assignments
  - backend scope: auth
  - backend scope: backups
  - coordination target: base.module.ts
  - coordination target: connect-data
  - coordination target: connect-font
  - coordination target: connect-menu

### Recommended: connect-scenario

- Service slug: `service-scenario`
- Priority: `282`
- Delivery mode: `decompose-before-extract`
- Iframe score: `32`
- Pages: `7`
- Why selected:
  - selected as service-boundary candidate with priority 282
  - delivery mode: decompose-before-extract
  - service grouping target: service-scenario
  - page coverage: 7
  - backend groups covered: 39
  - cross-module targets: 4
  - shared dependency files: 29
  - iframe readiness: 32
  - backend scope: activities
  - backend scope: assignments
  - backend scope: auth
  - backend scope: backups
  - coordination target: base.module.ts
  - coordination target: connect-operator
  - coordination target: module.interface.ts
  - coordination target: template

### Recommended: connect-test

- Service slug: `service-test`
- Priority: `266`
- Delivery mode: `decompose-before-extract`
- Iframe score: `0`
- Pages: `20`
- Why selected:
  - selected as service-boundary candidate with priority 266
  - delivery mode: decompose-before-extract
  - service grouping target: service-test
  - page coverage: 20
  - backend groups covered: 41
  - cross-module targets: 14
  - shared dependency files: 101
  - iframe-free extraction path
  - backend scope: activities
  - backend scope: assignments
  - backend scope: auth
  - backend scope: backups
  - coordination target: base.module.ts
  - coordination target: connect-config
  - coordination target: connect-data
  - coordination target: connect-id

### Recommended: connect-menu

- Service slug: `service-menu`
- Priority: `260`
- Delivery mode: `decompose-before-extract`
- Iframe score: `38`
- Pages: `1`
- Why selected:
  - selected as service-boundary candidate with priority 260
  - delivery mode: decompose-before-extract
  - service grouping target: service-menu
  - page coverage: 1
  - backend groups covered: 39
  - cross-module targets: 2
  - shared dependency files: 35
  - iframe readiness: 38
  - backend scope: activities
  - backend scope: assignments
  - backend scope: auth
  - backend scope: backups
  - coordination target: connect-config
  - coordination target: connect-data
