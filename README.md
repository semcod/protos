# protos

Reusable delegation platform for migrating bounded slices from legacy systems with minimal coupling.

## Architecture

**Protos owns:**

- Contracts (Protobuf)
- Commands & Queries (CQRS)
- Events & Read Models
- Delegated UI Runtime

**Legacy Host (c2004) owns:**

- Shell & Navigation
- Auth/Session Bridge
- Iframe Routing only

Each delegated module follows a vertical-slice template:

- `contracts/{slice}/v1/` - Protobuf contracts
- `gateway/{slice}_handler.py` - Command/query handlers
- Event store + read model adapters
- Frontend assets in `gateway/static/`
- Smoke tests & health endpoints

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run gateway
uvicorn gateway.main:app --reload --port 8080

# Or use Makefile
make gateway
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

## Delegation Workflow

1. **Generate candidate report** in c2004 (`detect_migration_candidates.py`)
2. **Generate delegation plan** in protos:

   ```bash
   python scripts/legacy_bridge/generate_delegation_plan.py \
     --input /path/to/c2004/module-candidates.json \
     --clusters /path/to/c2004/cqrs-pattern-clusters.json \
     --output-dir docs
   ```

3. **(Recommended) Run full discovery pipeline** in protos:

   ```bash
   python scripts/legacy_bridge/run_arch_migration_discovery.py \
     --repo-root /path/to/c2004 \
     --output-dir reports/migration-discovery \
     --delegation-limit 30
   ```

4. Pick top module from Phase-1
5. Implement full vertical slice in protos
6. Switch c2004 route to iframe host
7. Validate parity & archive legacy

## Project Structure

```text
protos/
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
│   ├── legacy_bridge/     # Migration tooling
│   │   ├── generate_delegation_plan.py
│   │   └── delegation_plan.py
│   └── event_store.py     # CQRS event store
├── tests/                 # Test suite
└── docs/                  # Generated plans
    ├── delegation-plan.generated.json
    └── delegation-plan.generated.md
```

## Key Components

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

## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.0.4-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$1.05-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-3.9h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $1.0500 (7 commits)
- 👤 **Human dev:** ~$386 (3.9h @ $100/h, 30min dedup)

Generated on 2026-04-24 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

## License

Licensed under Apache-2.0.
