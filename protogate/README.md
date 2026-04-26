# Protogate Package README

This document describes how to use Protogate as a toolchain in medium and large projects.

## What Protogate owns

- Code generation engine for registry, JSON Schema, and Zod.
- Discovery tooling for migration and delegation plans.
- CLI orchestration.

## What Protogate does not own

- Business runtime of your domain services.
- Contract ownership policy decisions.
- Domain repository branching strategy.

## Recommended operating mode

Treat Protogate as deterministic build tooling:

1. Source of truth is contracts and typed schemas.
2. Generated artefacts are committed and never edited manually.
3. CI always runs generation and drift gate.

## CLI patterns

Local package usage:

python -m protogate.cli codegen registry <contracts-dir> --layers-root <repo-root>
python -m protogate.cli codegen json-schema --project-root <repo-root> --output-dir <schemas-dir> --module <module>
python -m protogate.cli codegen zod <schemas-dir> <zod-out-dir>

## Using Protogate in multiple repositories

For large refactors, use a federation model:

1. Contract hub repository
   - shared contract packages and release tags
2. Domain repositories
   - service-data, service-id, service-scenario, service-reports, service-manager
3. Workspace manifest
   - declares repos, versions, and codegen gates
4. Unified CI policy
   - codegen + drift check + tests in every repo

## Upgrade strategy

1. Pin Protogate version in each domain repository.
2. Upgrade one domain at a time.
3. Run codegen and drift checks before merge.
4. Publish migration notes for contract version changes.

## Failure recovery

If generated outputs are partially removed:

1. Purge generated outputs only.
2. Rebuild with full codegen pipeline.
3. Re-run drift gate.
4. Commit regenerated outputs with source changes.

## c2004 integration model

In c2004, wrappers in scripts/generate-*.py call Protogate CLI. The Makefile targets in make/codegen.mk are the operational contract for developers and CI.
