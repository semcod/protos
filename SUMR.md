# protogate

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `protogate`
- **version**: `0.1.1`
- **python_requires**: `>=3.9`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, requirements.txt, Makefile, testql(1), app.doql.less, goal.yaml, .env.example, docker-compose.yml, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: protogate;
  version: 0.1.1;
}

dependencies {
  runtime: "protobuf>=4.25.0, pydantic>=2.0.0, pydantic[email]>=2.0.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
  dev: "pytest>=7.0.0, pytest-cov>=4.0.0, black>=23.0.0, ruff>=0.1.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="protogate"] {

}

workflow[name="proto"] {
  trigger: manual;
  step-1: run cmd=buf generate;
}

workflow[name="zod"] {
  trigger: manual;
  step-1: run cmd=python scripts/generate_zod.py;
}

workflow[name="python"] {
  trigger: manual;
  step-1: run cmd=python scripts/generate_pydantic.py;
}

workflow[name="json"] {
  trigger: manual;
  step-1: run cmd=python scripts/generate_json_schema.py;
}

workflow[name="sql"] {
  trigger: manual;
  step-1: run cmd=python scripts/generate_sql.py;
}

workflow[name="proto-changed"] {
  trigger: manual;
  step-1: run cmd=git diff --name-only origin/main | grep ".proto" > changed.txt || true;
}

workflow[name="generate-incremental"] {
  trigger: manual;
  step-1: run cmd=python scripts/generate_incremental.py changed.txt;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=find generated/ -type f ! -name '.gitkeep' -delete;
}

workflow[name="registry-register"] {
  trigger: manual;
  step-1: run cmd=python scripts/schema_registry.py register contracts/user/v1/user.proto;
}

workflow[name="registry-check"] {
  trigger: manual;
  step-1: run cmd=python scripts/schema_registry.py check contracts/user/v1/user.proto;
}

workflow[name="registry-list"] {
  trigger: manual;
  step-1: run cmd=python scripts/schema_registry.py list;
}

workflow[name="proto-all"] {
  trigger: manual;
  step-1: depend target=proto;
  step-2: depend target=zod;
  step-3: depend target=python;
  step-4: depend target=json;
  step-5: depend target=sql;
}

workflow[name="gateway"] {
  trigger: manual;
  step-1: run cmd=pip install -q -r gateway/requirements.txt;
  step-2: run cmd=PYTHONPATH=. uvicorn gateway.main:app --reload --port 8080;
}

workflow[name="gateway-docker"] {
  trigger: manual;
  step-1: run cmd=docker build -f gateway/Dockerfile -t semcod-gateway .;
  step-2: run cmd=docker run --rm -p 8080:8080 semcod-gateway;
}

workflow[name="ci"] {
  trigger: manual;
  step-1: run cmd=echo "==> buf lint";
  step-2: run cmd=buf lint || true;
  step-3: run cmd=echo "==> proto-all (generate)";
  step-4: run cmd=$(MAKE) proto-all;
  step-5: run cmd=echo "==> pytest";
  step-6: run cmd=pytest tests/ -v;
  step-7: run cmd=echo "==> schema registry check (v1)";
  step-8: run cmd=python scripts/schema_registry.py check contracts/user/v1/user.proto || true;
  step-9: run cmd=echo "==> schema registry check (v2)";
  step-10: run cmd=python scripts/schema_registry.py check contracts/user/v2/user.proto || true;
  step-11: run cmd=echo "==> CI done ✓";
}

workflow[name="legacy-register"] {
  trigger: manual;
  step-1: run cmd=python scripts/legacy_registry.py register-json user.legacy contracts/legacy_bridge/user_legacy.schema.json;
  step-2: run cmd=python scripts/legacy_registry.py register-proto user.v1 contracts/legacy_bridge/user_legacy.v1.proto;
}

workflow[name="diff-legacy"] {
  trigger: manual;
  step-1: run cmd=python scripts/legacy_registry.py diff user.legacy user.v1;
}

workflow[name="legacy-report"] {
  trigger: manual;
  step-1: run cmd=python scripts/legacy_registry.py report user.legacy user.v1;
}

workflow[name="legacy-list"] {
  trigger: manual;
  step-1: run cmd=python scripts/legacy_registry.py list;
}

workflow[name="sync-check"] {
  trigger: manual;
  step-1: run cmd=echo "==> Checking legacy vs proto sync";
  step-2: run cmd=PYTHONPATH=. python scripts/legacy_bridge/sync_check.py;
}

workflow[name="bootstrap-legacy"] {
  trigger: manual;
  step-1: run cmd=echo "==> Bootstrapping EventStore from legacy.db";
  step-2: run cmd=PYTHONPATH=. python scripts/legacy_bridge/migrator.py;
}

deploy {
  target: docker-compose;
  compose_file: docker-compose.yml;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.9;
}
```

## Workflows

## Dependencies

### Runtime

```text markpact:deps python
protobuf>=4.25.0
pydantic>=2.0.0
pydantic[email]>=2.0.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

### Development

