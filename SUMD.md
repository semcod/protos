# protogate

Migration tool and delegation platform for extracting bounded slices from legacy systems

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `protogate`
- **version**: `0.1.1`
- **python_requires**: `>=3.9`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, requirements.txt, Makefile, testql(1), app.doql.less, goal.yaml, .env.example, docker-compose.yml, project/(2 analysis files)

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

## Interfaces

### CLI Entry Points

- `protogate`

### testql Scenarios

#### `testql-scenarios/generated-api-smoke.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-smoke.testql.toon.yaml
# SCENARIO: Auto-generated API Smoke Tests
# TYPE: api
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 5000

API[9]{method, endpoint, expected_status}:
  GET, /events/stream, 200
  GET, /health, 200
  GET, /health/modules, 200
  GET, /delegation/slices, 200
  POST, /commands/user/create, 201
  POST, /commands/user/dual-create, 201
  GET, /events, 200
  POST, /commands/search/index, 201
  GET, /queries/search, 200

ASSERT[1]{field, operator, expected}:
  status, <, 400
```

## Workflows

## Configuration

```yaml
project:
  name: protogate
  version: 0.1.1
  env: local
```

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

## Deployment

```bash markpact:run
pip install protogate

# development install
pip install -e .[dev]
```

### Requirements Files

#### `requirements.txt`

- `protobuf>=4.25.0`
- `pydantic>=2.0.0`
- `pydantic[email]>=2.0.0`
- `fastapi>=0.111.0`
- `uvicorn[standard]>=0.29.0`
- `sse-starlette>=2.1.0`

### Docker Compose (`docker-compose.yml`)

- **generator** image=`{'context': '.', 'dockerfile': 'Dockerfile.generator'}`
- **gateway** image=`{'context': '.', 'dockerfile': 'gateway/Dockerfile'}` ports: `8080:8080`

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`protogate`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `protogate/__init__.py:__version__`

## Makefile Targets

- `all` — Default: run all generators (requires buf on PATH for the proto target)
- `proto` — Run buf generate (requires buf CLI: https://buf.build/docs/installation)
- `zod` — TypeScript Zod schemas
- `python` — Pydantic Python models
- `json` — JSON Schema (draft-07)
- `sql` — SQL DDL
- `proto-changed` — Detect changed proto files against main branch
- `generate-incremental` — Incremental mode: only regenerate changed protogate artifacts
- `clean` — Remove all generated artefacts (keeps the directory skeletons)
- `registry-register` — Register the default proto file (contracts/user/v1/user.proto) in the registry
- `registry-check` — Check compatibility of the default proto without registering
- `registry-list` — List all schemas in the registry
- `proto-all` — Full generation: buf (gRPC stubs) + all custom generators
- `gateway` — Run the FastAPI gateway in development mode (hot-reload)
- `gateway-docker` — Build + run gateway via Docker
- `ci` — Full CI pipeline: lint → generate → test → registry check
- `legacy-register` — Register legacy JSON schema
- `diff-legacy` — Diff legacy vs proto
- `legacy-report` — Generate detailed migration report
- `legacy-list` — List all schemas
- `sync-check` — Full sync check (fails if readiness < 1.0)
- `bootstrap-legacy` — Bootstrap EventStore from Legacy DB

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# protos | 87f 12368L | python:75,typescript:9,shell:2,less:1 | 2026-04-24
# stats: 313 func | 95 cls | 87 mod | CC̄=5.0 | critical:39 | cycles:0
# alerts[5]: CC _calculate_module_stats=26; CC build_service_boundary_decision_report=21; CC discover_candidate_paths=20; CC select_execution_plan=20; CC analyze_repository=20
# hotspots[5]: run_discovery fan=37; analyze_repository fan=26; build_ts_index fan=21; main fan=21; main fan=20
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[87]:
  adapters/legacy_to_proto/user_adapter.py,37
  adapters/proto_to_legacy/user_adapter.py,22
  app.doql.less,159
  gateway/__init__.py,1
  gateway/delegation.py,148
  gateway/main.py,333
  gateway/search_handler.py,47
  gateway/sse.py,106
  gateway/tests/test_gateway.py,12
  gateway/user_handler.py,151
  gateway/ws.py,77
  generated/python/identification_v1_models.py,32
  generated/python/search_v1_models.py,36
  generated/python/user_v1_models.py,17
  generated/python/user_v2_models.py,22
  generated/python_cli/examples_identification_v1_identification_models.py,32
  generated/python_cli/legacy_bridge_user_legacy.v1_models.py,17
  generated/python_cli/search_v1_search_models.py,36
  generated/python_cli/user_v1_user_models.py,19
  generated/python_cli/user_v2_user_models.py,22
  generated/ts/zod/identification_v1.ts,33
  generated/ts/zod/search_v1.ts,40
  generated/ts/zod/user_v1.ts,19
  generated/ts/zod/user_v2.ts,22
  generated/ts_cli/examples_identification_v1_identification.ts,33
  generated/ts_cli/legacy_bridge_user_legacy.v1.ts,13
  generated/ts_cli/search_v1_search.ts,40
  generated/ts_cli/user_v1_user.ts,19
  generated/ts_cli/user_v2_user.ts,22
  project.sh,48
  protogate/__init__.py,9
  protogate/cli.py,292
  scratch/smoke_test_dual_write.py,28
  scratch/smoke_test_search.py,31
  scratch/swop_pipeline_service_id.py,90
  scratch/swop_scan_c2004.py,238
  scripts/__init__.py,1
  scripts/conflict_resolver.py,247
  scripts/detect_migration_candidates.py,547
  scripts/dual_writer.py,115
  scripts/event_store.py,399
  scripts/generate_incremental.py,149
  scripts/generate_json_schema.py,100
  scripts/generate_pydantic.py,147
  scripts/generate_sql.py,98
  scripts/generate_zod.py,130
  scripts/idempotency_store.py,42
  scripts/legacy_bridge/__init__.py,1
  scripts/legacy_bridge/analyze_service_boundaries.py,1345
  scripts/legacy_bridge/candidate_selection.py,57
  scripts/legacy_bridge/delegation_plan.py,151
  scripts/legacy_bridge/detect_cqrs_pattern_clusters.py,477
  scripts/legacy_bridge/diff_engine.py,110
  scripts/legacy_bridge/generate_delegation_plan.py,117
  scripts/legacy_bridge/generate_migration_wave_plan.py,339
  scripts/legacy_bridge/migration_advisor.py,55
  scripts/legacy_bridge/migrator.py,70
  scripts/legacy_bridge/normalizer.py,99
  scripts/legacy_bridge/report_generator.py,57
  scripts/legacy_bridge/report_rendering.py,208
  scripts/legacy_bridge/run_arch_migration_discovery.py,700
  scripts/legacy_bridge/swop_integration.py,373
  scripts/legacy_bridge/sync_check.py,40
  scripts/legacy_registry.py,246
  scripts/parse_proto.py,320
  scripts/schema_registry.py,544
  scripts/search_index.py,62
  scripts/vector_clock.py,113
  tests/conftest.py,3
  tests/test_analyze_service_boundaries.py,170
  tests/test_conflict_resolver.py,371
  tests/test_delegation_plan.py,54
  tests/test_delegation_registry.py,54
  tests/test_detect_cqrs_pattern_clusters.py,69
  tests/test_detect_migration_candidates.py,128
  tests/test_diff_engine.py,71
  tests/test_dual_write.py,78
  tests/test_event_store.py,161
  tests/test_generate_migration_wave_plan.py,43
  tests/test_generators.py,259
  tests/test_incremental.py,81
  tests/test_legacy_registry.py,55
  tests/test_migrator.py,49
  tests/test_report_rendering.py,103
  tests/test_run_arch_migration_discovery.py,427
  tests/test_schema_registry.py,428
  tree.sh,2
D:
  adapters/legacy_to_proto/user_adapter.py:
    e: legacy_to_proto,wrap_for_event_store
    legacy_to_proto(legacy_json)
    wrap_for_event_store(legacy_json)
  adapters/proto_to_legacy/user_adapter.py:
    e: proto_to_legacy
    proto_to_legacy(proto_dict)
  gateway/__init__.py:
  gateway/delegation.py:
    e: get_delegated_slice,list_delegated_slices,get_delegation_health,DelegatedSlice
    DelegatedSlice: _path_checks(3),health(1),summary(1),detail(1)
    get_delegated_slice(name)
    list_delegated_slices(root)
    get_delegation_health(root)
  gateway/main.py:
    e: lifespan,health,health_modules,health_module,delegation_slices,delegation_slice_detail,websocket_endpoint,sse_stream,cmd_create_user,cmd_dual_create_user,cmd_change_email,cmd_deactivate_user,query_get_user,list_events,cmd_index_search_entry,query_search,CreateUserRequest,DualCreateUserRequest,IndexEntryRequest,ChangeEmailRequest
    CreateUserRequest:
    DualCreateUserRequest:
    IndexEntryRequest:
    ChangeEmailRequest:
    lifespan(app)
    health()
    health_modules()
    health_module(slice_name)
    delegation_slices()
    delegation_slice_detail(slice_name)
    websocket_endpoint(ws)
    sse_stream(request)
    cmd_create_user(body)
    cmd_dual_create_user(body)
    cmd_change_email(user_id;body)
    cmd_deactivate_user(user_id)
    query_get_user(user_id)
    list_events(aggregate_id)
    cmd_index_search_entry(body)
    query_search(q;category;limit)
  gateway/search_handler.py:
    e: handle_index_entry,handle_search
    handle_index_entry(id;title;category;content;metadata)
    handle_search(query;category;limit)
  gateway/sse.py:
    e: subscribe,unsubscribe,push_to_subscribers,event_generator
    subscribe(q)
    unsubscribe(q)
    push_to_subscribers(event_type;payload)
    event_generator(request;queue)
  gateway/tests/test_gateway.py:
    e: test_placeholder,test_import
    test_placeholder()
    test_import()
  gateway/user_handler.py:
    e: handle_create_user,handle_dual_write_user,handle_change_email,handle_deactivate_user,handle_get_user,handle_list_events
    handle_create_user(email;first_name;last_name)
    handle_dual_write_user(command_id;email;first_name;last_name;age)
    handle_change_email(user_id;new_email)
    handle_deactivate_user(user_id)
    handle_get_user(user_id)
    handle_list_events(aggregate_id)
  gateway/ws.py:
    e: ConnectionManager
    ConnectionManager: __init__(0),connect(1),disconnect(1),broadcast(2)  # Thread-safe (asyncio-safe) WebSocket broadcast pool.
  generated/python/identification_v1_models.py:
    e: IdentifierType,IdentifyUserCommand,UserIdentificationReadModel,UserIdentifiedEvent
    IdentifierType:
    IdentifyUserCommand:
    UserIdentificationReadModel:
    UserIdentifiedEvent:
  generated/python/search_v1_models.py:
    e: IndexEntryCommand,EntryIndexed,SearchRequest,SearchResponse,Result
    IndexEntryCommand:
    EntryIndexed:
    SearchRequest:
    SearchResponse:
    Result:
  generated/python/user_v1_models.py:
    e: CreateUserCommand,GetUserQuery,User
    CreateUserCommand:
    GetUserQuery:
    User:
  generated/python/user_v2_models.py:
    e: CreateUserCommand,GetUserQuery,User
    CreateUserCommand:
    GetUserQuery:
    User:
  generated/python_cli/examples_identification_v1_identification_models.py:
    e: IdentifierType,IdentifyUserCommand,UserIdentificationReadModel,UserIdentifiedEvent
    IdentifierType:
    IdentifyUserCommand:
    UserIdentificationReadModel:
    UserIdentifiedEvent:
  generated/python_cli/legacy_bridge_user_legacy.v1_models.py:
    e: LegacyUser
    LegacyUser:
  generated/python_cli/search_v1_search_models.py:
    e: IndexEntryCommand,EntryIndexed,SearchRequest,SearchResponse,Result
    IndexEntryCommand:
    EntryIndexed:
    SearchRequest:
    SearchResponse:
    Result:
  generated/python_cli/user_v1_user_models.py:
    e: CreateUserCommand,GetUserQuery,User
    CreateUserCommand:
    GetUserQuery:
    User:
  generated/python_cli/user_v2_user_models.py:
    e: CreateUserCommand,GetUserQuery,User
    CreateUserCommand:
    GetUserQuery:
    User:
  protogate/__init__.py:
  protogate/cli.py:
    e: run_command,cmd_generate,cmd_registry,cmd_legacy,cmd_gateway,cmd_ci,cmd_discovery,cmd_clean,_proto_to_output_name,_batch_generate,cmd_generate_pydantic,cmd_generate_zod,main
    run_command(cmd;cwd)
    cmd_generate(args)
    cmd_registry(args)
    cmd_legacy(args)
    cmd_gateway(args)
    cmd_ci(args)
    cmd_discovery(args)
    cmd_clean(args)
    _proto_to_output_name(proto_path;suffix)
    _batch_generate(args;suffix;script_name;generate_func_name)
    cmd_generate_pydantic(args)
    cmd_generate_zod(args)
    main()
  scratch/smoke_test_dual_write.py:
  scratch/smoke_test_search.py:
  scratch/swop_pipeline_service_id.py:
    e: main
    main()
  scratch/swop_scan_c2004.py:
    e: _kind_by_suffix,_base_names,_kind_by_base,collect_ground_truth,run_swop_scan,main
    _kind_by_suffix(name)
    _base_names(node)
    _kind_by_base(bases)
    collect_ground_truth(root)
    run_swop_scan()
    main()
  scripts/__init__.py:
  scripts/conflict_resolver.py:
    e: _field_effects,UnresolvableConflictError,ConflictResolver
    UnresolvableConflictError: __init__(2)  # Raised when two concurrent events cannot be automatically me
    ConflictResolver: __post_init__(0),resolve_lww(2),_check_exclusive_event_pairs(2),_check_field_conflicts(2),resolve_merge(2)  # Resolves conflicts between concurrent event streams.
    _field_effects(event_type;payload;effect_map)
  scripts/detect_migration_candidates.py:
    e: normalize_token,has_candidate_markers,infer_kind,discover_candidate_paths,iter_files,read_text,extract_python_imports,extract_ts_imports,import_tokens,count_api_routes,count_outbound_api_calls,_check_candidate_flags,_analyze_file_content,analyze_candidate,score_migration_candidate,classify_extraction_target,build_output_row,analyze_repository,get_service_candidates,parse_args,main,CandidatePath,CandidateMetrics
    CandidatePath:
    CandidateMetrics:
    normalize_token(value)
    has_candidate_markers(path)
    infer_kind(path)
    discover_candidate_paths(repo_root)
    iter_files(path)
    read_text(path)
    extract_python_imports(content)
    extract_ts_imports(content)
    import_tokens(specifier)
    count_api_routes(path;content)
    count_outbound_api_calls(content)
    _check_candidate_flags(candidate_path)
    _analyze_file_content(file_path;content;current_alias;other_aliases;normalized_top_level_names)
    analyze_candidate(candidate;all_candidates;top_level_names)
    score_migration_candidate(metrics)
    classify_extraction_target(metrics)
    build_output_row(metrics)
    analyze_repository(repo_root)
    get_service_candidates(rows;min_service_score)
    parse_args()
    main()
  scripts/dual_writer.py:
    e: LegacyDB,DualWriter
    LegacyDB: __init__(1),_init_db(0),upsert_user(1),get_all_users(0)  # Simulated legacy database.
    DualWriter: __init__(3),execute_create_user(2)
  scripts/event_store.py:
    e: _connect,make_user_replay_engine,StoredEvent,Snapshot,EventStore,ReplayEngine
    StoredEvent:
    Snapshot:
    EventStore: __init__(1),append(4),get_stream(2),iter_all(0),save_snapshot(3),load_snapshot(1),merge_streams(4),_current_version(1),_row_to_event(1)  # Append-only event store backed by SQLite.
    ReplayEngine: register(1),replay(2)  # Rebuild aggregate state by replaying events from the event s
    _connect(db_path)
    make_user_replay_engine(store)
  scripts/generate_incremental.py:
    e: file_hash,load_cache,save_cache,should_regenerate,_stem,_write,regenerate,main
    file_hash(path)
    load_cache()
    save_cache(cache)
    should_regenerate(file;cache)
    _stem(proto_path)
    _write(path;content)
    regenerate(proto_path)
    main()
  scripts/generate_json_schema.py:
    e: generate,main
    generate(ast;registry_id;registry_version)
    main()
  scripts/generate_pydantic.py:
    e: _flatten_messages,_flatten_enums,_py_type,generate,main
    _flatten_messages(ast)
    _flatten_enums(ast)
    _py_type(field;message_names;enum_names)
    generate(ast)
    main()
  scripts/generate_sql.py:
    e: _table_name,generate_sql,main
    _table_name(message_name)
    generate_sql(ast)
    main()
  scripts/generate_zod.py:
    e: _flatten_messages,_flatten_enums,_zod_type,to_zod,main
    _flatten_messages(ast)
    _flatten_enums(ast)
    _zod_type(field;message_names;enum_names)
    to_zod(ast)
    main()
  scripts/idempotency_store.py:
    e: IdempotencyStore
    IdempotencyStore: __init__(1),_init_db(0),is_processed(1),mark_processed(2),get_response(1)
  scripts/legacy_bridge/__init__.py:
  scripts/legacy_bridge/analyze_service_boundaries.py:
    e: deep_merge,load_config,parse_args,is_ignored,iter_files,strip_source_suffix,extract_prefixed_module,matches_page_pattern,detect_frontend_module,read_text,resolve_candidate_file,resolve_ts_import,parse_ts_import_specs,normalize_api_group,extract_api_groups,build_ts_index,const_str,parse_router_prefixes,parse_python_imports,route_group_from_prefixes,counter_rows,merge_named_rows,build_backend_index,backend_group_summary,transitive_closure,route_group_from_api_group,service_slug,classify_delivery,choose_component_anchor,_build_eligible_modules,_apply_merge_hints,_determine_component_action,_build_component_row,build_service_components,select_execution_plan,build_target_structure,build_cleanup_checklist,_build_module_index,_calculate_module_stats,_generate_merge_hints,analyze_frontend_modules,_append_execution_plan_section,_append_service_components_section,_append_recommended_candidates_section,_append_merge_hints_section,_append_frontend_modules_section,build_markdown,build_execution_plan_markdown,build_target_structure_markdown,build_cleanup_markdown,_build_cqrs_endpoint_templates,build_service_blueprint_markdown,build_cqrs_model_boundaries_markdown,analyze,write_outputs,main,TsFile,PyRouteFile
    TsFile:
    PyRouteFile:
    deep_merge(base;override)
    load_config(config_path)
    parse_args()
    is_ignored(path;ignored_names)
    iter_files(root;suffixes;ignored_names)
    strip_source_suffix(name)
    extract_prefixed_module(name;rules)
    matches_page_pattern(rel;patterns)
    detect_frontend_module(path;root;config)
    read_text(path)
    resolve_candidate_file(path;allowed_roots)
    resolve_ts_import(current;spec;workspace_root;allowed_roots;alias_roots)
    parse_ts_import_specs(source)
    normalize_api_group(path;group_depth)
    extract_api_groups(source;api_pattern;group_depth)
    build_ts_index(workspace_root;config;api_pattern)
    const_str(node)
    parse_router_prefixes(tree)
    parse_python_imports(tree)
    route_group_from_prefixes(rel_path;prefixes)
    counter_rows(counter;limit)
    merge_named_rows(groups;field;limit)
    build_backend_index(workspace_root;config)
    backend_group_summary(index)
    transitive_closure(start;index)
    route_group_from_api_group(api_group)
    service_slug(module)
    classify_delivery(iframe_score;cross_targets;backend_groups)
    choose_component_anchor(component_rows)
    _build_eligible_modules(module_rows)
    _apply_merge_hints(eligible;merge_hints)
    _determine_component_action(rows;avg_iframe_score;cross_targets;route_groups)
    _build_component_row(rows;backend_groups)
    build_service_components(module_rows;merge_hints;backend_groups)
    select_execution_plan(service_components;top_services)
    build_target_structure(execution_plan)
    build_cleanup_checklist(execution_plan)
    _build_module_index(ts_index)
    _calculate_module_stats(module;owned_files;ts_index;backend_groups;cross_edges;shared_modules)
    _generate_merge_hints(ranked;cross_edges)
    analyze_frontend_modules(ts_index;backend_index;top_services;shared_modules)
    _append_execution_plan_section(lines;payload)
    _append_service_components_section(lines;payload)
    _append_recommended_candidates_section(lines;payload)
    _append_merge_hints_section(lines;payload)
    _append_frontend_modules_section(lines;payload)
    build_markdown(payload)
    build_execution_plan_markdown(payload)
    build_target_structure_markdown(payload)
    build_cleanup_markdown(payload)
    _build_cqrs_endpoint_templates(service_data)
    build_service_blueprint_markdown(service_slug;payload)
    build_cqrs_model_boundaries_markdown(payload)
    analyze(repo_root;config;top_services)
    write_outputs(output_dir;basename;payload)
    main()
  scripts/legacy_bridge/candidate_selection.py:
    e: parse_score,get_candidate_exclusion_reasons,is_delegable_candidate
    parse_score(row)
    get_candidate_exclusion_reasons(row)
    is_delegable_candidate(row)
  scripts/legacy_bridge/delegation_plan.py:
    e: _to_float,_normalize_shared_types_package,_normalize_reasons,to_slice_name,build_steps,build_slice_blueprint,build_output_row,render_markdown
    _to_float(value;default)
    _normalize_shared_types_package(value)
    _normalize_reasons(value)
    to_slice_name(module)
    build_steps(module)
    build_slice_blueprint(module)
    build_output_row(row;cluster_meta)
    render_markdown(rows;limit;clusters)
  scripts/legacy_bridge/detect_cqrs_pattern_clusters.py:
    e: deep_merge,load_config,normalize_config,parse_args,read_text,load_candidate_scores,module_from_types_path,split_tokens,classify_pattern,jaccard,assign_clusters,shared_tokens_for_module,analyze_repository,render_markdown,main,ModulePattern
    ModulePattern:
    deep_merge(base;override)
    load_config(config_path)
    normalize_config(config)
    parse_args()
    read_text(path)
    load_candidate_scores(path)
    module_from_types_path(path;root)
    split_tokens(tokens)
    classify_pattern(commands;events;config)
    jaccard(left;right)
    assign_clusters(signature_map;pattern_map;threshold)
    shared_tokens_for_module(repo_root;module)
    analyze_repository(repo_root;config;candidate_scores)
    render_markdown(payload)
    main()
  scripts/legacy_bridge/diff_engine.py:
    e: diff_fields,DiffKind,DiffEntry,DiffReport
    DiffKind:
    DiffEntry:
    DiffReport:
    diff_fields(legacy_fields;proto_fields)
  scripts/legacy_bridge/generate_delegation_plan.py:
    e: load_candidates,load_clusters,dedupe_candidates,parse_args,main
    load_candidates(path)
    load_clusters(path)
    dedupe_candidates(rows)
    parse_args()
    main()
  scripts/legacy_bridge/generate_migration_wave_plan.py:
    e: parse_args,load_json,resolve_path,determine_wave_name,estimate_effort,build_waves,render_markdown,main,WaveModule,MigrationWave
    WaveModule:
    MigrationWave:
    parse_args()
    load_json(path)
    resolve_path(repo_root;raw)
    determine_wave_name(pattern;extraction_target)
    estimate_effort(modules)
    build_waves(clusters_data;candidates_data;max_waves)
    render_markdown(waves)
    main()
  scripts/legacy_bridge/migration_advisor.py:
    e: suggest_proto_additions,get_migration_summary
    suggest_proto_additions(report;message_name)
    get_migration_summary(report)
  scripts/legacy_bridge/migrator.py:
    e: migrate_users,main
    migrate_users(legacy_db;event_store)
    main()
  scripts/legacy_bridge/normalizer.py:
    e: normalize_json_schema,normalize_proto_ast,NormalizedField
    NormalizedField:
    normalize_json_schema(schema;origin)
    normalize_proto_ast(message_ast)
  scripts/legacy_bridge/report_generator.py:
    e: generate_markdown_report
    generate_markdown_report(subject;legacy_version;proto_version;report;suggestion)
  scripts/legacy_bridge/report_rendering.py:
    e: _append_reason_counts_section,_append_simple_list_section,_append_artifacts_table,_format_detail_value,_append_detail_section,render_summary_markdown,render_excluded_candidates_markdown,render_delegation_decisions_markdown,render_service_boundary_decisions_markdown
    _append_reason_counts_section(lines;heading;reason_counts)
    _append_simple_list_section(lines;heading;items)
    _append_artifacts_table(lines;artifacts)
    _format_detail_value(row;key;value_format)
    _append_detail_section(lines)
    render_summary_markdown(summary)
    render_excluded_candidates_markdown(payload)
    render_delegation_decisions_markdown(payload)
    render_service_boundary_decisions_markdown(payload)
  scripts/legacy_bridge/run_arch_migration_discovery.py:
    e: parse_args,read_text,resolve_output_dir,profile_repository,render_repository_profile_markdown,render_module_candidates_markdown,_parse_score,build_excluded_candidates_report,build_service_boundary_decision_report,build_delegation_decision_report,build_delegation_plan,build_summary,write_text,write_json,relative_artifact_path,run_discovery,main
    parse_args()
    read_text(path)
    resolve_output_dir(repo_root;raw_output_dir)
    profile_repository(repo_root;config)
    render_repository_profile_markdown(profile)
    render_module_candidates_markdown(rows)
    _parse_score(row)
    build_excluded_candidates_report(rows)
    build_service_boundary_decision_report(payload)
    build_delegation_decision_report(rows)
    build_delegation_plan(rows;limit;clusters_by_module)
    build_summary(repo_root;profile;candidate_rows;service_boundary_payload;cqrs_pattern_payload;delegation_rows;wave_plan_payload;artifact_paths;service_boundary_decisions_payload;swop_payload)
    write_text(path;content)
    write_json(path;payload)
    relative_artifact_path(path;repo_root)
    run_discovery(repo_root;output_dir;config_path;top_services;delegation_limit;swop_repo;swop_cqrs_root;swop_contexts)
    main()
  scripts/legacy_bridge/swop_integration.py:
    e: infer_contexts_from_service_boundaries,_eligible_groups,_context_score,_group_match_score,_name_tokens,_normalize_token,_relative_path,_default_swop_python,_swop_subprocess_script,run_swop_pipeline,render_swop_markdown,render_swop_json
    infer_contexts_from_service_boundaries(service_boundaries;repo_root;cqrs_root)
    _eligible_groups(row;base_dir)
    _context_score(row;group)
    _group_match_score(group;row)
    _name_tokens()
    _normalize_token(value)
    _relative_path(path;root)
    _default_swop_python(swop_repo)
    _swop_subprocess_script()
    run_swop_pipeline(repo_root;output_dir;swop_repo;service_boundaries;cqrs_root;contexts;swop_python)
    render_swop_markdown(payload)
    render_swop_json(payload)
  scripts/legacy_bridge/sync_check.py:
    e: main
    main()
  scripts/legacy_registry.py:
    e: main,LegacySchemaVersion,LegacySchemaRegistry
    LegacySchemaVersion:
    LegacySchemaRegistry: __init__(1),_init_db(0),register(6),_get_next_version(2),get_latest(2),_row_to_sv(1),list_schemas(0)
    main()
  scripts/parse_proto.py:
    e: _parse_reserved_numbers,_to_dict,_parse_top_level_declarations,_handle_message_start,_handle_enum_start,_handle_block_end,_handle_enum_value,_handle_message_fields,parse_proto,EnumValue,ProtoEnum,Field,Message
    EnumValue:
    ProtoEnum:
    Field:
    Message:
    _parse_reserved_numbers(token)
    _to_dict(obj)
    _parse_top_level_declarations(code;ast)
    _handle_message_start(code;stack)
    _handle_enum_start(code;ast;stack)
    _handle_block_end(code;ast;stack;current_enum)
    _handle_enum_value(code;current_enum)
    _handle_message_fields(code;active)
    parse_proto(file_path)
  scripts/schema_registry.py:
    e: _connect,_diff_messages,check_compatibility,_sha256_file,_cli,IncompatibleSchemaError,SchemaVersion,SchemaRegistry
    IncompatibleSchemaError: __init__(2)  # Raised when a proposed schema change violates the active com
    SchemaVersion:
    SchemaRegistry: __init__(1),set_compatibility(2),get_compatibility(1),register(2),get_latest(1),get_by_version(2),list_schemas(0),_next_version(1),_all_versions(1),_row_to_sv(1)  # SQLite-backed proto schema registry with compatibility enfor
    _connect(db_path)
    _diff_messages(old_msgs;new_msgs)
    check_compatibility(new_ast;old_ast;mode)
    _sha256_file(path)
    _cli()
  scripts/search_index.py:
    e: SearchIndex
    SearchIndex: __init__(1),_init_db(0),upsert_entry(5),search(3)
  scripts/vector_clock.py:
    e: VectorClock
    VectorClock: increment(1),merge(1),happened_before(1),concurrent_with(1),dominates(1),to_dict(0),from_dict(2),__eq__(1),__repr__(0)  # Immutable vector clock.
  tests/conftest.py:
  tests/test_analyze_service_boundaries.py:
    e: test_analyze_service_boundaries_detects_iframe_candidates,test_build_markdown_contains_expected_sections,test_build_module_index_creates_correct_structure,test_determine_component_action
    test_analyze_service_boundaries_detects_iframe_candidates(tmp_path)
    test_build_markdown_contains_expected_sections(tmp_path)
    test_build_module_index_creates_correct_structure()
    test_determine_component_action()
  tests/test_conflict_resolver.py:
    e: _event,store,resolver,TestVectorClock,TestLWWStrategy,TestMergeNonConflicting,TestMergeConflicts,TestEventStoreMergeStreams,TestConflictResolverHelpers
    TestVectorClock: test_increment_creates_new_instance(0),test_increment_increases_counter(0),test_merge_takes_element_wise_max(0),test_merge_includes_missing_keys(0),test_happened_before_simple(0),test_concurrent_when_neither_dominates(0),test_not_concurrent_when_one_dominates(0),test_equal_clocks_not_happened_before(0),test_dominates_is_reverse_happened_before(0),test_to_dict_and_from_dict_round_trip(0),test_equality(0),test_missing_key_treated_as_zero(0)
    TestLWWStrategy: test_lww_concurrent_email_updates_picks_latest(1),test_lww_returns_all_events_sorted_by_timestamp(1),test_lww_server_preferred_on_timestamp_tie(1),test_lww_empty_branch_returns_server_stream(1),test_lww_empty_server_returns_branch_stream(1)
    TestMergeNonConflicting: test_concurrent_deactivation_and_email_change_both_apply(1),test_merge_returns_chronological_order(1),test_empty_branch_returns_server_stream(1)
    TestMergeConflicts: test_concurrent_email_updates_raises(1),test_mutually_exclusive_events_raise(1),test_deactivated_plus_reactivated_raises(1),test_conflict_error_carries_structured_data(1)
    TestEventStoreMergeStreams: test_lww_merge_via_event_store(1),test_merge_strategy_deactivation_plus_email(1),test_unknown_strategy_raises(1),test_offline_gap_detection(1),test_merge_with_no_server_events_after_fork(1)
    TestConflictResolverHelpers: test_check_exclusive_event_pairs_detects_conflicts(1),test_check_exclusive_event_pairs_no_conflict(1),test_check_field_conflicts_detects_value_conflicts(1),test_check_field_conflicts_no_conflict_different_fields(1)
    _event(event_type;payload;timestamp;aggregate_id;version)
    store(tmp_path)
    resolver()
  tests/test_delegation_plan.py:
    e: test_build_slice_blueprint_normalizes_module_name,test_build_output_row_keeps_original_fields_and_adds_slice,test_render_markdown_includes_slice_blueprints_section
    test_build_slice_blueprint_normalizes_module_name()
    test_build_output_row_keeps_original_fields_and_adds_slice()
    test_render_markdown_includes_slice_blueprints_section()
  tests/test_delegation_registry.py:
    e: test_registry_contains_existing_slices,test_search_slice_reports_static_frontend_asset,test_delegated_slice_health_marks_missing_required_assets,test_aggregate_delegation_health_returns_counts
    test_registry_contains_existing_slices()
    test_search_slice_reports_static_frontend_asset()
    test_delegated_slice_health_marks_missing_required_assets(tmp_path)
    test_aggregate_delegation_health_returns_counts()
  tests/test_detect_cqrs_pattern_clusters.py:
    e: test_detect_cqrs_pattern_clusters_identifies_data_grid_cluster
    test_detect_cqrs_pattern_clusters_identifies_data_grid_cluster(tmp_path)
  tests/test_detect_migration_candidates.py:
    e: test_analyze_repository_identifies_delegated_slice_candidate,test_get_service_candidates_filters_out_monolith_fragments,test_check_candidate_flags,test_analyze_file_content
    test_analyze_repository_identifies_delegated_slice_candidate(tmp_path)
    test_get_service_candidates_filters_out_monolith_fragments(tmp_path)
    test_check_candidate_flags(tmp_path)
    test_analyze_file_content()
  tests/test_diff_engine.py:
    e: test_identical_schemas,test_missing_in_proto,test_type_mismatch,test_repeated_mismatch,test_normalize_json_schema
    test_identical_schemas()
    test_missing_in_proto()
    test_type_mismatch()
    test_repeated_mismatch()
    test_normalize_json_schema()
  tests/test_dual_write.py:
    e: clean_dbs,test_dual_write_success,test_idempotency_prevents_duplicate
    clean_dbs()
    test_dual_write_success(clean_dbs)
    test_idempotency_prevents_duplicate(clean_dbs)
  tests/test_event_store.py:
    e: store,user_engine,TestEventStore,TestSnapshots,TestReplayEngine
    TestEventStore: test_append_returns_event(1),test_version_auto_increments(1),test_get_stream_returns_ordered_events(1),test_get_stream_from_version(1),test_optimistic_concurrency_conflict(1),test_optimistic_concurrency_success(1),test_separate_aggregates_independent(1),test_iter_all_yields_all_events(1)
    TestSnapshots: test_save_and_load_snapshot(1),test_load_snapshot_none_when_missing(1),test_snapshot_overwrite(1)
    TestReplayEngine: test_replay_creates_state(2),test_replay_applies_email_change(2),test_replay_deactivate(2),test_replay_uses_snapshot(2),test_replay_empty_stream(1),test_register_decorator(1)
    store(tmp_path)
    user_engine(store)
  tests/test_generate_migration_wave_plan.py:
    e: test_build_waves_groups_by_pattern_priority,test_estimate_effort
    test_build_waves_groups_by_pattern_priority()
    test_estimate_effort()
  tests/test_generators.py:
    e: ast,TestParseProto,TestParseProtoHelpers,TestGenerateZod,TestGeneratePydantic,TestGenerateJsonSchema,TestGenerateSql
    TestParseProto: test_package_parsed(1),test_message_count(1),test_message_names(1),test_user_fields(1),test_create_user_command_fields(1),test_field_types(1),test_field_numbers(1),test_nonexistent_file_raises(0)
    TestParseProtoHelpers: test_parse_top_level_declarations_package(0),test_parse_top_level_declarations_import(0),test_handle_message_start(0),test_handle_enum_start(0),test_handle_block_end(0),test_handle_enum_value(0)
    TestGenerateZod: test_contains_import(1),test_schema_exports_present(1),test_string_fields_use_z_string(1),test_type_exports_present(1),test_output_to_file(2)
    TestGeneratePydantic: test_pydantic_import(1),test_class_definitions(1),test_string_fields(1),test_output_is_valid_python(1)
    TestGenerateJsonSchema: test_schema_key_present(1),test_user_definition_present(1),test_user_properties(1),test_required_fields(1),test_json_serialisable(1)
    TestGenerateSql: test_create_table_users(1),test_primary_key_on_id(1),test_email_not_null(1),test_no_command_tables(1)
    ast()
  tests/test_incremental.py:
    e: TestFileHash,TestShouldRegenerate,TestCachePersistence
    TestFileHash: test_returns_hex_string(1),test_same_content_same_hash(1),test_different_content_different_hash(1)
    TestShouldRegenerate: test_new_file_should_regenerate(1),test_unchanged_file_should_not_regenerate(1),test_changed_file_should_regenerate(1)
    TestCachePersistence: test_save_and_load_cache(2),test_load_cache_returns_empty_when_missing(2)
  tests/test_legacy_registry.py:
    e: registry,test_register_and_get_latest,test_different_formats_independent
    registry()
    test_register_and_get_latest(registry)
    test_different_formats_independent(registry)
  tests/test_migrator.py:
    e: dbs,test_migration_bootstrap
    dbs()
    test_migration_bootstrap(dbs)
  tests/test_report_rendering.py:
    e: test_render_summary_markdown_contains_required_sections,test_render_excluded_candidates_markdown_formats_details,test_render_delegation_markdown_empty_rows_message,test_render_service_boundary_markdown_empty_rows_message
    test_render_summary_markdown_contains_required_sections()
    test_render_excluded_candidates_markdown_formats_details()
    test_render_delegation_markdown_empty_rows_message()
    test_render_service_boundary_markdown_empty_rows_message()
  tests/test_run_arch_migration_discovery.py:
    e: _write,_create_stub_swop_repo,_create_sample_legacy_repo,test_infer_contexts_from_service_boundaries_prefers_focused_matches,test_run_swop_pipeline_auto_detects_contexts_without_explicit_list,test_run_discovery_writes_expected_artifacts,test_run_discovery_can_run_optional_swop_pipeline,test_installed_protogate_cli_runs_discovery_pipeline
    _write(path;content)
    _create_stub_swop_repo(root)
    _create_sample_legacy_repo(repo_root)
    test_infer_contexts_from_service_boundaries_prefers_focused_matches(tmp_path)
    test_run_swop_pipeline_auto_detects_contexts_without_explicit_list(tmp_path)
    test_run_discovery_writes_expected_artifacts(tmp_path)
    test_run_discovery_can_run_optional_swop_pipeline(tmp_path)
    test_installed_protogate_cli_runs_discovery_pipeline(tmp_path)
  tests/test_schema_registry.py:
    e: _make_ast,_msg,_field,registry,TestRegistration,TestRetrieval,TestReservedParsing,TestBackwardCompatibility,TestForwardCompatibility,TestNoneCompatibility,TestRegistryEnforcement,TestViolationStructure,TestJsonSchemaMetadata
    TestRegistration: test_register_v1_returns_version_1(1),test_register_twice_increments_version(2),test_sha256_stored_correctly(1),test_ast_round_trips(1)
    TestRetrieval: test_get_latest_returns_highest_version(1),test_get_latest_none_when_empty(1),test_get_by_version(1),test_get_by_version_none_when_missing(1),test_list_schemas_returns_all(1)
    TestReservedParsing: test_v2_has_reserved_number(0),test_v2_has_reserved_name(0),test_v2_new_fields_present(0)
    TestBackwardCompatibility: test_adding_field_is_backward_compatible(0),test_removing_field_is_backward_violation(0),test_removing_field_with_reservation_is_backward_violation(0),test_type_change_is_backward_violation(0),test_number_change_is_backward_violation(0),test_number_reuse_is_backward_violation(0),test_v2_backward_compatible_with_v1_user_message(0)
    TestForwardCompatibility: test_removing_field_is_forward_compatible(0),test_type_change_is_forward_violation(0),test_number_reuse_is_forward_violation(0)
    TestNoneCompatibility: test_any_change_accepted(0)
    TestRegistryEnforcement: _make_proto(3),test_backward_violation_raises(2),test_forward_accepts_field_removal(2),test_full_transitive_checks_all_versions(2),test_none_mode_accepts_breaking_change(2),test_compatibility_mode_persisted(1),test_default_compatibility_is_backward(1)
    TestViolationStructure: test_field_removed_has_field_key(0),test_type_changed_has_old_and_new_type(0),test_number_reused_has_old_and_new_field_names(0)
    TestJsonSchemaMetadata: test_x_proto_version_embedded(0),test_no_metadata_when_not_provided(0),test_existing_tests_still_pass(0)
    _make_ast(package;messages)
    _msg(name;fields;reserved_numbers;reserved_names)
    _field(name;ftype;number;repeated)
    registry(tmp_path)
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

## Intent

Migration tool and delegation platform for extracting bounded slices from legacy systems
