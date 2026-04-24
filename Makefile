.PHONY: all proto zod python json sql clean generate-incremental proto-changed

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

# Incremental mode: only regenerate changed protos
generate-incremental: proto-changed
	python scripts/generate_incremental.py changed.txt

# Remove all generated artefacts (keeps the directory skeletons)
clean:
	find generated/ -type f ! -name '.gitkeep' -delete