```text markpact:deps python scope=dev
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
ruff>=0.1.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Call Graph

*210 nodes · 188 edges · 31 modules · CC̄=1.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `run_discovery` *(in scripts.legacy_bridge.run_arch_migration_discovery)* | 12 ⚠ | 1 | 77 | **78** |
| `main` *(in scratch.swop_scan_c2004)* | 17 ⚠ | 0 | 53 | **53** |
| `build_delegation_decision_report` *(in scripts.legacy_bridge.run_arch_migration_discovery)* | 19 ⚠ | 1 | 43 | **44** |
| `analyze_repository` *(in scripts.legacy_bridge.detect_cqrs_pattern_clusters)* | 20 ⚠ | 2 | 37 | **39** |
| `_calculate_module_stats` *(in scripts.legacy_bridge.analyze_service_boundaries)* | 26 ⚠ | 1 | 35 | **36** |
| `get_candidate_exclusion_reasons` *(in scripts.legacy_bridge.candidate_selection)* | 14 ⚠ | 2 | 33 | **35** |
| `render_markdown` *(in scripts.legacy_bridge.delegation_plan)* | 8 | 1 | 33 | **34** |
| `discover_candidate_paths` *(in scripts.detect_migration_candidates)* | 20 ⚠ | 1 | 33 | **34** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/protos
# nodes: 210 | edges: 188 | modules: 31
# CC̄=1.8

HUBS[20]:
  scripts.legacy_bridge.run_arch_migration_discovery.run_discovery
    CC=12  in:1  out:77  total:78
  scratch.swop_scan_c2004.main
    CC=17  in:0  out:53  total:53
  scripts.legacy_bridge.run_arch_migration_discovery.build_delegation_decision_report
    CC=19  in:1  out:43  total:44
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository
    CC=20  in:2  out:37  total:39
  scripts.legacy_bridge.analyze_service_boundaries._calculate_module_stats
    CC=26  in:1  out:35  total:36
  scripts.legacy_bridge.candidate_selection.get_candidate_exclusion_reasons
    CC=14  in:2  out:33  total:35
  scripts.legacy_bridge.delegation_plan.render_markdown
    CC=8  in:1  out:33  total:34
  scripts.detect_migration_candidates.discover_candidate_paths
    CC=20  in:1  out:33  total:34
  scripts.legacy_bridge.run_arch_migration_discovery.profile_repository
    CC=18  in:1  out:33  total:34
  scripts.legacy_bridge.generate_migration_wave_plan.main
    CC=8  in:0  out:33  total:33
  scripts.legacy_bridge.generate_migration_wave_plan.build_waves
    CC=15  in:2  out:31  total:33
  scripts.legacy_bridge.analyze_service_boundaries.build_ts_index
    CC=10  in:1  out:30  total:31
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.main
    CC=10  in:0  out:31  total:31
  scripts.legacy_bridge.generate_delegation_plan.main
    CC=6  in:0  out:29  total:29
  scripts.legacy_bridge.run_arch_migration_discovery.main
    CC=8  in:0  out:29  total:29
  scripts.legacy_bridge.analyze_service_boundaries.build_service_blueprint_markdown
    CC=11  in:2  out:26  total:28
  protogate.cli._batch_generate
    CC=9  in:2  out:24  total:26
  scripts.legacy_bridge.swop_integration.run_swop_pipeline
    CC=13  in:0  out:25  total:25
  scripts.legacy_bridge.delegation_plan.build_output_row
    CC=6  in:3  out:22  total:25
  scripts.generate_incremental.main
    CC=11  in:0  out:24  total:24

MODULES:
  adapters.legacy_to_proto.user_adapter  [2 funcs]
    legacy_to_proto  CC=1  out:11
    wrap_for_event_store  CC=1  out:1
  gateway.delegation  [3 funcs]
    get_delegated_slice  CC=1  out:1
    get_delegation_health  CC=6  out:4
    list_delegated_slices  CC=2  out:3
  gateway.main  [14 funcs]
    cmd_change_email  CC=1  out:4
    cmd_create_user  CC=1  out:5
    cmd_deactivate_user  CC=1  out:4
    cmd_dual_create_user  CC=1  out:5
    cmd_index_search_entry  CC=1  out:3
    delegation_slice_detail  CC=2  out:4
    delegation_slices  CC=1  out:2
    health  CC=1  out:2
    health_module  CC=2  out:4
    health_modules  CC=1  out:2
  gateway.search_handler  [2 funcs]
    handle_index_entry  CC=1  out:2
    handle_search  CC=1  out:2
  gateway.sse  [4 funcs]
    event_generator  CC=6  out:11
    push_to_subscribers  CC=4  out:5
    subscribe  CC=1  out:3
    unsubscribe  CC=2  out:3
  gateway.user_handler  [6 funcs]
    handle_change_email  CC=1  out:2
    handle_create_user  CC=1  out:4
    handle_deactivate_user  CC=1  out:2
    handle_dual_write_user  CC=1  out:4
    handle_get_user  CC=2  out:2
    handle_list_events  CC=3  out:3
  protogate.cli  [11 funcs]
    _batch_generate  CC=9  out:24
    cmd_ci  CC=1  out:1
    cmd_clean  CC=1  out:1
    cmd_discovery  CC=7  out:10
    cmd_gateway  CC=2  out:1
    cmd_generate  CC=8  out:2
    cmd_generate_pydantic  CC=1  out:1
    cmd_generate_zod  CC=1  out:1
    cmd_legacy  CC=7  out:2
    cmd_registry  CC=6  out:3
  scratch.swop_scan_c2004  [6 funcs]
    _base_names  CC=7  out:9
    _kind_by_base  CC=3  out:0
    _kind_by_suffix  CC=4  out:1
    collect_ground_truth  CC=9  out:12
    main  CC=17  out:53
    run_swop_scan  CC=1  out:2
  scripts.conflict_resolver  [2 funcs]
    _check_field_conflicts  CC=8  out:5
    _field_effects  CC=2  out:3
  scripts.detect_migration_candidates  [19 funcs]
    _analyze_file_content  CC=18  out:15
    _check_candidate_flags  CC=6  out:11
    analyze_candidate  CC=12  out:12
    analyze_repository  CC=4  out:13
    build_output_row  CC=2  out:2
    classify_extraction_target  CC=19  out:12
    count_api_routes  CC=3  out:5
    count_outbound_api_calls  CC=2  out:3
    discover_candidate_paths  CC=20  out:33
    extract_python_imports  CC=6  out:8
  scripts.event_store  [1 funcs]
    __init__  CC=1  out:1
  scripts.generate_incremental  [8 funcs]
    _stem  CC=1  out:2
    _write  CC=2  out:7
    file_hash  CC=2  out:6
    load_cache  CC=2  out:3
    main  CC=11  out:24
    regenerate  CC=1  out:11
    save_cache  CC=1  out:3
    should_regenerate  CC=1  out:2
  scripts.generate_json_schema  [2 funcs]
    generate  CC=6  out:3
    main  CC=3  out:10
  scripts.generate_pydantic  [4 funcs]
    _flatten_enums  CC=1  out:8
    _flatten_messages  CC=1  out:5
    generate  CC=10  out:16
    main  CC=3  out:9
  scripts.generate_sql  [3 funcs]
    _table_name  CC=1  out:2
    generate_sql  CC=6  out:6
    main  CC=3  out:9
  scripts.generate_zod  [4 funcs]
    _flatten_enums  CC=1  out:8
    _flatten_messages  CC=1  out:5
    main  CC=3  out:9
    to_zod  CC=7  out:15
  scripts.legacy_bridge.analyze_service_boundaries  [46 funcs]
    _append_execution_plan_section  CC=4  out:6
    _append_frontend_modules_section  CC=4  out:6
    _append_merge_hints_section  CC=3  out:3
    _append_recommended_candidates_section  CC=4  out:5
    _append_service_components_section  CC=4  out:6
    _apply_merge_hints  CC=8  out:7
    _build_component_row  CC=18  out:21
    _build_cqrs_endpoint_templates  CC=6  out:9
    _build_eligible_modules  CC=4  out:0
    _build_module_index  CC=5  out:4
  scripts.legacy_bridge.candidate_selection  [3 funcs]
    get_candidate_exclusion_reasons  CC=14  out:33
    is_delegable_candidate  CC=1  out:1
    parse_score  CC=2  out:2
  scripts.legacy_bridge.delegation_plan  [7 funcs]
    _normalize_shared_types_package  CC=5  out:3
    _to_float  CC=2  out:1
    build_output_row  CC=6  out:22
    build_slice_blueprint  CC=1  out:2
    build_steps  CC=1  out:1
    render_markdown  CC=8  out:33
    to_slice_name  CC=1  out:4
  scripts.legacy_bridge.detect_cqrs_pattern_clusters  [9 funcs]
    analyze_repository  CC=20  out:37
    assign_clusters  CC=9  out:14
    deep_merge  CC=4  out:6
    load_config  CC=3  out:5
    main  CC=10  out:31
    normalize_config  CC=2  out:1
    parse_args  CC=1  out:8
    read_text  CC=3  out:2
    shared_tokens_for_module  CC=4  out:5
  scripts.legacy_bridge.diff_engine  [1 funcs]
    diff_fields  CC=12  out:19
  scripts.legacy_bridge.generate_delegation_plan  [4 funcs]
    dedupe_candidates  CC=6  out:8
    load_clusters  CC=9  out:10
    main  CC=6  out:29
    parse_args  CC=1  out:9
  scripts.legacy_bridge.generate_migration_wave_plan  [5 funcs]
    build_waves  CC=15  out:31
    load_json  CC=3  out:3
    main  CC=8  out:33
    parse_args  CC=1  out:8
    resolve_path  CC=2  out:2
  scripts.legacy_bridge.migrator  [2 funcs]
    main  CC=1  out:7
    migrate_users  CC=3  out:6
  scripts.legacy_bridge.normalizer  [2 funcs]
    normalize_json_schema  CC=3  out:10
    normalize_proto_ast  CC=2  out:5
  scripts.legacy_bridge.report_rendering  [9 funcs]
    _append_artifacts_table  CC=2  out:4
    _append_detail_section  CC=5  out:12
    _append_reason_counts_section  CC=4  out:3
    _append_simple_list_section  CC=3  out:3
    _format_detail_value  CC=5  out:3
    render_delegation_decisions_markdown  CC=1  out:5
    render_excluded_candidates_markdown  CC=2  out:5
    render_service_boundary_decisions_markdown  CC=1  out:5
    render_summary_markdown  CC=6  out:20
  scripts.legacy_bridge.run_arch_migration_discovery  [11 funcs]
    _parse_score  CC=1  out:1
    build_delegation_decision_report  CC=19  out:43
    build_delegation_plan  CC=5  out:7
    build_excluded_candidates_report  CC=5  out:18
    main  CC=8  out:29
    parse_args  CC=1  out:11
    profile_repository  CC=18  out:33
    resolve_output_dir  CC=2  out:2
    run_discovery  CC=12  out:77
    write_json  CC=1  out:2
  scripts.legacy_bridge.swop_integration  [7 funcs]
    _context_score  CC=18  out:19
    _eligible_groups  CC=6  out:5
    _group_match_score  CC=11  out:13
    _name_tokens  CC=10  out:8
    _normalize_token  CC=7  out:7
    infer_contexts_from_service_boundaries  CC=15  out:21
    run_swop_pipeline  CC=13  out:25
  scripts.legacy_bridge.sync_check  [1 funcs]
    main  CC=6  out:12
  scripts.parse_proto  [6 funcs]
    _handle_block_end  CC=6  out:5
    _handle_enum_start  CC=3  out:5
    _handle_message_start  CC=3  out:5
    _parse_top_level_declarations  CC=3  out:5
    _to_dict  CC=5  out:5
    parse_proto  CC=15  out:14
  scripts.schema_registry  [6 funcs]
    __init__  CC=1  out:1
    register  CC=10  out:18
    _connect  CC=1  out:5
    _diff_messages  CC=19  out:16
    _sha256_file  CC=2  out:6
    check_compatibility  CC=6  out:2

EDGES:
  gateway.sse.push_to_subscribers → gateway.sse.unsubscribe
  gateway.sse.event_generator → gateway.sse.unsubscribe
  gateway.delegation.get_delegation_health → gateway.delegation.list_delegated_slices
  scripts.parse_proto._handle_block_end → scripts.parse_proto._to_dict
  scripts.parse_proto.parse_proto → scripts.parse_proto._handle_message_start
  scripts.parse_proto.parse_proto → scripts.parse_proto._handle_enum_start
  scripts.parse_proto.parse_proto → scripts.parse_proto._handle_block_end
  scripts.parse_proto.parse_proto → scripts.parse_proto._to_dict
  scripts.parse_proto.parse_proto → scripts.parse_proto._parse_top_level_declarations
  scripts.generate_incremental.should_regenerate → scripts.generate_incremental.file_hash
  scripts.generate_incremental.regenerate → scripts.generate_incremental._stem
  scripts.generate_incremental.regenerate → scripts.parse_proto.parse_proto
  scripts.generate_incremental.regenerate → scripts.generate_incremental._write
  scripts.generate_incremental.regenerate → scripts.generate_zod.to_zod
  scripts.generate_incremental.main → scripts.generate_incremental.load_cache
  scripts.generate_incremental.main → scripts.generate_incremental.should_regenerate
  scripts.generate_incremental.main → scripts.generate_incremental.save_cache
  scripts.generate_sql.generate_sql → scripts.generate_sql._table_name
  scripts.generate_sql.main → scripts.parse_proto.parse_proto
  scripts.generate_sql.main → scripts.generate_sql.generate_sql
  scripts.schema_registry.check_compatibility → scripts.schema_registry._diff_messages
  scripts.schema_registry.SchemaRegistry.__init__ → scripts.schema_registry._connect
  scripts.schema_registry.SchemaRegistry.register → scripts.parse_proto.parse_proto
  scripts.schema_registry.SchemaRegistry.register → scripts.schema_registry._sha256_file
  scripts.generate_json_schema.main → scripts.parse_proto.parse_proto
  scripts.generate_json_schema.main → scripts.generate_json_schema.generate
  scripts.generate_pydantic.generate → scripts.generate_pydantic._flatten_enums
  scripts.generate_pydantic.generate → scripts.generate_pydantic._flatten_messages
  scripts.generate_pydantic.main → scripts.parse_proto.parse_proto
  scripts.generate_pydantic.main → scripts.generate_pydantic.generate
  scripts.conflict_resolver.ConflictResolver._check_field_conflicts → scripts.conflict_resolver._field_effects
  scripts.event_store.EventStore.__init__ → scripts.schema_registry._connect
  scripts.generate_zod.to_zod → scripts.generate_zod._flatten_enums
  scripts.generate_zod.to_zod → scripts.generate_zod._flatten_messages
  scripts.generate_zod.main → scripts.parse_proto.parse_proto
  scripts.generate_zod.main → scripts.generate_zod.to_zod
  scripts.legacy_bridge.delegation_plan.build_steps → scripts.legacy_bridge.delegation_plan.to_slice_name
  scripts.legacy_bridge.delegation_plan.build_slice_blueprint → scripts.legacy_bridge.delegation_plan.to_slice_name
  scripts.legacy_bridge.delegation_plan.build_slice_blueprint → scripts.legacy_bridge.delegation_plan.build_steps
  scripts.legacy_bridge.delegation_plan.build_output_row → scripts.legacy_bridge.delegation_plan._normalize_shared_types_package
  scripts.legacy_bridge.delegation_plan.build_output_row → scripts.legacy_bridge.delegation_plan._to_float
  scripts.legacy_bridge.delegation_plan.render_markdown → scripts.legacy_bridge.delegation_plan.build_output_row
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.load_config → scripts.legacy_bridge.detect_cqrs_pattern_clusters.deep_merge
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.normalize_config → scripts.legacy_bridge.detect_cqrs_pattern_clusters.deep_merge
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.shared_tokens_for_module → scripts.legacy_bridge.detect_cqrs_pattern_clusters.read_text
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository → scripts.legacy_bridge.detect_cqrs_pattern_clusters.normalize_config
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository → scripts.legacy_bridge.detect_cqrs_pattern_clusters.assign_clusters
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.main → scripts.legacy_bridge.detect_cqrs_pattern_clusters.parse_args
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.main → scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository
  scripts.legacy_bridge.sync_check.main → scripts.legacy_bridge.normalizer.normalize_json_schema
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Api (1)

**`Auto-generated API Smoke Tests`**
- `GET /events/stream` → `200`
- `GET /health` → `200`
- `GET /health/modules` → `200`
- assert `status < 400`

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/protos
# nodes: 210 | edges: 188 | modules: 31
# CC̄=1.8

HUBS[20]:
  scripts.legacy_bridge.run_arch_migration_discovery.run_discovery
    CC=12  in:1  out:77  total:78
  scratch.swop_scan_c2004.main
    CC=17  in:0  out:53  total:53
  scripts.legacy_bridge.run_arch_migration_discovery.build_delegation_decision_report
    CC=19  in:1  out:43  total:44
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository
    CC=20  in:2  out:37  total:39
  scripts.legacy_bridge.analyze_service_boundaries._calculate_module_stats
    CC=26  in:1  out:35  total:36
  scripts.legacy_bridge.candidate_selection.get_candidate_exclusion_reasons
    CC=14  in:2  out:33  total:35
  scripts.legacy_bridge.delegation_plan.render_markdown
    CC=8  in:1  out:33  total:34
  scripts.detect_migration_candidates.discover_candidate_paths
    CC=20  in:1  out:33  total:34
  scripts.legacy_bridge.run_arch_migration_discovery.profile_repository
    CC=18  in:1  out:33  total:34
  scripts.legacy_bridge.generate_migration_wave_plan.main
    CC=8  in:0  out:33  total:33
  scripts.legacy_bridge.generate_migration_wave_plan.build_waves
    CC=15  in:2  out:31  total:33
  scripts.legacy_bridge.analyze_service_boundaries.build_ts_index
    CC=10  in:1  out:30  total:31
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.main
    CC=10  in:0  out:31  total:31
  scripts.legacy_bridge.generate_delegation_plan.main
    CC=6  in:0  out:29  total:29
  scripts.legacy_bridge.run_arch_migration_discovery.main
    CC=8  in:0  out:29  total:29
  scripts.legacy_bridge.analyze_service_boundaries.build_service_blueprint_markdown
    CC=11  in:2  out:26  total:28
  protogate.cli._batch_generate
    CC=9  in:2  out:24  total:26
  scripts.legacy_bridge.swop_integration.run_swop_pipeline
    CC=13  in:0  out:25  total:25
  scripts.legacy_bridge.delegation_plan.build_output_row
    CC=6  in:3  out:22  total:25
  scripts.generate_incremental.main
    CC=11  in:0  out:24  total:24

MODULES:
  adapters.legacy_to_proto.user_adapter  [2 funcs]
    legacy_to_proto  CC=1  out:11
    wrap_for_event_store  CC=1  out:1
  gateway.delegation  [3 funcs]
    get_delegated_slice  CC=1  out:1
    get_delegation_health  CC=6  out:4
    list_delegated_slices  CC=2  out:3
  gateway.main  [14 funcs]
    cmd_change_email  CC=1  out:4
    cmd_create_user  CC=1  out:5
    cmd_deactivate_user  CC=1  out:4
    cmd_dual_create_user  CC=1  out:5
    cmd_index_search_entry  CC=1  out:3
    delegation_slice_detail  CC=2  out:4
    delegation_slices  CC=1  out:2
    health  CC=1  out:2
    health_module  CC=2  out:4
    health_modules  CC=1  out:2
  gateway.search_handler  [2 funcs]
    handle_index_entry  CC=1  out:2
    handle_search  CC=1  out:2
  gateway.sse  [4 funcs]
    event_generator  CC=6  out:11
    push_to_subscribers  CC=4  out:5
    subscribe  CC=1  out:3
    unsubscribe  CC=2  out:3
  gateway.user_handler  [6 funcs]
    handle_change_email  CC=1  out:2
    handle_create_user  CC=1  out:4
    handle_deactivate_user  CC=1  out:2
    handle_dual_write_user  CC=1  out:4
    handle_get_user  CC=2  out:2
    handle_list_events  CC=3  out:3
  protogate.cli  [11 funcs]
    _batch_generate  CC=9  out:24
    cmd_ci  CC=1  out:1
    cmd_clean  CC=1  out:1
    cmd_discovery  CC=7  out:10
    cmd_gateway  CC=2  out:1
    cmd_generate  CC=8  out:2
    cmd_generate_pydantic  CC=1  out:1
    cmd_generate_zod  CC=1  out:1
    cmd_legacy  CC=7  out:2
    cmd_registry  CC=6  out:3
  scratch.swop_scan_c2004  [6 funcs]
    _base_names  CC=7  out:9
    _kind_by_base  CC=3  out:0
    _kind_by_suffix  CC=4  out:1
    collect_ground_truth  CC=9  out:12
    main  CC=17  out:53
    run_swop_scan  CC=1  out:2
  scripts.conflict_resolver  [2 funcs]
    _check_field_conflicts  CC=8  out:5
    _field_effects  CC=2  out:3
  scripts.detect_migration_candidates  [19 funcs]
    _analyze_file_content  CC=18  out:15
    _check_candidate_flags  CC=6  out:11
    analyze_candidate  CC=12  out:12
    analyze_repository  CC=4  out:13
    build_output_row  CC=2  out:2
    classify_extraction_target  CC=19  out:12
    count_api_routes  CC=3  out:5
    count_outbound_api_calls  CC=2  out:3
    discover_candidate_paths  CC=20  out:33
    extract_python_imports  CC=6  out:8
  scripts.event_store  [1 funcs]
    __init__  CC=1  out:1
  scripts.generate_incremental  [8 funcs]
    _stem  CC=1  out:2
    _write  CC=2  out:7
    file_hash  CC=2  out:6
    load_cache  CC=2  out:3
    main  CC=11  out:24
    regenerate  CC=1  out:11
    save_cache  CC=1  out:3
    should_regenerate  CC=1  out:2
  scripts.generate_json_schema  [2 funcs]
    generate  CC=6  out:3
    main  CC=3  out:10
  scripts.generate_pydantic  [4 funcs]
    _flatten_enums  CC=1  out:8
    _flatten_messages  CC=1  out:5
    generate  CC=10  out:16
    main  CC=3  out:9
  scripts.generate_sql  [3 funcs]
    _table_name  CC=1  out:2
    generate_sql  CC=6  out:6
    main  CC=3  out:9
  scripts.generate_zod  [4 funcs]
    _flatten_enums  CC=1  out:8
    _flatten_messages  CC=1  out:5
    main  CC=3  out:9
    to_zod  CC=7  out:15
  scripts.legacy_bridge.analyze_service_boundaries  [46 funcs]
    _append_execution_plan_section  CC=4  out:6
    _append_frontend_modules_section  CC=4  out:6
    _append_merge_hints_section  CC=3  out:3
    _append_recommended_candidates_section  CC=4  out:5
    _append_service_components_section  CC=4  out:6
    _apply_merge_hints  CC=8  out:7
    _build_component_row  CC=18  out:21
    _build_cqrs_endpoint_templates  CC=6  out:9
    _build_eligible_modules  CC=4  out:0
    _build_module_index  CC=5  out:4
  scripts.legacy_bridge.candidate_selection  [3 funcs]
    get_candidate_exclusion_reasons  CC=14  out:33
    is_delegable_candidate  CC=1  out:1
    parse_score  CC=2  out:2
  scripts.legacy_bridge.delegation_plan  [7 funcs]
    _normalize_shared_types_package  CC=5  out:3
    _to_float  CC=2  out:1
    build_output_row  CC=6  out:22
    build_slice_blueprint  CC=1  out:2
    build_steps  CC=1  out:1
    render_markdown  CC=8  out:33
    to_slice_name  CC=1  out:4
  scripts.legacy_bridge.detect_cqrs_pattern_clusters  [9 funcs]
    analyze_repository  CC=20  out:37
    assign_clusters  CC=9  out:14
    deep_merge  CC=4  out:6
    load_config  CC=3  out:5
    main  CC=10  out:31
    normalize_config  CC=2  out:1
    parse_args  CC=1  out:8
    read_text  CC=3  out:2
    shared_tokens_for_module  CC=4  out:5
  scripts.legacy_bridge.diff_engine  [1 funcs]
    diff_fields  CC=12  out:19
  scripts.legacy_bridge.generate_delegation_plan  [4 funcs]
    dedupe_candidates  CC=6  out:8
    load_clusters  CC=9  out:10
    main  CC=6  out:29
    parse_args  CC=1  out:9
  scripts.legacy_bridge.generate_migration_wave_plan  [5 funcs]
    build_waves  CC=15  out:31
    load_json  CC=3  out:3
    main  CC=8  out:33
    parse_args  CC=1  out:8
    resolve_path  CC=2  out:2
  scripts.legacy_bridge.migrator  [2 funcs]
    main  CC=1  out:7
    migrate_users  CC=3  out:6
  scripts.legacy_bridge.normalizer  [2 funcs]
    normalize_json_schema  CC=3  out:10
    normalize_proto_ast  CC=2  out:5
  scripts.legacy_bridge.report_rendering  [9 funcs]
    _append_artifacts_table  CC=2  out:4
    _append_detail_section  CC=5  out:12
    _append_reason_counts_section  CC=4  out:3
    _append_simple_list_section  CC=3  out:3
    _format_detail_value  CC=5  out:3
    render_delegation_decisions_markdown  CC=1  out:5
    render_excluded_candidates_markdown  CC=2  out:5
    render_service_boundary_decisions_markdown  CC=1  out:5
    render_summary_markdown  CC=6  out:20
  scripts.legacy_bridge.run_arch_migration_discovery  [11 funcs]
    _parse_score  CC=1  out:1
    build_delegation_decision_report  CC=19  out:43
    build_delegation_plan  CC=5  out:7
    build_excluded_candidates_report  CC=5  out:18
    main  CC=8  out:29
    parse_args  CC=1  out:11
    profile_repository  CC=18  out:33
    resolve_output_dir  CC=2  out:2
    run_discovery  CC=12  out:77
    write_json  CC=1  out:2
  scripts.legacy_bridge.swop_integration  [7 funcs]
    _context_score  CC=18  out:19
    _eligible_groups  CC=6  out:5
    _group_match_score  CC=11  out:13
    _name_tokens  CC=10  out:8
    _normalize_token  CC=7  out:7
    infer_contexts_from_service_boundaries  CC=15  out:21
    run_swop_pipeline  CC=13  out:25
  scripts.legacy_bridge.sync_check  [1 funcs]
    main  CC=6  out:12
  scripts.parse_proto  [6 funcs]
    _handle_block_end  CC=6  out:5
    _handle_enum_start  CC=3  out:5
    _handle_message_start  CC=3  out:5
    _parse_top_level_declarations  CC=3  out:5
    _to_dict  CC=5  out:5
    parse_proto  CC=15  out:14
  scripts.schema_registry  [6 funcs]
    __init__  CC=1  out:1
    register  CC=10  out:18
    _connect  CC=1  out:5
    _diff_messages  CC=19  out:16
    _sha256_file  CC=2  out:6
    check_compatibility  CC=6  out:2

EDGES:
  gateway.sse.push_to_subscribers → gateway.sse.unsubscribe
  gateway.sse.event_generator → gateway.sse.unsubscribe
  gateway.delegation.get_delegation_health → gateway.delegation.list_delegated_slices
  scripts.parse_proto._handle_block_end → scripts.parse_proto._to_dict
  scripts.parse_proto.parse_proto → scripts.parse_proto._handle_message_start
  scripts.parse_proto.parse_proto → scripts.parse_proto._handle_enum_start
  scripts.parse_proto.parse_proto → scripts.parse_proto._handle_block_end
  scripts.parse_proto.parse_proto → scripts.parse_proto._to_dict
  scripts.parse_proto.parse_proto → scripts.parse_proto._parse_top_level_declarations
  scripts.generate_incremental.should_regenerate → scripts.generate_incremental.file_hash
  scripts.generate_incremental.regenerate → scripts.generate_incremental._stem
  scripts.generate_incremental.regenerate → scripts.parse_proto.parse_proto
  scripts.generate_incremental.regenerate → scripts.generate_incremental._write
  scripts.generate_incremental.regenerate → scripts.generate_zod.to_zod
  scripts.generate_incremental.main → scripts.generate_incremental.load_cache
  scripts.generate_incremental.main → scripts.generate_incremental.should_regenerate
  scripts.generate_incremental.main → scripts.generate_incremental.save_cache
  scripts.generate_sql.generate_sql → scripts.generate_sql._table_name
  scripts.generate_sql.main → scripts.parse_proto.parse_proto
  scripts.generate_sql.main → scripts.generate_sql.generate_sql
  scripts.schema_registry.check_compatibility → scripts.schema_registry._diff_messages
  scripts.schema_registry.SchemaRegistry.__init__ → scripts.schema_registry._connect
  scripts.schema_registry.SchemaRegistry.register → scripts.parse_proto.parse_proto
  scripts.schema_registry.SchemaRegistry.register → scripts.schema_registry._sha256_file
  scripts.generate_json_schema.main → scripts.parse_proto.parse_proto
  scripts.generate_json_schema.main → scripts.generate_json_schema.generate
  scripts.generate_pydantic.generate → scripts.generate_pydantic._flatten_enums
  scripts.generate_pydantic.generate → scripts.generate_pydantic._flatten_messages
  scripts.generate_pydantic.main → scripts.parse_proto.parse_proto
  scripts.generate_pydantic.main → scripts.generate_pydantic.generate
  scripts.conflict_resolver.ConflictResolver._check_field_conflicts → scripts.conflict_resolver._field_effects
  scripts.event_store.EventStore.__init__ → scripts.schema_registry._connect
  scripts.generate_zod.to_zod → scripts.generate_zod._flatten_enums
  scripts.generate_zod.to_zod → scripts.generate_zod._flatten_messages
  scripts.generate_zod.main → scripts.parse_proto.parse_proto
  scripts.generate_zod.main → scripts.generate_zod.to_zod
  scripts.legacy_bridge.delegation_plan.build_steps → scripts.legacy_bridge.delegation_plan.to_slice_name
  scripts.legacy_bridge.delegation_plan.build_slice_blueprint → scripts.legacy_bridge.delegation_plan.to_slice_name
  scripts.legacy_bridge.delegation_plan.build_slice_blueprint → scripts.legacy_bridge.delegation_plan.build_steps
  scripts.legacy_bridge.delegation_plan.build_output_row → scripts.legacy_bridge.delegation_plan._normalize_shared_types_package
  scripts.legacy_bridge.delegation_plan.build_output_row → scripts.legacy_bridge.delegation_plan._to_float
  scripts.legacy_bridge.delegation_plan.render_markdown → scripts.legacy_bridge.delegation_plan.build_output_row
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.load_config → scripts.legacy_bridge.detect_cqrs_pattern_clusters.deep_merge
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.normalize_config → scripts.legacy_bridge.detect_cqrs_pattern_clusters.deep_merge
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.shared_tokens_for_module → scripts.legacy_bridge.detect_cqrs_pattern_clusters.read_text
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository → scripts.legacy_bridge.detect_cqrs_pattern_clusters.normalize_config
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository → scripts.legacy_bridge.detect_cqrs_pattern_clusters.assign_clusters
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.main → scripts.legacy_bridge.detect_cqrs_pattern_clusters.parse_args
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.main → scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository
  scripts.legacy_bridge.sync_check.main → scripts.legacy_bridge.normalizer.normalize_json_schema
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 112f 39122L | python:54,md:14,yaml:11,typescript:9,json:8,proto:5,txt:4,generator:1,ini:1,shell:1,yml:1,toml:1 | 2026-04-24
# CC̄=1.8 | critical:18/843 | dups:0 | cycles:0

HEALTH[18]:
  🟡 CC    parse_proto CC=15 (limit:15)
  🟡 CC    _diff_messages CC=19 (limit:15)
  🟡 CC    analyze_repository CC=20 (limit:15)
  🟡 CC    build_waves CC=15 (limit:15)
  🟡 CC    main CC=17 (limit:15)
  🟡 CC    infer_contexts_from_service_boundaries CC=15 (limit:15)
  🟡 CC    _context_score CC=18 (limit:15)
  🟡 CC    profile_repository CC=18 (limit:15)
  🟡 CC    build_service_boundary_decision_report CC=21 (limit:15)
  🟡 CC    build_delegation_decision_report CC=19 (limit:15)
  🟡 CC    build_summary CC=18 (limit:15)
  🟡 CC    discover_candidate_paths CC=20 (limit:15)
  🟡 CC    _analyze_file_content CC=18 (limit:15)
  🟡 CC    score_migration_candidate CC=15 (limit:15)
  🟡 CC    classify_extraction_target CC=19 (limit:15)
  🟡 CC    _build_component_row CC=18 (limit:15)
  🟡 CC    select_execution_plan CC=20 (limit:15)
  🟡 CC    _calculate_module_stats CC=26 (limit:15)

REFACTOR[1]:
  1. split 18 high-CC methods  (CC>15)

PIPELINES[147]:
  [1] Src [CreateUserCommandSchema]: CreateUserCommandSchema
      PURITY: 100% pure
  [2] Src [GetUserQuerySchema]: GetUserQuerySchema
      PURITY: 100% pure
  [3] Src [UserSchema]: UserSchema
      PURITY: 100% pure
  [4] Src [CreateUserCommandSchema]: CreateUserCommandSchema
      PURITY: 100% pure
  [5] Src [GetUserQuerySchema]: GetUserQuerySchema
      PURITY: 100% pure

LAYERS:
  scratch/                        CC̄=6.9    ←in:0  →out:0
  │ !! swop_scan_c2004            237L  0C    6m  CC=17     ←0
  │ swop_pipeline_service_id    89L  0C    1m  CC=7      ←0
  │ smoke_test_search           30L  0C    0m  CC=0.0    ←0
  │ smoke_test_dual_write       27L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=5.0    ←in:1  →out:9  !! split
  │ !! analyze_service_boundaries  1344L  2C   56m  CC=26     ←1
  │ !! run_arch_migration_discovery   699L  0C   17m  CC=21     ←0
  │ !! detect_migration_candidates   546L  2C   21m  CC=20     ←0
  │ !! schema_registry            543L  3C   16m  CC=19     ←1
  │ !! detect_cqrs_pattern_clusters   476L  1C   15m  CC=20     ←1
  │ event_store                398L  4C   13m  CC=7      ←0
  │ !! swop_integration           372L  0C   12m  CC=18     ←0
  │ !! generate_migration_wave_plan   338L  2C    8m  CC=15     ←1
  │ !! parse_proto                319L  4C    9m  CC=15     ←8
  │ conflict_resolver          246L  2C    7m  CC=11     ←0
  │ legacy_registry            245L  2C    8m  CC=11     ←0
  │ report_rendering           207L  0C    9m  CC=6      ←0
  │ delegation_plan            150L  0C    8m  CC=8      ←2
  │ generate_incremental       148L  0C    8m  CC=11     ←0
  │ generate_pydantic          146L  0C    5m  CC=10     ←0
  │ generate_zod               129L  0C    5m  CC=7      ←1
  │ generate_delegation_plan   116L  0C    5m  CC=9      ←0
  │ dual_writer                114L  2C    6m  CC=5      ←0
  │ vector_clock               112L  1C    9m  CC=4      ←0
  │ diff_engine                109L  3C    1m  CC=12     ←2
  │ generate_json_schema        99L  0C    2m  CC=6      ←0
  │ normalizer                  98L  1C    2m  CC=3      ←2
  │ generate_sql                97L  0C    3m  CC=6      ←1
  │ migrator                    69L  0C    2m  CC=3      ←0
  │ search_index                61L  1C    4m  CC=5      ←0
  │ candidate_selection         57L  0C    3m  CC=14     ←2
  │ report_generator            56L  0C    1m  CC=6      ←1
  │ migration_advisor           54L  0C    2m  CC=9      ←1
  │ idempotency_store           41L  1C    5m  CC=2      ←0
  │ sync_check                  39L  0C    1m  CC=6      ←0
  │
  protogate/                      CC̄=3.8    ←in:0  →out:1
  │ cli                        291L  0C   13m  CC=9      ←0
  │ __init__                     8L  0C    0m  CC=0.0    ←0
  │
  gateway/                        CC̄=1.9    ←in:0  →out:0
  │ main                       332L  4C   16m  CC=3      ←0
  │ user_handler               150L  0C    6m  CC=3      ←1
  │ delegation                 147L  1C    7m  CC=6      ←1
  │ sse                        105L  0C    4m  CC=6      ←1
  │ ws                          76L  1C    4m  CC=5      ←0
  │ search_handler              46L  0C    2m  CC=1      ←1
  │ requirements.txt             3L  0C    0m  CC=0.0    ←0
  │ __init__                     0L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   0L  0C    0m  CC=0.0    ←0
  │
  generated/                      CC̄=1.0    ←in:0  →out:0
  │ search_v1.ts                39L  0C    5m  CC=1      ←0
  │ search_v1_search.ts         39L  0C    5m  CC=1      ←0
  │ search_v1_models            35L  5C    0m  CC=0.0    ←0
  │ search_v1_search_models     35L  5C    0m  CC=0.0    ←0
  │ identification_v1.ts        32L  0C    3m  CC=1      ←0
  │ examples_identification_v1_identification.ts    32L  0C    3m  CC=1      ←0
  │ identification_v1_models    31L  4C    0m  CC=0.0    ←0
  │ examples_identification_v1_identification_models    31L  4C    0m  CC=0.0    ←0
  │ user_v2.ts                  21L  0C    3m  CC=1      ←0
  │ user_v2_user.ts             21L  0C    3m  CC=1      ←0
  │ user_v2_models              21L  3C    0m  CC=0.0    ←0
  │ user_v2_user_models         21L  3C    0m  CC=0.0    ←0
  │ user_v1.ts                  18L  0C    3m  CC=1      ←0
  │ user_v1_user.ts             18L  0C    3m  CC=1      ←0
  │ user_v1_user_models         18L  3C    0m  CC=0.0    ←0
  │ user_v1_models              16L  3C    0m  CC=0.0    ←0
  │ legacy_bridge_user_legacy.v1_models    16L  1C    0m  CC=0.0    ←0
  │ legacy_bridge_user_legacy.v1.ts    12L  0C    1m  CC=1      ←0
  │
  adapters/                       CC̄=1.0    ←in:0  →out:0
  │ user_adapter                36L  0C    2m  CC=1      ←0
  │ user_adapter                21L  0C    1m  CC=1      ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ !! migration-orchestrator-strategy.md   626L  0C    0m  CC=0.0    ←0
  │ !! delegation-plan.generated.json   526L  0C    0m  CC=0.0    ←0
  │ refactor-delegation-architecture.md   116L  0C    0m  CC=0.0    ←0
  │ protogate-integration.md    71L  0C    1m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! SUMD.md                   1236L  0C  244m  CC=0.0    ←1
  │ !! SUMR.md                   1215L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ README.md                  369L  0C    0m  CC=0.0    ←0
  │ tree.txt                   148L  0C    0m  CC=0.0    ←0
  │ CHANGELOG.md               120L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              95L  0C    0m  CC=0.0    ←0
  │ TODO.md                     94L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          69L  0C    0m  CC=0.0    ←0
  │ project.sh                  48L  0C    0m  CC=0.0    ←0
  │ buf.gen.yaml                25L  0C    0m  CC=0.0    ←0
  │ buf.yaml                    10L  0C    0m  CC=0.0    ←0
  │ requirements.txt             8L  0C    0m  CC=0.0    ←0
  │ pytest.ini                   5L  0C    0m  CC=0.0    ←0
  │ Dockerfile.generator         0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                2648L  0C    0m  CC=0.0    ←0
  │ !! map.toon.yaml              573L  0C  244m  CC=0.0    ←0
  │ !! context.md                 573L  0C    0m  CC=0.0    ←0
  │ README.md                  339L  0C    0m  CC=0.0    ←0
  │ calls.toon.yaml            277L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         182L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml      156L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           51L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         43L  0C    0m  CC=0.0    ←0
  │
  reports/                        CC̄=0.0    ←in:0  →out:0
  │ !! service-boundaries.json  16058L  0C    0m  CC=0.0    ←0
  │ !! cqrs-pattern-clusters.json   888L  0C    0m  CC=0.0    ←0
  │ !! module-candidates.json     676L  0C    0m  CC=0.0    ←0
  │ !! delegation-plan.generated.json   526L  0C    0m  CC=0.0    ←0
  │ migration-discovery.summary.json   474L  0C    0m  CC=0.0    ←0
  │ delegation-decisions.md    167L  0C    0m  CC=0.0    ←0
  │ repository-profile.json    144L  0C    0m  CC=0.0    ←0
  │ excluded-candidates.md     137L  0C    0m  CC=0.0    ←0
  │ service-boundary-decisions.md   126L  0C    0m  CC=0.0    ←0
  │ migration-wave-plan.md      86L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-api-smoke.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │
  contracts/                      CC̄=0.0    ←in:0  →out:0
  │ search.proto                40L  0C    0m  CC=0.0    ←0
  │ identification.proto        36L  0C    0m  CC=0.0    ←0
  │ user.proto                  27L  0C    0m  CC=0.0    ←0
  │ user.proto                  20L  0C    0m  CC=0.0    ←0
  │ user_legacy.schema.json     18L  0C    0m  CC=0.0    ←0
  │ user_legacy.v1.proto        14L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     Dockerfile.generator                      0L
     Makefile                                  0L
     gateway/Dockerfile                        0L
     gateway/__init__.py                       0L

COUPLING:
                         scripts.legacy_bridge                scripts                   SUMD              protogate
  scripts.legacy_bridge                     ──                     ←9                      6                         hub
                scripts                      9                     ──                                            ←1  !! fan-out
                   SUMD                     ←6                                            ──                         hub
              protogate                                             1                                            ──
  CYCLES: none
  HUB: scripts.legacy_bridge/ (fan-in=9)
  HUB: SUMD/ (fan-in=6)
  SMELL: scripts/ fan-out=9 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 18 groups | 45f 8966L | 2026-04-24

SUMMARY:
  files_scanned: 45
  total_lines:   8966
  dup_groups:    18
  dup_fragments: 39
  saved_lines:   147
  scan_ms:       6370

HOTSPOTS[7] (files with most duplication):
  scripts/legacy_bridge/report_rendering.py  dup=46L  groups=1  frags=2  (0.5%)
  scripts/generate_pydantic.py  dup=42L  groups=5  frags=5  (0.5%)
  scripts/generate_zod.py  dup=42L  groups=5  frags=5  (0.5%)
  scripts/legacy_bridge/analyze_service_boundaries.py  dup=30L  groups=5  frags=5  (0.3%)
  scripts/legacy_bridge/detect_cqrs_pattern_clusters.py  dup=25L  groups=4  frags=4  (0.3%)
  scripts/legacy_bridge/run_arch_migration_discovery.py  dup=13L  groups=3  frags=3  (0.1%)
  scripts/generate_sql.py  dup=12L  groups=1  frags=1  (0.1%)

DUPLICATES[18] (ranked by impact):
  [1a1a5665e06d1f8a]   STRU  main  L=12 N=3 saved=24 sim=1.00
      scripts/generate_pydantic.py:131-142  (main)
      scripts/generate_sql.py:82-93  (main)
      scripts/generate_zod.py:114-125  (main)
  [00c0e6e28fc8aac6]   STRU  render_delegation_decisions_markdown  L=23 N=2 saved=23 sim=1.00
      scripts/legacy_bridge/report_rendering.py:160-182  (render_delegation_decisions_markdown)
      scripts/legacy_bridge/report_rendering.py:185-207  (render_service_boundary_decisions_markdown)
  [61fb05c14ef39274]   EXAC  _flatten_messages  L=11 N=2 saved=11 sim=1.00
      scripts/generate_pydantic.py:35-45  (_flatten_messages)
      scripts/generate_zod.py:36-46  (_flatten_messages)
  [2a4922ec3dfa1bef]   EXAC  _flatten_enums  L=11 N=2 saved=11 sim=1.00
      scripts/generate_pydantic.py:48-58  (_flatten_enums)
      scripts/generate_zod.py:49-59  (_flatten_enums)
  [e140be6cf51d2681]   EXAC  read_text  L=5 N=3 saved=10 sim=1.00
      scripts/detect_migration_candidates.py:189-193  (read_text)
      scripts/legacy_bridge/analyze_service_boundaries.py:170-174  (read_text)
      scripts/legacy_bridge/run_arch_migration_discovery.py:145-149  (read_text)
  [42491376f509549f]   EXAC  deep_merge  L=8 N=2 saved=8 sim=1.00
      scripts/legacy_bridge/analyze_service_boundaries.py:82-89  (deep_merge)
      scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:163-170  (deep_merge)
  [2b4dc3f0af97a67d]   STRU  __init__  L=4 N=3 saved=8 sim=1.00
      scripts/dual_writer.py:24-27  (__init__)
      scripts/idempotency_store.py:11-14  (__init__)
      scripts/search_index.py:12-15  (__init__)
  [9600d037241ef7f6]   STRU  _connect  L=8 N=2 saved=8 sim=1.00
      scripts/event_store.py:58-65  (_connect)
      scripts/schema_registry.py:114-121  (_connect)
  [2bf86c6a91094d26]   EXAC  load_config  L=7 N=2 saved=7 sim=1.00
      scripts/legacy_bridge/analyze_service_boundaries.py:92-98  (load_config)
      scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:173-179  (load_config)
  [56a0a4b947778620]   EXAC  find  L=5 N=2 saved=5 sim=1.00
      scripts/legacy_bridge/analyze_service_boundaries.py:435-439  (find)
      scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:275-279  (find)
  [1c853fca582fc078]   EXAC  union  L=5 N=2 saved=5 sim=1.00
      scripts/legacy_bridge/analyze_service_boundaries.py:441-445  (union)
      scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:281-285  (union)
  [f323e07cca628456]   STRU  health_module  L=5 N=2 saved=5 sim=1.00
      gateway/main.py:133-137  (health_module)
      gateway/main.py:146-150  (delegation_slice_detail)
  [5438849e5bfbe6fc]   STRU  relative_artifact_path  L=5 N=2 saved=5 sim=1.00
      scripts/legacy_bridge/run_arch_migration_discovery.py:495-499  (relative_artifact_path)
      scripts/legacy_bridge/swop_integration.py:181-185  (_relative_path)
  [ddebd58cc0058ba6]   EXAC  walk  L=4 N=2 saved=4 sim=1.00
      scripts/generate_pydantic.py:39-42  (walk)
      scripts/generate_zod.py:40-43  (walk)
  [1d1b3f6d77e9ac98]   EXAC  walk  L=4 N=2 saved=4 sim=1.00
      scripts/generate_pydantic.py:52-55  (walk)
      scripts/generate_zod.py:53-56  (walk)
  [557430fa9861578c]   STRU  cmd_ci  L=3 N=2 saved=3 sim=1.00
      protogate/cli.py:91-93  (cmd_ci)
      protogate/cli.py:124-126  (cmd_clean)
  [9f2a33ec1209fe93]   STRU  cmd_generate_pydantic  L=3 N=2 saved=3 sim=1.00
      protogate/cli.py:197-199  (cmd_generate_pydantic)
      protogate/cli.py:202-204  (cmd_generate_zod)
  [cae7903dcb44e30d]   STRU  resolve_path  L=3 N=2 saved=3 sim=1.00
      scripts/legacy_bridge/generate_migration_wave_plan.py:95-97  (resolve_path)
      scripts/legacy_bridge/run_arch_migration_discovery.py:152-154  (resolve_output_dir)

REFACTOR[18] (ranked by priority):
  [1] ○ extract_function   → scripts/utils/main.py
      WHY: 3 occurrences of 12-line block across 3 files — saves 24 lines
      FILES: scripts/generate_pydantic.py, scripts/generate_sql.py, scripts/generate_zod.py
  [2] ○ extract_function   → scripts/legacy_bridge/utils/render_delegation_decisions_markdown.py
      WHY: 2 occurrences of 23-line block across 1 files — saves 23 lines
      FILES: scripts/legacy_bridge/report_rendering.py
  [3] ○ extract_function   → scripts/utils/_flatten_messages.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: scripts/generate_pydantic.py, scripts/generate_zod.py
  [4] ○ extract_function   → scripts/utils/_flatten_enums.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: scripts/generate_pydantic.py, scripts/generate_zod.py
  [5] ○ extract_function   → scripts/utils/read_text.py
      WHY: 3 occurrences of 5-line block across 3 files — saves 10 lines
      FILES: scripts/detect_migration_candidates.py, scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/run_arch_migration_discovery.py
  [6] ○ extract_function   → scripts/legacy_bridge/utils/deep_merge.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/detect_cqrs_pattern_clusters.py
  [7] ○ extract_function   → scripts/utils/__init__.py
      WHY: 3 occurrences of 4-line block across 3 files — saves 8 lines
      FILES: scripts/dual_writer.py, scripts/idempotency_store.py, scripts/search_index.py
  [8] ○ extract_function   → scripts/utils/_connect.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: scripts/event_store.py, scripts/schema_registry.py
  [9] ○ extract_function   → scripts/legacy_bridge/utils/load_config.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/detect_cqrs_pattern_clusters.py
  [10] ○ extract_function   → scripts/legacy_bridge/utils/find.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/detect_cqrs_pattern_clusters.py
  [11] ○ extract_function   → scripts/legacy_bridge/utils/union.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/detect_cqrs_pattern_clusters.py
  [12] ○ extract_function   → gateway/utils/health_module.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: gateway/main.py
  [13] ○ extract_function   → scripts/legacy_bridge/utils/relative_artifact_path.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: scripts/legacy_bridge/run_arch_migration_discovery.py, scripts/legacy_bridge/swop_integration.py
  [14] ○ extract_function   → scripts/utils/walk.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: scripts/generate_pydantic.py, scripts/generate_zod.py
  [15] ○ extract_function   → scripts/utils/walk.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: scripts/generate_pydantic.py, scripts/generate_zod.py
  [16] ○ extract_function   → protogate/utils/cmd_ci.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: protogate/cli.py
  [17] ○ extract_function   → protogate/utils/cmd_generate_pydantic.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: protogate/cli.py
  [18] ○ extract_function   → scripts/legacy_bridge/utils/resolve_path.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: scripts/legacy_bridge/generate_migration_wave_plan.py, scripts/legacy_bridge/run_arch_migration_discovery.py

QUICK_WINS[9] (low risk, high savings — do first):
  [1] extract_function   saved=24L  → scripts/utils/main.py
      FILES: generate_pydantic.py, generate_sql.py, generate_zod.py
  [2] extract_function   saved=23L  → scripts/legacy_bridge/utils/render_delegation_decisions_markdown.py
      FILES: report_rendering.py
  [3] extract_function   saved=11L  → scripts/utils/_flatten_messages.py
      FILES: generate_pydantic.py, generate_zod.py
  [4] extract_function   saved=11L  → scripts/utils/_flatten_enums.py
      FILES: generate_pydantic.py, generate_zod.py
  [5] extract_function   saved=10L  → scripts/utils/read_text.py
      FILES: detect_migration_candidates.py, analyze_service_boundaries.py, run_arch_migration_discovery.py
  [6] extract_function   saved=8L  → scripts/legacy_bridge/utils/deep_merge.py
      FILES: analyze_service_boundaries.py, detect_cqrs_pattern_clusters.py
  [7] extract_function   saved=8L  → scripts/utils/__init__.py
      FILES: dual_writer.py, idempotency_store.py, search_index.py
  [8] extract_function   saved=8L  → scripts/utils/_connect.py
      FILES: event_store.py, schema_registry.py
  [9] extract_function   saved=7L  → scripts/legacy_bridge/utils/load_config.py
      FILES: analyze_service_boundaries.py, detect_cqrs_pattern_clusters.py

EFFORT_ESTIMATE (total ≈ 4.9h):
  medium main                                saved=24L  ~48min
  medium render_delegation_decisions_markdown saved=23L  ~46min
  easy   _flatten_messages                   saved=11L  ~22min
  easy   _flatten_enums                      saved=11L  ~22min
  easy   read_text                           saved=10L  ~20min
  easy   deep_merge                          saved=8L  ~16min
  easy   __init__                            saved=8L  ~16min
  easy   _connect                            saved=8L  ~16min
  easy   load_config                         saved=7L  ~14min
  easy   find                                saved=5L  ~10min
  ... +8 more (~64min)

METRICS-TARGET:
  dup_groups:  18 → 0
  saved_lines: 147 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 580 func | 23f | 2026-04-24

NEXT[1] (ranked by impact):
  [1] !  SPLIT-FUNC      main  CC=17  fan=23
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 391


RISKS[0]: none

METRICS-TARGET:
  CC̄:          0.3 → ≤0.2
  max-CC:      17 → ≤8
  god-modules: 0 → 0
  high-CC(≥15): 1 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=0.4 → now CC̄=0.3
```

## Intent

Migration tool and delegation platform for extracting bounded slices from legacy systems
