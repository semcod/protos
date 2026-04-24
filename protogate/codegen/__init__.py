"""protogate codegen library - reusable generators for non-proto sources.

Modules:
    registry: build contract registry JSON/Markdown from JSON contract files
    typescript: generate TypeScript types/interfaces/enums from Python dataclasses
"""

from protogate.codegen import registry, typescript

__all__ = ["registry", "typescript"]
