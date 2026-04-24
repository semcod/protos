# Protos Integration ADR — c2004

**Status:** Draft | **Date:** 2026-04-24

## Decyzja

protos jest **TOOLCHAINEM** dla c2004 — generuje kontrakty i kod, nie wymusza runtime'u.

## Decyzje integracyjne

### 1. Gdzie .proto files?
**c2004/contracts/proto/** — lokalnie. protos jest CLI, nie magazyn.

### 2. Jak protos jest wywoływany?
**CLI tool** na maszynie dev + CI:
```yaml
tasks:
  contracts:gen:
    cmds:
      - protos generate-pydantic contracts/proto/ backend/generated/contracts/
      - protos generate-zod      contracts/proto/ frontend/src/generated/contracts/
```

### 3. Co z 50 plikami *.command.json?
**Out of scope.** Pilot (service-id) piszemy od nowa w Proto. Reszta żyje dalej.

### 4. Proto jako IDL czy wire format?
**IDL only.** Wire format to dalej JSON przez REST/WS.

## Pilot walking skeleton (5 dni)

| Dzień | Cel | Artefakt |
|-------|-----|----------|
| 0 | Weryfikacja generatorow | `identification.proto` -> Pydantic + Zod import OK |
| 1 | Pierwszy kontrakt | `c2004/contracts/proto/service_id/v1/identification.proto` |
| 2 | Backend integration | `POST /api/v3/identification/identify` uzywa wygenerowanego Pydantic |
| 3 | Frontend integration | connect-id uzywa wygenerowanego Zod do walidacji |
| 4 | CI integration | `verify-contracts` + `verify-compat` jobs |
| 5 | Diff report + decyzja | GO / STOP / ADJUST |

## Poza scope

- Legacy bridge dla 50 plikow JSON
- Wave planner (nie uzywamy w pilocie)
- Gateway / EventStore z protos (c2004 ma wlasne)
- Runtime validation middleware w CQRS bus (tydzien 2)

## Przykład end-to-end

Pliki referencyjne z dzialajacymi generatorami:
- `contracts/examples/identification/v1/identification.proto` — command, event, read model z enum i timestamp
- `generated/python/identification_v1_models.py` — wygenerowany Pydantic (import OK)
- `generated/ts/zod/identification_v1.ts` — wygenerowany Zod z `z.nativeEnum(IdentifierType)`

Przeplyw (gateway jest opcjonalny):
```
Klient (React/TS)
  -> POST /api/v3/identification/identify
    -> c2004 FastAPI router
      -> wygenerowany IdentifyUserCommand (Pydantic) — walidacja shape
      -> handler biznesowy (istniejacy kod c2004)
      -> wygenerowany UserIdentificationReadModel (Pydantic) — serializacja odpowiedzi
    -> JSON response
  -> Zod.parse() w frontend (opcjonalna dodatkowa walidacja)
```

Gateway z protos **nie jest uzywany**.

## Ryzyko

Jesli generatory okaza sie niepelne w dniu 1 (budget 2h) — od razu sciezka (c): standardowy buf ecosystem (`@bufbuild/protoc-gen-es` dla TS + `datamodel-code-generator` dla Python).
