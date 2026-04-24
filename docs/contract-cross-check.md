# Contract Enum Cross-Check

**Audience**: contract authors, ADR-010/ADR-012 reviewers, c2004 codegen
operators.

`protogate codegen registry` cross-checks CQRS contract JSON files
(`*.command.json`, `*.query.json`, `*.event.json`) against Pydantic
`Literal[...]` annotations in the Python module referenced by
`layers.python`. It catches a class of drift that broke ADR-012 Wave 2
in c2004, where a server emitted an enum value the contract did not
advertise, crashing the client decoder with an unknown-enum error.

The check is **AST-based** — no runtime Pydantic import, no side
effects. Implementation lives in
[`protogate/codegen/pydantic_cross_check.py`](../protogate/codegen/pydantic_cross_check.py).

## Motivation: the Wave 2 regression

In c2004 ADR-012 Wave 2, a service-id health endpoint was updated:

* **Pydantic** `Literal["ok", "degraded", "error"]` (widened)
* **Contract JSON** `"enum": ["ok", "error"]` (not updated)

The server started returning `"degraded"`. The Zod-based client
decoder rejected the response, surfacing as a 500 on every health
poll. No pre-commit gate caught the drift because contracts and
Pydantic models evolve in separate files and neither was authoritative
at check time.

The cross-check validator makes the two sides mutually accountable and
lets CI block the commit that introduces such a drift — or, with
`--fix-safe --auto-expand-output`, fix it automatically.

## Directional subset rules

An initial strict-equality check produced too many false positives
(benign refactors where one side was intentionally widened ahead of
the other). The current rules treat each block as a surface with a
direction:

| Block | Direction        | Rule                    | Verdict                                                       |
| ----- | ---------------- | ----------------------- | ------------------------------------------------------------- |
| `output`, `payload` | server → client | `pydantic ⊆ contract` | compatible                                                    |
| `output`, `payload` | server → client | `pydantic ⊋ contract` | **error** — client may crash on undeclared value              |
| `output`, `payload` | server → client | `contract ⊋ pydantic` | **warning** — dead code paths on client                       |
| `input`             | client → server | `contract ⊆ pydantic` | compatible                                                    |
| `input`             | client → server | `contract ⊋ pydantic` | **error** — server rejects valid-per-contract input (HTTP 422) |
| `input`             | client → server | `pydantic ⊋ contract` | compatible (intentional API restriction)                      |

**Error messages** carry the `block_kind` (`input`/`output`/`payload`)
and a one-line rationale, for example:

```
output field 'database' enum drift in GetServiceIdHealth.query.json:
  Pydantic Literal has extra values the contract does not advertise
  (server may return values the client cannot decode): degraded
```

## CLI usage

### `protogate codegen registry`

```bash
# 1. Report-only (use in CI)
protogate codegen registry contracts/ --check --cross-check-pydantic

# 2. Auto-fix warnings (always safe; JSON only)
protogate codegen registry contracts/ --cross-check-pydantic --fix-safe

# 3. Auto-fix warnings + expand output enums (opt-in; review diff!)
protogate codegen registry contracts/ --cross-check-pydantic \
    --fix-safe --auto-expand-output
```

### Flags

| Flag | Effect | Modifies disk? |
| --- | --- | --- |
| `--cross-check-pydantic`   | Run the cross-check; errors fail exit 1, warnings printed to stdout. | no |
| `--fix-safe`               | Additionally auto-apply **warning-level** drift fixes to contract JSON (remove enum values Pydantic never emits). | yes (JSON) |
| `--auto-expand-output`     | With `--fix-safe`: also expand output/payload contract enums to cover values Pydantic Literal emits. Never applied to `input` blocks. | yes (JSON) |

The Pydantic Python source is **never** modified by any of these flags.
All auto-fixes apply to contract JSON only.

## Auto-fix matrix

| Scenario                                 | `--fix-safe` | `--fix-safe --auto-expand-output` | Never auto-fixed                     |
| ---------------------------------------- | ------------ | ---------------------------------- | ------------------------------------ |
| `output contract ⊋ pydantic` (warning)   | ✏️ remove    | ✏️ remove                          |                                      |
| `output pydantic ⊋ contract` (error)     |              | ✏️ expand                          |                                      |
| `input contract ⊋ pydantic` (error)      |              |                                    | ❌ human decision (narrow vs loosen) |
| Missing Pydantic field                   |              |                                    | silent skip                          |
| `Literal` not found in `layers.python`   |              |                                    | silent skip                          |

The `--auto-expand-output` path is opt-in because it can silently
legitimise a server-side bug: if Pydantic happens to list an enum value
by accident, expanding the contract blesses that accident. The default
`--fix-safe` tier is always safe because removing unused advertised
values can never change server runtime behaviour.

## Integration in c2004

