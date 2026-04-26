# protos-runtime

Lightweight runtime library extracted from `semcod/protos`. Provides:

- **`protos_runtime.search_index.SearchIndex`** — SQLite FTS5 read model for the search vertical slice.
- **`protos_runtime.models.search_v1`** — Pydantic contract types (`IndexEntryCommand`, `SearchResponse`, etc).
- **`protos_runtime.models.identification_v1`** — Pydantic contract types for identification domain.

Designed to be embedded by downstream applications (e.g. `maskservice/c2004`) without requiring the full `protogate` distribution (gateway, code-generators, migrators).

## Installation (editable, monorepo-local)

```bash
pip install -e /path/to/semcod/protos/packages/protos-runtime-py
```

## Usage

```python
from protos_runtime.search_index import SearchIndex
from protos_runtime.models.search_v1 import IndexEntryCommand

index = SearchIndex(db_path="my_app.db")
cmd = IndexEntryCommand(
    id="abc-123",
    title="Example",
    category="docs",
    content="Hello world",
    metadata={"source": "manual"},
)
index.upsert_entry(**cmd.model_dump())

results = index.search("Hello")
```

## Source of truth

This package is a **copy** of source files from the parent `semcod/protos` monorepo:

- `src/protos_runtime/search_index.py` ← `protos/scripts/search_index.py`
- `src/protos_runtime/models/search_v1.py` ← `protos/generated/python/search_v1_models.py`
- `src/protos_runtime/models/identification_v1.py` ← `protos/generated/python/identification_v1_models.py`

If the originals change, this package must be re-synced. A future task may automate the sync via `protogate generate --target=runtime-package`.
