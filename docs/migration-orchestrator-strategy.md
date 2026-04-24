# Generic Migration Orchestrator Strategy

## Objective

Build a generic migration orchestrator around `protos` so that existing systems can be onboarded from different languages and architectural styles without rewriting the migration process for each repository.

The orchestrator should turn migration from an ad hoc activity into a repeatable pipeline:

1. discover repository structure
2. detect bounded candidates and service boundaries
3. classify migration strategy per slice
4. generate executable migration artifacts
5. enforce parity and archive-ready gates

## Why this is needed now

Current `protos` direction already establishes the target delegation model:

1. `protos` owns contracts, commands, queries, events, read models, and delegated UI runtime
2. legacy host keeps shell, auth/session bridge, and iframe routing only
3. migration should be driven by readiness scoring, service-boundary analysis, health checks, and cutover gates

The missing piece is a generic orchestration layer that can absorb inputs from different codebases, languages, and architectural layouts.

## Target capabilities

A complete migration orchestrator should support:

1. monoliths
2. modular monoliths
3. mixed backend + frontend repositories
4. backend-only services
5. frontend-heavy applications with shell + pages + services structure
6. gradual migrations where some slices become iframes, some become standalone services, and some require decomposition first

It should work across multiple language stacks through adapters, not through one hardcoded parser.

## Core design principle

The orchestrator should be built around a canonical migration model, while language and framework specifics live behind adapters.

### Canonical model

Each analyzed repository should be normalized into a common graph of:

- **module candidates**
- **frontend units**
- **backend route groups**
- **contracts**
- **data ownership signals**
- **cross-module dependencies**
- **shared dependency pressure**
- **delivery recommendations**
- **cutover and cleanup requirements**

This keeps orchestration generic while allowing detection to vary by language.

## Orchestrator architecture

### 1. Coordinator

Main responsibility:

- load config
- choose adapters
- run pipeline stages in order
- persist artifacts
- decide which gates can advance

Suggested future entrypoint:

- `scripts/legacy_bridge/run_arch_migration_discovery.py`

### 2. Adapter registry

Main responsibility:

- select analyzers by language/framework
- expose a uniform interface to the coordinator

Suggested adapter categories:

- **frontend source adapters**
- **backend route adapters**
- **dependency graph adapters**
- **contract adapters**
- **persistence/data adapters**
- **smoke/parity adapters**

### 3. Policy engine

Main responsibility:

- classify delivery mode
- classify extraction target
- choose execution phase
- decide if a candidate is `iframe-first`, `shell-first`, `backend-first`, `extract-service`, or `decompose-before-extract`

This should stay language-agnostic.

### 4. Artifact generators

Main responsibility:

- generate JSON artifacts
- generate Markdown execution plans
- generate slice blueprints
- generate cleanup checklists
- generate target structure proposals

### 5. Gates

Main responsibility:

- prevent unsafe cutover
- prevent premature legacy removal
- ensure archive only happens after parity and health pass

## Canonical pipeline

### Phase 0 - Repository profiling

Input:

- repository root
- optional config

Output:

- detected languages
- detected frameworks
- probable frontend roots
- probable backend roots
- probable route systems
- probable contract locations
- probable persistence layers

This phase answers: *what kind of system is this?*

### Phase 1 - Discovery

Output artifacts:

- candidate module list
- package/service/app roots
- dependency graph seeds

This phase should use repository heuristics such as:

- manifest files
- route files
- package boundaries
- app/module descriptors
- entrypoints
- Docker/build files

### Phase 2 - Boundary analysis

Output artifacts:

- frontend ownership map
- backend route ownership map
- cross-module dependency graph
- API usage graph
- service-boundary report

This is where the current `analyze_service_boundaries.py` belongs.

### Phase 3 - Candidate scoring

Output artifacts:

- migration readiness scores
- extraction target classification
- service candidate ranking
- merge hints

This is where the current `detect_migration_candidates.py` belongs.

### Phase 4 - Strategy selection

For each candidate or grouped component, choose one strategy:

- **`iframe-first`**
- **`shell-first`**
- **`backend-first`**
- **`extract-service`**
- **`decompose-before-extract`**
- **`shared-package-first`**
- **`strangler-proxy-first`**

This phase should be rule-based first, and only later optionally weighted by telemetry.

### Phase 5 - Planning

Output artifacts:

- delegation plan
- execution plan
- target structure
- cleanup checklist
- slice blueprint
- shared-package plan

