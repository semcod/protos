.PHONY: all proto zod python json sql clean generate-incremental proto-changed \
        registry-register registry-check registry-list \
	proto-all gateway gateway-docker ci codegen-verify

# Default: run all generators (requires buf on PATH for the proto target)
all: proto zod python json sql

# Run buf generate (requires buf CLI: https://buf.build/docs/installation)
proto:
	buf generate

# TypeScript Zod schemas
zod:
	python scripts/generate_zod.py

# Pydantic Python models
python:
	python scripts/generate_pydantic.py

# JSON Schema (draft-07)
json:
	python scripts/generate_json_schema.py

# SQL DDL
sql:
	python scripts/generate_sql.py

# Detect changed proto files against main branch
proto-changed:
	git diff --name-only origin/main | grep ".proto" > changed.txt || true

# Incremental mode: only regenerate changed protogate artifacts
generate-incremental: proto-changed
	python scripts/generate_incremental.py changed.txt

# Remove all generated artefacts (keeps the directory skeletons)
clean:
	find generated/ -type f ! -name '.gitkeep' -delete

# ---------------------------------------------------------------------------
# Schema Registry targets
# ---------------------------------------------------------------------------
# Register the default proto file (contracts/user/v1/user.proto) in the registry
registry-register:
	python scripts/schema_registry.py register contracts/user/v1/user.proto

# Check compatibility of the default proto without registering
registry-check:
	python scripts/schema_registry.py check contracts/user/v1/user.proto

# List all schemas in the registry
registry-list:
	python scripts/schema_registry.py list

# ---------------------------------------------------------------------------
# Platform targets (gateway + full pipeline)
# ---------------------------------------------------------------------------

# Full generation: buf (gRPC stubs) + all custom generators
proto-all: proto zod python json sql

# Run the FastAPI gateway in development mode (hot-reload)
gateway:
	@pip install -q -r gateway/requirements.txt
	PYTHONPATH=. uvicorn gateway.main:app --reload --port 8080

# Build + run gateway via Docker
gateway-docker:
	docker build -f gateway/Dockerfile -t semcod-gateway .
	docker run --rm -p 8080:8080 semcod-gateway

# Full CI pipeline: lint → generate → test → registry check
ci:
	@echo "==> buf lint"
	buf lint || true
	@echo "==> proto-all (generate)"
	$(MAKE) proto-all
	@echo "==> pytest"
	pytest tests/ -v
	@echo "==> schema registry check (v1)"
	python scripts/schema_registry.py check contracts/user/v1/user.proto || true
	@echo "==> schema registry check (v2)"
	python scripts/schema_registry.py check contracts/user/v2/user.proto || true
	@echo "==> CI done ✓"

# Verify codegen guardrails and (optionally) check TS outputs for drift.
# Usage with real targets:
#   make codegen-verify TS_CODEGEN_SCRIPT=/abs/path/to/generate-typescript-types.py \
#        TS_CODEGEN_OUTPUTS="/abs/path/a.ts /abs/path/b.ts"
codegen-verify:
	@echo "==> pytest: TypeScript codegen guardrails"
	pytest tests/test_typescript_codegen.py tests/test_protogate_cli.py -q
	@if [ -n "$(TS_CODEGEN_SCRIPT)" ] && [ -n "$(TS_CODEGEN_OUTPUTS)" ]; then \
		echo "==> protogate ts-from-python --check"; \
		cmd="python -m protogate.cli codegen ts-from-python --script $(TS_CODEGEN_SCRIPT) --check"; \
		for out in $(TS_CODEGEN_OUTPUTS); do cmd="$$cmd --output $$out"; done; \
		eval "$$cmd"; \
	else \
		echo "==> skip ts-from-python drift check (set TS_CODEGEN_SCRIPT and TS_CODEGEN_OUTPUTS to enable)"; \
	fi

# ---------------------------------------------------------------------------
# Legacy Bridge targets
# ---------------------------------------------------------------------------

# Register legacy JSON schema
legacy-register:
	python scripts/legacy_registry.py register-json user.legacy contracts/legacy_bridge/user_legacy.schema.json
	python scripts/legacy_registry.py register-proto user.v1 contracts/legacy_bridge/user_legacy.v1.proto

# Diff legacy vs proto
diff-legacy:
	python scripts/legacy_registry.py diff user.legacy user.v1

# Generate detailed migration report
legacy-report:
	python scripts/legacy_registry.py report user.legacy user.v1

# List all schemas
legacy-list:
	python scripts/legacy_registry.py list

# Full sync check (fails if readiness < 1.0)
sync-check:
	@echo "==> Checking legacy vs proto sync"
	@PYTHONPATH=. python scripts/legacy_bridge/sync_check.py

# Bootstrap EventStore from Legacy DB
bootstrap-legacy:
	@echo "==> Bootstrapping EventStore from legacy.db"
	@PYTHONPATH=. python scripts/legacy_bridge/migrator.py
