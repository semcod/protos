# protogate

Migration tool and delegation platform for extracting bounded slices from legacy systems with minimal coupling. Built on SUMD + DOQL + testql + taskfile ecosystem.

## Architecture

**c2004 owns (c2004-first):**

- Contracts (Protobuf)
- Generators and schema registry
- Commands & Queries (CQRS) handlers
- Migration discovery and planning artifacts
- Shell, navigation, auth/session bridge, iframe routing

**protogate owns:**

- Delegation/execution tooling layer
- Runtime bridge for invoking migration tooling from c2004
- Gateway runtime and health endpoints

protogate is not the source-of-truth for migration contracts, discovery logic, or planning artifacts.

Each delegated module follows a vertical-slice template:

- `contracts/{slice}/v1/` - Protobuf contracts
- `gateway/{slice}_handler.py` - Command/query handlers
- Event store + read model adapters
- Frontend assets in `gateway/static/`
- Smoke tests & health endpoints

## Quick Start

### Using CLI (Recommended)

```bash
# Install protogate CLI
pip install -e .

# Generate all artifacts from contracts
protogate generate all

# Run specific generator
protogate generate python
protogate generate zod

# Schema registry operations
protogate registry check contracts/user/v1/user.proto
protogate registry list

# Run gateway
protogate gateway

# Run full CI pipeline
protogate ci
```

### Using Makefile (Legacy)

```bash
# Install dependencies
pip install -r requirements.txt

# Run gateway (development mode)
make gateway

# Run full CI pipeline
make ci
```

## API Overview

### Core Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/health` | Platform health + module aggregation |
| GET | `/health/modules` | All delegated slices status |
| GET | `/health/modules/{slice}` | Specific slice health |
| GET | `/delegation/slices` | List all delegated slices |
| GET | `/delegation/slices/{slice}` | Slice details & metadata |

### User Module (Live)

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/commands/user/create` | Create user |
| POST | `/commands/user/dual-create` | Dual-write with idempotency |
| POST | `/commands/user/{id}/change-email` | Change email |
| POST | `/commands/user/{id}/deactivate` | Deactivate user |
| GET | `/queries/user/{id}` | Get user state |
| GET | `/events` | Event stream |

### Search Module (Phase-1)

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/commands/search/index` | Index entry |
| GET | `/queries/search?q={query}` | Full-text search |

## Code Generation

The project provides multiple code generators from Protobuf contracts:

### Makefile Targets

| Target | Description |
| ------ | ----------- |
| `make proto` | Generate gRPC stubs via buf (requires buf CLI) |
| `make zod` | Generate TypeScript Zod schemas |
| `make python` | Generate Pydantic Python models |
| `make json` | Generate JSON Schema (draft-07) |
| `make sql` | Generate SQL DDL |
| `make proto-all` | Run all generators (proto + zod + python + json + sql) |
| `make proto-changed` | Detect changed proto files against main branch |
| `make generate-incremental` | Incremental regeneration (only changed proto files) |
| `make clean` | Remove all generated artifacts |

### Schema Registry

Manage schema versions and compatibility:

| Target | Description |
| ------ | ----------- |
| `make registry-register` | Register proto file in schema registry |
| `make registry-check` | Check compatibility without registering |
| `make registry-list` | List all schemas in registry |

### Legacy Bridge

Legacy schema migration and synchronization:

| Target | Description |
| ------ | ----------- |
| `make legacy-register` | Register legacy JSON schema + proto mapping |
| `make diff-legacy` | Diff legacy vs proto schemas |
| `make legacy-report` | Generate detailed migration report |
| `make legacy-list` | List all legacy schemas |
| `make sync-check` | Full sync check (fails if readiness < 1.0) |
| `make bootstrap-legacy` | Bootstrap EventStore from legacy DB |

### CI Pipeline

| Target | Description |
| ------ | ----------- |
| `make ci` | Full CI: lint → generate → test → registry check |

## Delegation Workflow

1. **Generate candidate report** in c2004 (`detect_migration_candidates.py`)
2. **Generate delegation plan** in protogate:

   ```bash
   python scripts/legacy_bridge/generate_delegation_plan.py \
     --input /path/to/c2004/module-candidates.json \
     --clusters /path/to/c2004/cqrs-pattern-clusters.json \
     --output-dir docs
   ```

3. **(Recommended) Run full discovery pipeline** in protogate:

   ```bash
   python scripts/legacy_bridge/run_arch_migration_discovery.py \
     --repo-root /path/to/c2004 \
     --output-dir reports/migration-discovery \
     --delegation-limit 30
   ```

4. Pick top module from Phase-1
5. Implement full vertical slice in protogate
6. Switch c2004 route to iframe host
7. Validate parity & archive legacy

## Project Structure