This is where `generate_delegation_plan.py` and future planners belong.

### Phase 6 - Enablement

Output artifacts:

- slice scaffolds
- contract stubs
- frontend shell compatibility manifests
- bootstrap adapters
- health definitions

### Phase 7 - Validation and gates

Output artifacts:

- smoke status
- data bootstrap parity
- contract sync status
- archive-ready status

Future scripts should include:

- `archive_ready_gate.py`
- parity gate runner
- smoke aggregator

## Generic adapter model

Each adapter should expose structured capabilities instead of custom one-off outputs.

### Repository profile adapter

Detects:

- languages
- frameworks
- build tools
- dependency managers
- repo layout patterns

Examples:

- Python + FastAPI + SQLAlchemy
- TypeScript + React + Vite
- Java + Spring Boot
- C# + ASP.NET Core
- Go + Gin/Fiber
- Node + Express/Nest

### Frontend ownership adapter

Detects:

- page files
- route registrations
- module ownership
- imports
- API calls
- shared shell dependencies

### Backend route adapter

Detects:

- route groups
- route prefixes
- handler ownership
- imported domain/services/models layers
- transport surfaces

### Contract adapter

Detects:

- OpenAPI
- protobuf
- JSON schema
- ad hoc HTTP contract files
- event schemas

### Persistence adapter

Detects:

- database ownership hints
- migration files
- ORM models
- repository/services using specific tables

### Runtime gate adapter

Detects or executes:

- smoke checks
- health endpoints
- parity comparisons
- cutover rollback switches

## Language and framework support strategy

The orchestrator should never assume one stack. It should map source technologies to adapters.

### Python

Good first-class support:

- import graph via `ast`
- FastAPI/Flask route detection
- SQLAlchemy model detection
- Alembic migration detection

### TypeScript / JavaScript

Good first-class support:

- import graph via source regex or parser
- React/Vue/Nest/Express route detection
- fetch/axios/http client detection
- page/module ownership discovery

### Java / Kotlin

Support via source adapters:

- package graph
- Spring controller detection
- service/repository annotations
- Gradle/Maven module boundaries

### C#

Support via source adapters:

- ASP.NET controllers/minimal APIs
- project references
- solution/project graphs
- EF Core migrations

### Go

Support via source adapters:

- package imports
- router registrations
- service/repository directories
- module/workspace manifests

## Architecture coverage strategy

### Modular monolith

Primary signals:

- module directories
- internal import boundaries
- route ownership
- shared package pressure

### Layered monolith

Primary signals:

- controllers/routes
- services/application layer
- domain/model packages
- shared utility concentration

### Microfrontend + backend monolith

Primary signals:

- page ownership
- API group affinity
- shell/shared dependency pressure
- iframe suitability

### Service-oriented backend

Primary signals:

- deployable roots
- Docker/build manifests
- own routes
- own persistence
- own tests

## Canonical artifact schema

The orchestrator should produce interoperable artifacts with stable keys.

### Recommended artifact families

- **`repository-profile.json`**
- **`module-candidates.json`**
- **`service-boundaries.json`**
- **`shared-package-candidates.json`**
- **`delegation-plan.generated.json`**
- **`execution-plan.generated.json`**
- **`cleanup-checklist.generated.json`**
- **`archive-ready-report.json`**

### Required shared fields

- `module`
- `service_slug`
- `path`
- `kind`
- `score`
- `phase`
- `effort`
- `delivery_mode`
- `extraction_target`
- `iframe_candidate`
- `cross_module_targets`
- `backend_route_groups`
- `owned_files`
- `shared_dependency_files`
- `recommended_owner`

## Generic config model

The orchestrator should be configuration-driven.

Example shape:

```json
{
  "ignore_dirs": ["node_modules", ".git", "dist"],
  "frontend": {
    "roots": ["frontend/src", "apps/web/src"],
    "page_patterns": ["pages/**/*.page.ts", "routes/**/*.tsx"],
    "module_dir_names": ["modules", "features"],
    "module_prefix_rules": [
      {"prefix": "connect-", "segments": 2},
      {"prefix": "feature-", "segments": 2}
    ],
    "alias_roots": {
      "@/": "frontend/src",
      "@app/": "apps/web/src"
    }
  },
  "backend": {
    "route_roots": ["backend/api/routes/v3", "src/main/java", "src/Api"],
    "extensions": [".py", ".java", ".cs"]
  },
  "api": {
    "path_regex": "/api/v\\d+(?:/[A-Za-z0-9._{}\\-]+)+",
    "group_depth": 3
  },
  "analysis": {
    "top_services": 4,
    "shared_modules": ["shared", "shell", "common"]
  }
}
```

