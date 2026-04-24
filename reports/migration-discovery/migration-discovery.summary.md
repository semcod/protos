# Migration Discovery Summary

Generated at: 2026-04-24T15:03:18.483224+00:00

- Repository root: `/home/tom/github/maskservice/c2004`
- Languages: `typescript, python, javascript, protobuf`
- Frameworks: `fastapi, vite`
- Architecture hints: `frontend-backend-repo, modular-monolith, monolith-root-backend, service-oriented`

## Counts

| Metric | Value |
| --- | ---: |
| candidate_modules | 17 |
| delegable_candidate_modules | 6 |
| excluded_candidate_modules | 11 |
| service_boundary_modules | 30 |
| cqrs_pattern_modules | 11 |
| cqrs_clusters | 10 |
| migration_waves | 5 |
| recommended_services | 4 |
| delegation_plan_modules | 6 |
| swop_contexts | 0 |
| swop_proto_files | 0 |

## Top delegable candidates

- `connect-reports-month`
- `connect-config-network`
- `connect-manager-library`
- `connect-id-user-list`
- `connect-template`

## Top raw migration candidates

- `connect-reports-month`
- `connect-config-network`
- `connect-manager-library`
- `.swop`
- `project`

## Top service candidates

- `connect-config`
- `connect-scenario`
- `connect-test`
- `connect-menu`

## Service-boundary decision reasons

- `delivery mode: decompose-before-extract`: 4
- `backend scope: activities`: 4
- `backend scope: assignments`: 4
- `backend scope: auth`: 4
- `backend scope: backups`: 4
- `coordination target: base.module.ts`: 3
- `coordination target: connect-data`: 3
- `backend groups covered: 39`: 2
- `coordination target: connect-config`: 2
- `selected as service-boundary candidate with priority 456`: 1

## Excluded candidate reasons

- `not marked as service candidate and lacks delegated slice naming`: 11
- `recommended owner is legacy-host`: 6
- `extraction target is monolith-fragment`: 6
- `technical or container-level module`: 5
- `technical or container-level path`: 4
- `hidden or temporary module name`: 1
- `top-level application should not be delegated as a slice`: 1

## Delegation decision reasons

- `service signal: has docker packaging`: 6
- `cqrs cluster size: 1`: 6
- `service signal: exposes own API routes`: 5
- `service signal: has executable entrypoint`: 5
- `readiness signal: external imports: 4`: 5
- `readiness signal: api endpoints used: 0`: 5
- `service signal: has dedicated api/app directory`: 4
- `service signal: has vertical api+ui structure`: 4
- `readiness signal: cross-module imports: 0`: 4
- `estimated effort is medium`: 3

## Top CQRS pattern candidates

- `connect-config`
- `connect-data`
- `connect-devtools`
- `connect-id`
- `connect-manager`

## Top swop contexts

- `none`

## Artifacts

| Name | Path |
| --- | --- |
| cqrs_pattern_clusters_json | `/home/tom/github/semcod/protos/reports/migration-discovery/cqrs-pattern-clusters.json` |
| cqrs_pattern_clusters_md | `/home/tom/github/semcod/protos/reports/migration-discovery/cqrs-pattern-clusters.md` |
| delegation_decisions_json | `/home/tom/github/semcod/protos/reports/migration-discovery/delegation-decisions.json` |
| delegation_decisions_md | `/home/tom/github/semcod/protos/reports/migration-discovery/delegation-decisions.md` |
| delegation_plan_json | `/home/tom/github/semcod/protos/reports/migration-discovery/delegation-plan.generated.json` |
| delegation_plan_md | `/home/tom/github/semcod/protos/reports/migration-discovery/delegation-plan.generated.md` |
| excluded_candidates_json | `/home/tom/github/semcod/protos/reports/migration-discovery/excluded-candidates.json` |
| excluded_candidates_md | `/home/tom/github/semcod/protos/reports/migration-discovery/excluded-candidates.md` |
| migration_wave_plan_json | `/home/tom/github/semcod/protos/reports/migration-discovery/migration-wave-plan.json` |
| migration_wave_plan_md | `/home/tom/github/semcod/protos/reports/migration-discovery/migration-wave-plan.md` |
| module_candidates_json | `/home/tom/github/semcod/protos/reports/migration-discovery/module-candidates.json` |
| module_candidates_md | `/home/tom/github/semcod/protos/reports/migration-discovery/module-candidates.md` |
| repository_profile_json | `/home/tom/github/semcod/protos/reports/migration-discovery/repository-profile.json` |
| repository_profile_md | `/home/tom/github/semcod/protos/reports/migration-discovery/repository-profile.md` |
| service_boundaries_json | `/home/tom/github/semcod/protos/reports/migration-discovery/service-boundaries.json` |
| service_boundaries_md | `/home/tom/github/semcod/protos/reports/migration-discovery/service-boundaries.md` |
| service_boundary_decisions_json | `/home/tom/github/semcod/protos/reports/migration-discovery/service-boundary-decisions.json` |
| service_boundary_decisions_md | `/home/tom/github/semcod/protos/reports/migration-discovery/service-boundary-decisions.md` |