```text
protogate/
├── contracts/              # Protobuf contracts per slice
│   ├── user/v{1,2}/
│   ├── search/v1/
│   └── legacy_bridge/
├── gateway/                # FastAPI gateway
│   ├── main.py            # Entry point & routes
│   ├── delegation.py      # Slice registry & health
│   ├── user_handler.py    # User CQRS handlers
│   ├── search_handler.py  # Search CQRS handlers
│   └── static/            # Delegated UI assets
├── adapters/              # Legacy ↔ Proto adapters
├── scripts/               # Code generation & migration
│   ├── generate_zod.py    # TypeScript Zod generator
│   ├── generate_pydantic.py # Python Pydantic generator
│   ├── generate_json_schema.py # JSON Schema generator
│   ├── generate_sql.py    # SQL DDL generator
│   ├── generate_incremental.py # Incremental regeneration
│   ├── schema_registry.py # Proto schema registry
│   ├── legacy_registry.py # Legacy schema registry
│   ├── event_store.py     # CQRS event store
│   ├── conflict_resolver.py # Event conflict resolution
│   ├── dual_writer.py     # Dual-write pattern
│   ├── idempotency_store.py # Idempotency tracking
│   ├── vector_clock.py    # Vector clock for ordering
│   └── legacy_bridge/     # Migration tooling
│       ├── run_arch_migration_discovery.py # Full orchestrator
│       ├── detect_migration_candidates.py # Module scoring
│       ├── analyze_service_boundaries.py # Frontend/backend analysis
│       ├── detect_cqrs_pattern_clusters.py # CQRS pattern detection
│       ├── generate_migration_wave_plan.py # Wave planning
│       ├── delegation_plan.py # Delegation plan logic
│       ├── generate_delegation_plan.py # Plan generator
│       ├── migrator.py # Legacy to EventStore migration
│       ├── sync_check.py # Sync validation
│       └── diff_engine.py # Schema diffing
├── tests/                 # Test suite
└── docs/                  # Generated plans
    ├── delegation-plan.generated.json
    └── delegation-plan.generated.md
```

## Key Components

### Code Generators

- **Zod Generator** (`scripts/generate_zod.py`): TypeScript runtime validation schemas
- **Pydantic Generator** (`scripts/generate_pydantic.py`): Python data models
- **JSON Schema Generator** (`scripts/generate_json_schema.py`): Draft-07 JSON schemas
- **SQL Generator** (`scripts/generate_sql.py`): Database DDL
- **Incremental Generator** (`scripts/generate_incremental.py`): Regenerate only changed proto files

### Schema Registry

SQLite-backed schema registry with compatibility enforcement (`scripts/schema_registry.py`):

- Register schema versions with SHA256 hashing
- Check backward/forward compatibility
- List all registered schemas
- Prevent breaking changes

### Legacy Bridge

Comprehensive migration tooling for legacy systems:

- **Migration Discovery Orchestrator**: Full pipeline profiling, candidate detection, service boundary analysis, CQRS pattern clustering, and delegation planning
- **Migration Candidate Detection**: Score modules by extraction suitability, identify service boundaries
- **Service Boundary Analysis**: Frontend module detection, backend route grouping, iframe suitability assessment
- **CQRS Pattern Clustering**: Classify modules by command/event patterns (data-grid, reports, manager, config)
- **Migration Wave Planning**: Generate phased extraction plans with effort estimation
- **Legacy Schema Registry**: Track legacy JSON schemas and proto mappings
- **Diff Engine**: Compare legacy vs proto schemas for compatibility
- **Migrator**: Bootstrap EventStore from legacy databases
- **Sync Check**: Validate legacy-proto synchronization readiness

### CQRS Infrastructure

- **Event Store** (`scripts/event_store.py`): Append-only event store with SQLite, optimistic concurrency, snapshots, stream merging
- **Conflict Resolver** (`scripts/conflict_resolver.py`): Last-Write-Wins and merge strategies for concurrent events
- **Vector Clock** (`scripts/vector_clock.py`): Causal ordering and conflict detection
- **Dual Writer** (`scripts/dual_writer.py`): Dual-write pattern for legacy migration
- **Idempotency Store** (`scripts/idempotency_store.py`): Prevent duplicate command processing

### DelegatedSlice Registry

Runtime model for slice metadata in `gateway/delegation.py`:

```python
DelegatedSlice(
    name="search",
    phase="phase-1",           # phase-1 | phase-2 | live
    backend="delegated",
    frontend="static",         # none | static | planned
    contract_paths=("contracts/search/v1/search.proto",),
    command_routes=("/commands/search/index",),
    query_routes=("/queries/search",),
    smoke_checks=("/health", "/queries/search?q=test"),
)
```

### Health Checks

Per-slice health validates:

- Contract files exist
- Read model assets present
- Frontend assets (if required)

Returns `ok` or `degraded` with missing requirements listed.

## Deployment

### Docker Compose

```bash
# Build and run all services
docker-compose up

# Services:
# - generator: Proto code generation
# - gateway: FastAPI gateway (port 8080)
```

### Gateway Docker

```bash
# Build gateway image
docker build -f gateway/Dockerfile -t semcod-gateway .

# Run gateway container
docker run --rm -p 8080:8080 semcod-gateway
```

Or use Makefile:

```bash
make gateway-docker
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | LLM model for AI-assisted features |
| `PFIX_AUTO_APPLY` | `true` | Apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | Auto pip/uv install dependencies |
| `PFIX_AUTO_RESTART` | `false` | Restart after fix |
| `PFIX_MAX_RETRIES` | `3` | Max retry attempts |
| `PFIX_ENABLED` | `true` | Enable auto-fix features |
| `PFIX_GIT_COMMIT` | `false` | Auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | Commit message prefix |

## Testing

### TestQL Scenarios

Auto-generated API smoke tests in `testql-scenarios/generated-api-smoke.testql.toon.yaml`:

- Health checks
- Delegation slice endpoints
- Command/query endpoints
- Event streaming

### Pytest

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_event_store.py -v
```

## Release Management

- **Versioning**: Semantic versioning (semver)
- **Commits**: Conventional commits with scope=`protogate`
- **Changelog**: Keep-a-changelog format
- **Build strategies**: Python, Node.js, Rust
- **Version files**: `VERSION`, generated package versions

## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.10-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$3.00-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-10.5h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $3.0000 (20 commits)
- 👤 **Human dev:** ~$1045 (10.5h @ $100/h, 30min dedup)

Generated on 2026-04-24 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

## License

Licensed under Apache-2.0.
