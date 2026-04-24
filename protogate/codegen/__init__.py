"""protogate codegen library - reusable generators for non-proto sources.

Modules:
    registry:             build contract registry JSON/Markdown from JSON contract files
    typescript:           generate TypeScript types/interfaces/enums from Python dataclasses
    pydantic_json_schema: generate JSON Schema (draft 2020-12) from Pydantic models
    jsonschema_zod:       generate Zod TypeScript validators from JSON Schema
"""

from protogate.codegen import registry, typescript, pydantic_json_schema, jsonschema_zod

__all__ = ["registry", "typescript", "pydantic_json_schema", "jsonschema_zod"]
