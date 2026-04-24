"""JSON Schema generator from Pydantic models.

Loads one or more Python modules containing Pydantic ``BaseModel`` subclasses
and emits one ``{kebab-case}.schema.json`` file per class, plus an
``_index.json`` barrel.

Ported from ``c2004/scripts/generate_json_schemas.py`` (ADR-010 Sprint C).
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


def camel_to_kebab(name: str) -> str:
    """Convert ``CamelCase``/``camelCase`` to ``kebab-case``."""
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"-\1", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", s)
    return s.lower()


def discover_pydantic_models(
    module_name: str,
    *,
    class_filter: list[str] | None = None,
) -> dict[str, type]:
    """Import a module and return Pydantic ``BaseModel`` subclasses.

    Parameters
    ----------
    module_name:
        Dotted module path, e.g. ``api.schemas.scenarios``.
    class_filter:
        Optional list of class names to include. If ``None`` or empty, all
        ``BaseModel`` subclasses defined *in* the module (not imported) are
        returned.
    """
    try:
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError(
            "pydantic is not installed in this environment; required for json-schema codegen"
        ) from exc

    module = importlib.import_module(module_name)
    found: dict[str, type] = {}

    if class_filter:
        for cls_name in class_filter:
            cls = getattr(module, cls_name, None)
            if cls is not None and hasattr(cls, "model_json_schema"):
                found[cls_name] = cls
        return found

    for attr_name in dir(module):
        if attr_name.startswith("_"):
            continue
        obj = getattr(module, attr_name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseModel)
            and obj is not BaseModel
            and obj.__module__ == module.__name__
        ):
            found[attr_name] = obj
    return found


def generate_schema(model_class: Any) -> dict:
    """Generate JSON Schema (draft 2020-12) from a Pydantic model class."""
    return model_class.model_json_schema(mode="serialization")


def run_cli(
    modules: Iterable[str],
    output_dir: Path,
    *,
    class_filters: dict[str, list[str]] | None = None,
    project_root: Path | None = None,
    verbose: bool = True,
) -> int:
    """Generate JSON Schema files for the given modules.

    Parameters
    ----------
    modules:
        Iterable of dotted module paths (e.g. ``["api.schemas.scenarios"]``).
    output_dir:
        Target directory. Created if missing.
    class_filters:
        Optional mapping ``{module_name: [ClassName, ...]}`` to restrict which
        classes are emitted per module.
    project_root:
        If given, prepended to ``sys.path`` so module imports resolve.
    """
    if project_root is not None and str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    output_dir.mkdir(parents=True, exist_ok=True)
    class_filters = class_filters or {}

    if verbose:
        print(f"🔧 Generating JSON Schemas → {output_dir}/")
        print()

    models: dict[str, Any] = {}
    for module_name in modules:
        try:
            discovered = discover_pydantic_models(
                module_name,
                class_filter=class_filters.get(module_name),
            )
        except ImportError as exc:
            if verbose:
                print(f"  ⚠️  Skip {module_name}: {exc}")
            continue
        models.update(discovered)

    if not models:
        print("❌ No Pydantic models found", file=sys.stderr)
        return 1

    generated: list[str] = []
    for name, model_cls in sorted(models.items()):
        schema = generate_schema(model_cls)
        filename = f"{camel_to_kebab(name)}.schema.json"
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(schema, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        generated.append(filename)
        if verbose:
            print(f"  ✅ {name} → {filename}")

    index = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "description": "Schema index — generated from Pydantic models",
        "schemas": {
            name: f"./{camel_to_kebab(name)}.schema.json"
            for name in sorted(models.keys())
        },
    }
    index_path = output_dir / "_index.json"
    with open(index_path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    if verbose:
        print()
        print(f"📦 Generated {len(generated)} schemas + _index.json")
        print(f"📁 Output: {output_dir}/")
    return 0


__all__ = [
    "camel_to_kebab",
    "discover_pydantic_models",
    "generate_schema",
    "run_cli",
]
