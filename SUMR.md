# protos

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `protos`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: requirements.txt, Makefile, testql(1), app.doql.less, goal.yaml, .env.example, docker-compose.yml, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: protos;
  version: 0.1.0;
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
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
}
```

## Workflows

## Call Graph

*134 nodes · 112 edges · 26 modules · CC̄=1.7*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `analyze_frontend_modules` *(in scripts.legacy_bridge.analyze_service_boundaries)* | 43 ⚠ | 1 | 66 | **67** |
| `run_discovery` *(in scripts.legacy_bridge.run_arch_migration_discovery)* | 6 | 1 | 42 | **43** |
| `analyze_repository` *(in scripts.legacy_bridge.detect_cqrs_pattern_clusters)* | 19 ⚠ | 1 | 35 | **36** |
| `discover_candidate_paths` *(in scripts.detect_migration_candidates)* | 20 ⚠ | 1 | 33 | **34** |
| `profile_repository` *(in scripts.legacy_bridge.run_arch_migration_discovery)* | 18 ⚠ | 1 | 33 | **34** |
| `parse_proto` *(in scripts.parse_proto)* | 17 ⚠ | 8 | 26 | **34** |
| `build_waves` *(in scripts.legacy_bridge.generate_migration_wave_plan)* | 15 ⚠ | 3 | 31 | **34** |
| `build_service_components` *(in scripts.legacy_bridge.analyze_service_boundaries)* | 34 ⚠ | 1 | 32 | **33** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/protos
# nodes: 134 | edges: 112 | modules: 26
# CC̄=1.7

HUBS[20]:
  scripts.legacy_bridge.analyze_service_boundaries.analyze_frontend_modules
    CC=43  in:1  out:66  total:67
  scripts.legacy_bridge.run_arch_migration_discovery.run_discovery
    CC=6  in:1  out:42  total:43
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository
    CC=19  in:1  out:35  total:36
  scripts.detect_migration_candidates.discover_candidate_paths
    CC=20  in:1  out:33  total:34
  scripts.legacy_bridge.run_arch_migration_discovery.profile_repository
    CC=18  in:1  out:33  total:34
  scripts.parse_proto.parse_proto
    CC=17  in:8  out:26  total:34
  scripts.legacy_bridge.generate_migration_wave_plan.build_waves
    CC=15  in:3  out:31  total:34
  scripts.legacy_bridge.analyze_service_boundaries.build_service_components
    CC=34  in:1  out:32  total:33
  scripts.legacy_bridge.generate_migration_wave_plan.main
    CC=8  in:0  out:33  total:33
  scripts.detect_migration_candidates.analyze_candidate
    CC=28  in:1  out:32  total:33
  scripts.legacy_bridge.analyze_service_boundaries.build_ts_index
    CC=10  in:1  out:30  total:31
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.main
    CC=10  in:0  out:31  total:31
  scripts.legacy_bridge.delegation_plan.render_markdown
    CC=8  in:1  out:30  total:31
  scripts.legacy_bridge.generate_delegation_plan.main
    CC=4  in:0  out:27  total:27
  scripts.generate_incremental.main
    CC=11  in:0  out:24  total:24
  scripts.legacy_bridge.run_arch_migration_discovery.main
    CC=6  in:0  out:24  total:24
  scripts.legacy_bridge.analyze_service_boundaries.main
    CC=7  in:0  out:24  total:24
  scripts.legacy_bridge.diff_engine.diff_fields
    CC=12  in:3  out:19  total:22
  scripts.legacy_bridge.analyze_service_boundaries.build_backend_index
    CC=7  in:1  out:19  total:20
  scripts.schema_registry.SchemaRegistry.register
    CC=10  in:0  out:18  total:18

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
  scripts.conflict_resolver  [2 funcs]
    resolve_merge  CC=22  out:15
    _field_effects  CC=2  out:3
  scripts.detect_migration_candidates  [13 funcs]
    analyze_candidate  CC=28  out:32
    analyze_repository  CC=4  out:13
    build_output_row  CC=2  out:2
    classify_extraction_target  CC=19  out:12
    discover_candidate_paths  CC=20  out:33
    get_service_candidates  CC=4  out:7
    has_candidate_markers  CC=6  out:6
    import_tokens  CC=3  out:2
    iter_files  CC=8  out:1
    main  CC=5  out:17
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
  scripts.generate_pydantic  [2 funcs]
    generate  CC=5  out:6
    main  CC=3  out:9
  scripts.generate_sql  [3 funcs]
    _table_name  CC=1  out:2
    generate_sql  CC=6  out:6
    main  CC=3  out:9
  scripts.generate_zod  [2 funcs]
    main  CC=3  out:9
    to_zod  CC=4  out:7
  scripts.legacy_bridge.analyze_service_boundaries  [28 funcs]
    analyze  CC=2  out:10
    analyze_frontend_modules  CC=43  out:66
    backend_group_summary  CC=9  out:11
    build_backend_index  CC=7  out:19
    build_cleanup_checklist  CC=2  out:1
    build_service_components  CC=34  out:32
    build_target_structure  CC=2  out:1
    build_ts_index  CC=10  out:30
    choose_component_anchor  CC=1  out:2
    const_str  CC=3  out:2
  scripts.legacy_bridge.delegation_plan  [5 funcs]
    build_output_row  CC=3  out:15
    build_slice_blueprint  CC=1  out:2
    build_steps  CC=1  out:1
    render_markdown  CC=8  out:30
    to_slice_name  CC=1  out:4
  scripts.legacy_bridge.detect_cqrs_pattern_clusters  [7 funcs]
    analyze_repository  CC=19  out:35
    assign_clusters  CC=9  out:14
    deep_merge  CC=4  out:6
    load_config  CC=3  out:5
    main  CC=10  out:31
    normalize_config  CC=2  out:1
    parse_args  CC=1  out:8
  scripts.legacy_bridge.diff_engine  [1 funcs]
    diff_fields  CC=12  out:19
  scripts.legacy_bridge.generate_delegation_plan  [4 funcs]
    load_candidates  CC=4  out:5
    load_clusters  CC=7  out:7
    main  CC=4  out:27
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
  scripts.legacy_bridge.run_arch_migration_discovery  [8 funcs]
    build_delegation_plan  CC=2  out:5
    main  CC=6  out:24
    parse_args  CC=1  out:8
    profile_repository  CC=18  out:33
    resolve_output_dir  CC=2  out:2
    run_discovery  CC=6  out:42
    write_json  CC=1  out:2
    write_text  CC=1  out:2
  scripts.legacy_bridge.sync_check  [1 funcs]
    main  CC=6  out:12
  scripts.parse_proto  [1 funcs]
    parse_proto  CC=17  out:26
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
  gateway.main.health → gateway.delegation.get_delegation_health
  gateway.main.health_modules → gateway.delegation.get_delegation_health
  gateway.main.health_module → gateway.delegation.get_delegated_slice
  gateway.main.delegation_slices → gateway.delegation.list_delegated_slices
  gateway.main.delegation_slice_detail → gateway.delegation.get_delegated_slice
  gateway.main.sse_stream → gateway.sse.subscribe
  gateway.main.sse_stream → gateway.sse.event_generator
  gateway.main.cmd_create_user → gateway.user_handler.handle_create_user
  gateway.main.cmd_create_user → gateway.sse.push_to_subscribers
  gateway.main.cmd_dual_create_user → gateway.user_handler.handle_dual_write_user
  gateway.main.cmd_dual_create_user → gateway.sse.push_to_subscribers
  gateway.main.cmd_change_email → gateway.user_handler.handle_change_email
  gateway.main.cmd_change_email → gateway.sse.push_to_subscribers
  gateway.main.cmd_deactivate_user → gateway.user_handler.handle_deactivate_user
  gateway.main.cmd_deactivate_user → gateway.sse.push_to_subscribers
  gateway.main.query_get_user → gateway.user_handler.handle_get_user
  gateway.main.list_events → gateway.user_handler.handle_list_events
  gateway.main.cmd_index_search_entry → gateway.search_handler.handle_index_entry
  gateway.main.query_search → gateway.search_handler.handle_search
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
  scripts.generate_pydantic.main → scripts.parse_proto.parse_proto
  scripts.generate_pydantic.main → scripts.generate_pydantic.generate
  scripts.detect_migration_candidates.discover_candidate_paths → scripts.detect_migration_candidates.has_candidate_markers
  scripts.detect_migration_candidates.import_tokens → scripts.detect_migration_candidates.normalize_token
  scripts.detect_migration_candidates.analyze_candidate → scripts.detect_migration_candidates.normalize_token
  scripts.detect_migration_candidates.analyze_candidate → scripts.detect_migration_candidates.iter_files
  scripts.detect_migration_candidates.build_output_row → scripts.detect_migration_candidates.score_migration_candidate
  scripts.detect_migration_candidates.build_output_row → scripts.detect_migration_candidates.classify_extraction_target
  scripts.detect_migration_candidates.analyze_repository → scripts.detect_migration_candidates.discover_candidate_paths
  scripts.detect_migration_candidates.analyze_repository → scripts.detect_migration_candidates.analyze_candidate
  scripts.detect_migration_candidates.analyze_repository → scripts.detect_migration_candidates.build_output_row
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
# nodes: 134 | edges: 112 | modules: 26
# CC̄=1.7

HUBS[20]:
  scripts.legacy_bridge.analyze_service_boundaries.analyze_frontend_modules
    CC=43  in:1  out:66  total:67
  scripts.legacy_bridge.run_arch_migration_discovery.run_discovery
    CC=6  in:1  out:42  total:43
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.analyze_repository
    CC=19  in:1  out:35  total:36
  scripts.detect_migration_candidates.discover_candidate_paths
    CC=20  in:1  out:33  total:34
  scripts.legacy_bridge.run_arch_migration_discovery.profile_repository
    CC=18  in:1  out:33  total:34
  scripts.parse_proto.parse_proto
    CC=17  in:8  out:26  total:34
  scripts.legacy_bridge.generate_migration_wave_plan.build_waves
    CC=15  in:3  out:31  total:34
  scripts.legacy_bridge.analyze_service_boundaries.build_service_components
    CC=34  in:1  out:32  total:33
  scripts.legacy_bridge.generate_migration_wave_plan.main
    CC=8  in:0  out:33  total:33
  scripts.detect_migration_candidates.analyze_candidate
    CC=28  in:1  out:32  total:33
  scripts.legacy_bridge.analyze_service_boundaries.build_ts_index
    CC=10  in:1  out:30  total:31
  scripts.legacy_bridge.detect_cqrs_pattern_clusters.main
    CC=10  in:0  out:31  total:31
  scripts.legacy_bridge.delegation_plan.render_markdown
    CC=8  in:1  out:30  total:31
  scripts.legacy_bridge.generate_delegation_plan.main
    CC=4  in:0  out:27  total:27
  scripts.generate_incremental.main
    CC=11  in:0  out:24  total:24
  scripts.legacy_bridge.run_arch_migration_discovery.main
    CC=6  in:0  out:24  total:24
  scripts.legacy_bridge.analyze_service_boundaries.main
    CC=7  in:0  out:24  total:24
  scripts.legacy_bridge.diff_engine.diff_fields
    CC=12  in:3  out:19  total:22
  scripts.legacy_bridge.analyze_service_boundaries.build_backend_index
    CC=7  in:1  out:19  total:20
  scripts.schema_registry.SchemaRegistry.register
    CC=10  in:0  out:18  total:18

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
  scripts.conflict_resolver  [2 funcs]
    resolve_merge  CC=22  out:15
    _field_effects  CC=2  out:3
  scripts.detect_migration_candidates  [13 funcs]
    analyze_candidate  CC=28  out:32
    analyze_repository  CC=4  out:13
    build_output_row  CC=2  out:2
    classify_extraction_target  CC=19  out:12
    discover_candidate_paths  CC=20  out:33
    get_service_candidates  CC=4  out:7
    has_candidate_markers  CC=6  out:6
    import_tokens  CC=3  out:2
    iter_files  CC=8  out:1
    main  CC=5  out:17
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
  scripts.generate_pydantic  [2 funcs]
    generate  CC=5  out:6
    main  CC=3  out:9
  scripts.generate_sql  [3 funcs]
    _table_name  CC=1  out:2
    generate_sql  CC=6  out:6
    main  CC=3  out:9
  scripts.generate_zod  [2 funcs]
    main  CC=3  out:9
    to_zod  CC=4  out:7
  scripts.legacy_bridge.analyze_service_boundaries  [28 funcs]
    analyze  CC=2  out:10
    analyze_frontend_modules  CC=43  out:66
    backend_group_summary  CC=9  out:11
    build_backend_index  CC=7  out:19
    build_cleanup_checklist  CC=2  out:1
    build_service_components  CC=34  out:32
    build_target_structure  CC=2  out:1
    build_ts_index  CC=10  out:30
    choose_component_anchor  CC=1  out:2
    const_str  CC=3  out:2
  scripts.legacy_bridge.delegation_plan  [5 funcs]
    build_output_row  CC=3  out:15
    build_slice_blueprint  CC=1  out:2
    build_steps  CC=1  out:1
    render_markdown  CC=8  out:30
    to_slice_name  CC=1  out:4
  scripts.legacy_bridge.detect_cqrs_pattern_clusters  [7 funcs]
    analyze_repository  CC=19  out:35
    assign_clusters  CC=9  out:14
    deep_merge  CC=4  out:6
    load_config  CC=3  out:5
    main  CC=10  out:31
    normalize_config  CC=2  out:1
    parse_args  CC=1  out:8
  scripts.legacy_bridge.diff_engine  [1 funcs]
    diff_fields  CC=12  out:19
  scripts.legacy_bridge.generate_delegation_plan  [4 funcs]
    load_candidates  CC=4  out:5
    load_clusters  CC=7  out:7
    main  CC=4  out:27
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
  scripts.legacy_bridge.run_arch_migration_discovery  [8 funcs]
    build_delegation_plan  CC=2  out:5
    main  CC=6  out:24
    parse_args  CC=1  out:8
    profile_repository  CC=18  out:33
    resolve_output_dir  CC=2  out:2
    run_discovery  CC=6  out:42
    write_json  CC=1  out:2
    write_text  CC=1  out:2
  scripts.legacy_bridge.sync_check  [1 funcs]
    main  CC=6  out:12
  scripts.parse_proto  [1 funcs]
    parse_proto  CC=17  out:26
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
  gateway.main.health → gateway.delegation.get_delegation_health
  gateway.main.health_modules → gateway.delegation.get_delegation_health
  gateway.main.health_module → gateway.delegation.get_delegated_slice
  gateway.main.delegation_slices → gateway.delegation.list_delegated_slices
  gateway.main.delegation_slice_detail → gateway.delegation.get_delegated_slice
  gateway.main.sse_stream → gateway.sse.subscribe
  gateway.main.sse_stream → gateway.sse.event_generator
  gateway.main.cmd_create_user → gateway.user_handler.handle_create_user
  gateway.main.cmd_create_user → gateway.sse.push_to_subscribers
  gateway.main.cmd_dual_create_user → gateway.user_handler.handle_dual_write_user
  gateway.main.cmd_dual_create_user → gateway.sse.push_to_subscribers
  gateway.main.cmd_change_email → gateway.user_handler.handle_change_email
  gateway.main.cmd_change_email → gateway.sse.push_to_subscribers
  gateway.main.cmd_deactivate_user → gateway.user_handler.handle_deactivate_user
  gateway.main.cmd_deactivate_user → gateway.sse.push_to_subscribers
  gateway.main.query_get_user → gateway.user_handler.handle_get_user
  gateway.main.list_events → gateway.user_handler.handle_list_events
  gateway.main.cmd_index_search_entry → gateway.search_handler.handle_index_entry
  gateway.main.query_search → gateway.search_handler.handle_search
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
  scripts.generate_pydantic.main → scripts.parse_proto.parse_proto
  scripts.generate_pydantic.main → scripts.generate_pydantic.generate
  scripts.detect_migration_candidates.discover_candidate_paths → scripts.detect_migration_candidates.has_candidate_markers
  scripts.detect_migration_candidates.import_tokens → scripts.detect_migration_candidates.normalize_token
  scripts.detect_migration_candidates.analyze_candidate → scripts.detect_migration_candidates.normalize_token
  scripts.detect_migration_candidates.analyze_candidate → scripts.detect_migration_candidates.iter_files
  scripts.detect_migration_candidates.build_output_row → scripts.detect_migration_candidates.score_migration_candidate
  scripts.detect_migration_candidates.build_output_row → scripts.detect_migration_candidates.classify_extraction_target
  scripts.detect_migration_candidates.analyze_repository → scripts.detect_migration_candidates.discover_candidate_paths
  scripts.detect_migration_candidates.analyze_repository → scripts.detect_migration_candidates.analyze_candidate
  scripts.detect_migration_candidates.analyze_repository → scripts.detect_migration_candidates.build_output_row
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 74f 15346L | python:38,yaml:11,md:9,txt:4,proto:4,json:2,yml:1,generator:1,ini:1,shell:1 | 2026-04-24
# CC̄=1.7 | critical:14/597 | dups:0 | cycles:0

HEALTH[14]:
  🟡 CC    parse_proto CC=17 (limit:15)
  🟡 CC    _diff_messages CC=19 (limit:15)
  🟡 CC    discover_candidate_paths CC=20 (limit:15)
  🟡 CC    analyze_candidate CC=28 (limit:15)
  🟡 CC    score_migration_candidate CC=15 (limit:15)
  🟡 CC    classify_extraction_target CC=19 (limit:15)
  🟡 CC    resolve_merge CC=22 (limit:15)
  🟡 CC    profile_repository CC=18 (limit:15)
  🟡 CC    analyze_repository CC=19 (limit:15)
  🟡 CC    build_service_components CC=34 (limit:15)
  🟡 CC    select_execution_plan CC=20 (limit:15)
  🟡 CC    analyze_frontend_modules CC=43 (limit:15)
  🟡 CC    build_markdown CC=15 (limit:15)
  🟡 CC    build_waves CC=15 (limit:15)

REFACTOR[1]:
  1. split 14 high-CC methods  (CC>15)

PIPELINES[96]:
  [1] Src [__init__]: __init__
      PURITY: 100% pure
  [2] Src [connect]: connect
      PURITY: 100% pure
  [3] Src [disconnect]: disconnect
      PURITY: 100% pure
  [4] Src [broadcast]: broadcast
      PURITY: 100% pure
  [5] Src [_path_checks]: _path_checks
      PURITY: 100% pure

LAYERS:
  scripts/                        CC̄=4.9    ←in:3  →out:9  !! split
  │ !! analyze_service_boundaries   843L  2C   37m  CC=43     ←0
  │ !! schema_registry            543L  3C   16m  CC=19     ←1
  │ !! detect_migration_candidates   499L  2C   19m  CC=28     ←2
  │ !! run_arch_migration_discovery   459L  0C   14m  CC=18     ←0
  │ event_store                398L  4C   13m  CC=7      ←0
  │ !! detect_cqrs_pattern_clusters   369L  1C   14m  CC=19     ←0
  │ !! generate_migration_wave_plan   320L  2C    8m  CC=15     ←1
  │ legacy_registry            245L  2C    8m  CC=11     ←0
  │ !! conflict_resolver          236L  2C    5m  CC=22     ←0
  │ !! parse_proto                159L  0C    2m  CC=17     ←7
  │ generate_incremental       148L  0C    8m  CC=11     ←0
  │ delegation_plan            118L  0C    5m  CC=8      ←1
  │ dual_writer                114L  2C    6m  CC=5      ←0
  │ vector_clock               112L  1C    9m  CC=4      ←0
  │ diff_engine                109L  3C    1m  CC=12     ←2
  │ generate_json_schema        99L  0C    2m  CC=6      ←0
  │ normalizer                  98L  1C    2m  CC=3      ←2
  │ generate_sql                97L  0C    3m  CC=6      ←1
  │ generate_delegation_plan    96L  0C    4m  CC=7      ←0
  │ generate_pydantic           74L  0C    2m  CC=5      ←0
  │ migrator                    69L  0C    2m  CC=3      ←0
  │ generate_zod                67L  0C    2m  CC=4      ←1
  │ search_index                61L  1C    4m  CC=5      ←0
  │ report_generator            56L  0C    1m  CC=6      ←1
  │ migration_advisor           54L  0C    2m  CC=9      ←1
  │ idempotency_store           41L  1C    5m  CC=2      ←0
  │ sync_check                  39L  0C    1m  CC=6      ←0
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
  adapters/                       CC̄=1.0    ←in:0  →out:0
  │ user_adapter                36L  0C    2m  CC=1      ←0
  │ user_adapter                21L  0C    1m  CC=1      ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! SUMD.md                   1025L  0C  180m  CC=0.0    ←0
  │ !! SUMR.md                    998L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ README.md                  150L  0C    0m  CC=0.0    ←0
  │ tree.txt                   148L  0C    0m  CC=0.0    ←0
  │ TODO.md                     94L  0C    0m  CC=0.0    ←0
  │ CHANGELOG.md                92L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          69L  0C    0m  CC=0.0    ←0
  │ project.sh                  48L  0C    0m  CC=0.0    ←0
  │ buf.gen.yaml                25L  0C    0m  CC=0.0    ←0
  │ buf.yaml                    10L  0C    0m  CC=0.0    ←0
  │ requirements.txt             8L  0C    0m  CC=0.0    ←0
  │ pytest.ini                   5L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Dockerfile.generator         0L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                1548L  0C    0m  CC=0.0    ←0
  │ !! context.md                 554L  0C    0m  CC=0.0    ←0
  │ map.toon.yaml              451L  0C  180m  CC=0.0    ←0
  │ README.md                  339L  0C    0m  CC=0.0    ←0
  │ calls.toon.yaml            234L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         138L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml      115L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           56L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  49L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         39L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ !! delegation-plan.generated.json  1262L  0C    0m  CC=0.0    ←0
  │ !! migration-orchestrator-strategy.md   626L  0C    0m  CC=0.0    ←0
  │ refactor-delegation-architecture.md   116L  0C    0m  CC=0.0    ←0
  │
  scratch/                        CC̄=0.0    ←in:0  →out:0
  │ smoke_test_search           30L  0C    0m  CC=0.0    ←0
  │ smoke_test_dual_write       27L  0C    0m  CC=0.0    ←0
  │
  contracts/                      CC̄=0.0    ←in:0  →out:0
  │ search.proto                40L  0C    0m  CC=0.0    ←0
  │ user.proto                  27L  0C    0m  CC=0.0    ←0
  │ user.proto                  20L  0C    0m  CC=0.0    ←0
  │ user_legacy.schema.json     18L  0C    0m  CC=0.0    ←0
  │ user_legacy.v1.proto        14L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-api-smoke.testql.toon.yaml    21L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     Dockerfile.generator                      0L
     Makefile                                  0L
     gateway/Dockerfile                        0L
     gateway/__init__.py                       0L

COUPLING:
                                       scripts  scripts.legacy_bridge
                scripts                     ──                      9  !! fan-out
  scripts.legacy_bridge                      3                     ──  hub
  CYCLES: none
  HUB: scripts.legacy_bridge/ (fan-in=9)
  SMELL: scripts/ fan-out=9 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 10 groups | 38f 6436L | 2026-04-24

SUMMARY:
  files_scanned: 38
  total_lines:   6436
  dup_groups:    10
  dup_fragments: 23
  saved_lines:   83
  scan_ms:       5903

HOTSPOTS[7] (files with most duplication):
  scripts/legacy_bridge/analyze_service_boundaries.py  dup=30L  groups=5  frags=5  (0.5%)
  scripts/legacy_bridge/detect_cqrs_pattern_clusters.py  dup=25L  groups=4  frags=4  (0.4%)
  scripts/generate_pydantic.py  dup=12L  groups=1  frags=1  (0.2%)
  scripts/generate_sql.py  dup=12L  groups=1  frags=1  (0.2%)
  scripts/generate_zod.py  dup=12L  groups=1  frags=1  (0.2%)
  gateway/main.py  dup=10L  groups=1  frags=2  (0.2%)
  scripts/legacy_bridge/run_arch_migration_discovery.py  dup=8L  groups=2  frags=2  (0.1%)

DUPLICATES[10] (ranked by impact):
  [1a1a5665e06d1f8a]   STRU  main  L=12 N=3 saved=24 sim=1.00
      scripts/generate_pydantic.py:59-70  (main)
      scripts/generate_sql.py:82-93  (main)
      scripts/generate_zod.py:52-63  (main)
  [e140be6cf51d2681]   EXAC  read_text  L=5 N=3 saved=10 sim=1.00
      scripts/detect_migration_candidates.py:189-193  (read_text)
      scripts/legacy_bridge/analyze_service_boundaries.py:170-174  (read_text)
      scripts/legacy_bridge/run_arch_migration_discovery.py:113-117  (read_text)
  [42491376f509549f]   EXAC  deep_merge  L=8 N=2 saved=8 sim=1.00
      scripts/legacy_bridge/analyze_service_boundaries.py:82-89  (deep_merge)
      scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:84-91  (deep_merge)
  [2b4dc3f0af97a67d]   STRU  __init__  L=4 N=3 saved=8 sim=1.00
      scripts/dual_writer.py:24-27  (__init__)
      scripts/idempotency_store.py:11-14  (__init__)
      scripts/search_index.py:12-15  (__init__)
  [9600d037241ef7f6]   STRU  _connect  L=8 N=2 saved=8 sim=1.00
      scripts/event_store.py:58-65  (_connect)
      scripts/schema_registry.py:114-121  (_connect)
  [2bf86c6a91094d26]   EXAC  load_config  L=7 N=2 saved=7 sim=1.00
      scripts/legacy_bridge/analyze_service_boundaries.py:92-98  (load_config)
      scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:94-100  (load_config)
  [56a0a4b947778620]   EXAC  find  L=5 N=2 saved=5 sim=1.00
      scripts/legacy_bridge/analyze_service_boundaries.py:431-435  (find)
      scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:186-190  (find)
  [1c853fca582fc078]   EXAC  union  L=5 N=2 saved=5 sim=1.00
      scripts/legacy_bridge/analyze_service_boundaries.py:437-441  (union)
      scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:192-196  (union)
  [f323e07cca628456]   STRU  health_module  L=5 N=2 saved=5 sim=1.00
      gateway/main.py:133-137  (health_module)
      gateway/main.py:146-150  (delegation_slice_detail)
  [cae7903dcb44e30d]   STRU  resolve_path  L=3 N=2 saved=3 sim=1.00
      scripts/legacy_bridge/generate_migration_wave_plan.py:89-91  (resolve_path)
      scripts/legacy_bridge/run_arch_migration_discovery.py:120-122  (resolve_output_dir)

REFACTOR[10] (ranked by priority):
  [1] ○ extract_function   → scripts/utils/main.py
      WHY: 3 occurrences of 12-line block across 3 files — saves 24 lines
      FILES: scripts/generate_pydantic.py, scripts/generate_sql.py, scripts/generate_zod.py
  [2] ○ extract_function   → scripts/utils/read_text.py
      WHY: 3 occurrences of 5-line block across 3 files — saves 10 lines
      FILES: scripts/detect_migration_candidates.py, scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/run_arch_migration_discovery.py
  [3] ○ extract_function   → scripts/legacy_bridge/utils/deep_merge.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/detect_cqrs_pattern_clusters.py
  [4] ○ extract_function   → scripts/utils/__init__.py
      WHY: 3 occurrences of 4-line block across 3 files — saves 8 lines
      FILES: scripts/dual_writer.py, scripts/idempotency_store.py, scripts/search_index.py
  [5] ○ extract_function   → scripts/utils/_connect.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: scripts/event_store.py, scripts/schema_registry.py
  [6] ○ extract_function   → scripts/legacy_bridge/utils/load_config.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/detect_cqrs_pattern_clusters.py
  [7] ○ extract_function   → scripts/legacy_bridge/utils/find.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/detect_cqrs_pattern_clusters.py
  [8] ○ extract_function   → scripts/legacy_bridge/utils/union.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: scripts/legacy_bridge/analyze_service_boundaries.py, scripts/legacy_bridge/detect_cqrs_pattern_clusters.py
  [9] ○ extract_function   → gateway/utils/health_module.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: gateway/main.py
  [10] ○ extract_function   → scripts/legacy_bridge/utils/resolve_path.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: scripts/legacy_bridge/generate_migration_wave_plan.py, scripts/legacy_bridge/run_arch_migration_discovery.py

QUICK_WINS[6] (low risk, high savings — do first):
  [1] extract_function   saved=24L  → scripts/utils/main.py
      FILES: generate_pydantic.py, generate_sql.py, generate_zod.py
  [2] extract_function   saved=10L  → scripts/utils/read_text.py
      FILES: detect_migration_candidates.py, analyze_service_boundaries.py, run_arch_migration_discovery.py
  [3] extract_function   saved=8L  → scripts/legacy_bridge/utils/deep_merge.py
      FILES: analyze_service_boundaries.py, detect_cqrs_pattern_clusters.py
  [4] extract_function   saved=8L  → scripts/utils/__init__.py
      FILES: dual_writer.py, idempotency_store.py, search_index.py
  [5] extract_function   saved=8L  → scripts/utils/_connect.py
      FILES: event_store.py, schema_registry.py
  [6] extract_function   saved=7L  → scripts/legacy_bridge/utils/load_config.py
      FILES: analyze_service_boundaries.py, detect_cqrs_pattern_clusters.py

EFFORT_ESTIMATE (total ≈ 2.8h):
  medium main                                saved=24L  ~48min
  easy   read_text                           saved=10L  ~20min
  easy   deep_merge                          saved=8L  ~16min
  easy   __init__                            saved=8L  ~16min
  easy   _connect                            saved=8L  ~16min
  easy   load_config                         saved=7L  ~14min
  easy   find                                saved=5L  ~10min
  easy   union                               saved=5L  ~10min
  easy   health_module                       saved=5L  ~10min
  easy   resolve_path                        saved=3L  ~6min

METRICS-TARGET:
  dup_groups:  10 → 0
  saved_lines: 83 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 402 func | 10f | 2026-04-24

NEXT[0]: no refactoring needed

RISKS[0]: none

METRICS-TARGET:
  CC̄:          0.2 → ≤0.1
  max-CC:      6 → ≤3
  god-modules: 0 → 0
  high-CC(≥15): 0 → ≤0
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
  prev CC̄=1.8 → now CC̄=0.2
```

## Intent

protos
