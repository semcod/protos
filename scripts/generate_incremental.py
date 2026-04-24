"""
generate_incremental.py – hash-based incremental proto → multi-target generator.

Reads a list of changed .proto files (one per line from a file or stdin),
computes SHA-256 hashes, compares them against a cache file, and only
regenerates artifacts for files whose hash has changed.

Usage:
    python scripts/generate_incremental.py [changed_files_list]

    changed_files_list  path to a text file containing one proto path per line.
                        Defaults to "changed.txt".
                        Pass "-" to read from stdin.

The hash cache is stored in ".proto_cache.json" at the repo root.

After generation the cache is updated so the next run is fast.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))

from parse_proto import parse_proto  # noqa: E402
from generate_zod import to_zod  # noqa: E402
from generate_pydantic import generate as gen_pydantic  # noqa: E402
from generate_json_schema import generate as gen_json_schema  # noqa: E402
from generate_sql import generate_sql  # noqa: E402


CACHE_PATH = ".proto_cache.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def file_hash(path: str) -> str:
    """Return the SHA-256 hex digest of the file at *path*."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_cache() -> dict[str, str]:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_cache(cache: dict[str, str]) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=2)
        fh.write("\n")


def should_regenerate(file: str, cache: dict[str, str]) -> bool:
    return cache.get(file) != file_hash(file)


# ---------------------------------------------------------------------------
# Per-proto generation
# ---------------------------------------------------------------------------


def _stem(proto_path: str) -> str:
    """Return the base name without extension, e.g. 'user' from 'user.proto'."""
    return os.path.splitext(os.path.basename(proto_path))[0]


def _write(path: str, content: str | Any, *, json_output: bool = False) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        if json_output:
            json.dump(content, fh, indent=2)
            fh.write("\n")
        else:
            fh.write(content)
    print(f"  written → {path}")


def regenerate(proto_path: str) -> None:
    print(f"[incremental] regenerating {proto_path} …")
    stem = _stem(proto_path)
    ast = parse_proto(proto_path)

    _write(f"generated/ts/zod/{stem}.ts", to_zod(ast))
    _write(f"generated/python/{stem}_models.py", gen_pydantic(ast))
    _write(f"generated/schema/{stem}.schema.json", gen_json_schema(ast), json_output=True)
    _write(f"generated/sql/{stem}.sql", generate_sql(ast))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    list_file = sys.argv[1] if len(sys.argv) > 1 else "changed.txt"

    if list_file == "-":
        lines = sys.stdin.read().splitlines()
    elif os.path.exists(list_file):
        with open(list_file, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    else:
        print(f"[incremental] file list '{list_file}' not found – nothing to do.")
        return

    proto_files = [ln.strip() for ln in lines if ln.strip().endswith(".proto")]

    if not proto_files:
        print("[incremental] no .proto files to process.")
        return

    cache = load_cache()
    changed: list[str] = []

    for pf in proto_files:
        if not os.path.exists(pf):
            print(f"[incremental] WARNING: {pf} not found, skipping.")
            continue
        if should_regenerate(pf, cache):
            regenerate(pf)
            cache[pf] = file_hash(pf)
            changed.append(pf)
        else:
            print(f"[incremental] {pf} unchanged – skipping.")

    if changed:
        save_cache(cache)
        print(f"[incremental] cache updated for {len(changed)} file(s).")
    else:
        print("[incremental] all files up-to-date.")


if __name__ == "__main__":
    main()