The c2004 repository wires the protogate CLI through a thin wrapper
(`scripts/generate-registry.py`) and exposes Makefile targets:

| Target                                | Protogate invocation                                   | CI?    |
| ------------------------------------- | ------------------------------------------------------ | ------ |
| `make codegen-registry-check`         | `--check --cross-check-pydantic`                       | yes    |
| `make codegen-registry-fix`           | `--cross-check-pydantic --fix-safe`                    | no     |
| `make codegen-registry-fix-aggressive`| `--cross-check-pydantic --fix-safe --auto-expand-output` | no     |

The CI gate (`codegen-registry-check`) does not perform auto-fixes.
Drift must be resolved by the author running one of the fix targets
locally and reviewing the diff.

## Output and exit codes

| Condition                              | Exit code | Prints                                             |
| -------------------------------------- | --------- | -------------------------------------------------- |
| Cross-check passed (no drift or warnings only) | 0 | `🔗 Cross-check passed`                           |
| Cross-check passed with warnings       | 0         | `⚠️  Cross-check warnings (non-blocking)` list    |
| Cross-check failed                     | 1         | `❌ Cross-check failed (contract enum vs Pydantic Literal)` list |
| Cross-check failed, `--fix-safe` off   | 1         | Above + `💡 Tip: rerun with --fix-safe ...`       |
| `--fix-safe` applied a fix             | 0 or 1    | `✏️  Auto-fixed {file}:` list                     |

## Python API

Every CLI behaviour is also available programmatically.

```python
from pathlib import Path
from protogate.codegen.pydantic_cross_check import (
    cross_check_contracts,
    apply_fixes_to_contract,
)

# Load contracts via protogate.codegen.registry.load_contracts, then:
pairs = cross_check_contracts(contracts, layers_root=Path("."))

for contract, result in pairs:
    if result.errors:
        print("FAIL", contract["_file"], result.errors)
    for warning in result.warnings:
        print("WARN", warning)

    # Apply only safe fixes:
    report = apply_fixes_to_contract(
        Path("contracts") / contract["_file"],
        result.auto_fixable_fixes(include_error_expansion=False),
    )
    for fix in report.applied:
        print("FIX", fix.describe())
```

`CrossCheckResult` carries:

* `ok: bool` — `False` iff there are any errors.
* `errors: list[str]` — human-readable error messages.
* `warnings: list[str]` — human-readable warnings.
* `fixes: list[ContractFix]` — structural fix proposals (see below).
* `auto_fixable_fixes(include_error_expansion)` — filter helper.

`ContractFix` describes a single JSON edit:

| Field         | Values                            |
| ------------- | --------------------------------- |
| `block_kind`  | `"input"` \| `"output"` \| `"payload"` |
| `field_path`  | dotted path inside the block (e.g. `"checks.database"`) |
| `action`      | `"remove_extra"` \| `"expand_contract"` |
| `values`      | list[str] — values to remove or add |
| `severity`    | `"warning"` \| `"error"`          |
| `rationale`   | one-line human explanation        |

`apply_fixes_to_contract` returns a `FixApplicationReport`:

| Field        | Meaning                                           |
| ------------ | ------------------------------------------------- |
| `applied`    | fixes that modified the file                       |
| `skipped`    | fixes excluded by safety policy or already in sync |
| `not_found`  | fixes whose `field_path` could not be resolved     |

## Known limitations

* **JSON pretty-print reformatting.** `apply_fixes_to_contract` rewrites
  the whole file via `json.dumps(..., indent=2, ensure_ascii=False)`.
  Contracts authored with inline object styling lose that formatting on
  first auto-fix. A one-time normalisation sweep
  (`make codegen-registry-fix` with no drift present) gets every file
  to the canonical form so subsequent runs produce clean diffs.
* **`Literal` resolution is class-scoped by field name.** If two
  distinct Pydantic classes in the same file annotate the same field
  name with different `Literal[...]` values, the validator uses the
  union. This is intentional: contracts cross-check a single JSON field
  against *any* matching Literal in the module.
* **No inheritance traversal.** Literals defined on a base class are
  picked up only if the class body literally contains the `AnnAssign`.
  Inheritance from an external module is not followed.
* **Silent skip on missing fields.** A contract field that has no
  matching Pydantic attribute is ignored (not flagged) to avoid false
  positives for response-wrapper fields like `success` or `timestamp`.

## Related code

* Validator: [`protogate/codegen/pydantic_cross_check.py`](../protogate/codegen/pydantic_cross_check.py)
* CLI wiring: [`protogate/cli.py`](../protogate/cli.py) (`codegen_registry`)
* Registry driver: [`protogate/codegen/registry.py`](../protogate/codegen/registry.py) (`run_cli`)
* Mirror validator in swop: `swop/registry/pydantic_cross_check.py` (semcod/inspect)
* c2004 wrapper: `scripts/generate-registry.py`, `make/codegen.mk`