## Strategy selection rules

The orchestrator should choose migration mode from evidence, not assumptions.

### `iframe-first`

Best when:

- frontend ownership is clear
- cross-module coupling is low
- backend surface is small and bounded
- shell dependencies are limited

### `shell-first`

Best when:

- slice is meaningful but still relies on shared host concerns
- a direct iframe cutover would be too risky

### `backend-first`

Best when:

- domain logic and data ownership are already relatively isolated
- frontend is still too entangled

### `extract-service`

Best when:

- a service root is already deployable
- it owns routes, runtime, and persistence

### `decompose-before-extract`

Best when:

- one module has too many cross-targets
- domain boundaries are still muddy
- it acts as a glue module over multiple domains

### `shared-package-first`

Best when:

- multiple slices share duplicated frontend or backend support code
- extraction is blocked by shared helper churn

## Safety invariants

The orchestrator should enforce these invariants:

1. no legacy module is archived before parity gates pass
2. no direct import from legacy internals into `protos` runtime handlers
3. contracts must be versioned before cutover
4. bootstrap scripts must be idempotent
5. health endpoints and smoke checks must exist per delegated slice
6. cleanup plans must list guardrail files and companion modules

## How this maps to current `protos`

### Already present (Phase 1 ✅)

| Component | Purpose | Location |
|-----------|---------|----------|
| Candidate detection | Score modules for migration readiness | `scripts/detect_migration_candidates.py` |
| Service boundary analysis | Detect cross-module dependencies | `scripts/legacy_bridge/analyze_service_boundaries.py` |
| Delegation plan generator | Generate JSON/Markdown plans from candidates | `scripts/legacy_bridge/generate_delegation_plan.py` |
| Blueprint model | Shared slice model (runtime + docs) | `scripts/legacy_bridge/delegation_plan.py` |
| Slice registry | Runtime `DelegatedSlice` metadata & health | `gateway/delegation.py` |
| Health endpoints | Per-slice & aggregate health checks | `GET /health/modules/{slice}` |
| Delegation API | List slices, get metadata, check health | `/delegation/slices` |

### Runtime health contract

```python
# Per-slice health check
delegated_slice.health() -> {
  "status": "ok | degraded",
  "missing_required": ["contracts/x/v1/x.proto"],
  "contracts": [...],
  "read_models": [...],
  "frontend_assets": [...]
}
```

### Next orchestration steps (Phase 2-3)

1. add `run_arch_migration_discovery.py` – unified discovery pipeline
2. add repository profile detection stage
3. add shared package detection in `protos`
4. add a common artifact schema module (`report_models.py`)
5. add `archive_ready_gate.py`
6. add bootstrap/parity orchestration
7. ~~connect generated plans with executable slice metadata and runtime health~~ ✅ Phase 1 complete

## Recommended implementation roadmap

### Step 1

Create a single discovery orchestrator in `scripts/legacy_bridge/run_arch_migration_discovery.py` that runs:

- repository profiling
- candidate scoring
- service-boundary analysis
- delegation plan generation

### Step 2

Introduce a shared report model module, for example:

- `scripts/legacy_bridge/report_models.py`

This should normalize keys used by all migration artifacts.

### Step 3

Introduce framework-specific adapters incrementally:

- `python_fastapi`
- `typescript_react`
- `node_express`
- `java_spring`
- `dotnet_aspnet`
- `go_http`

### Step 4

Introduce execution gates:

- contract sync gate
- bootstrap parity gate
- smoke gate
- archive-ready gate

### Step 5

Move from document-only plans to executable orchestration where the orchestrator can:

- scaffold slices
- register health
- emit cleanup steps
- validate cutover readiness

## Non-goals

The orchestrator should not:

- try to auto-migrate arbitrary business logic without human review
- infer perfect domain boundaries from code alone
- directly delete legacy code as part of discovery
- hide migration risk behind a single numeric score

## Final strategy statement

The generic migration orchestrator for `protos` should be a config-driven, adapter-based pipeline that normalizes heterogeneous repositories into one canonical migration graph, then derives candidate scores, boundary analysis, strategy selection, execution plans, and safety gates from that graph.

That gives `protos` a path from:

- isolated scripts for one legacy repo

to:

- a reusable migration platform for multiple languages, frameworks, and architectural styles.
