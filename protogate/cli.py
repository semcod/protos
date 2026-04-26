#!/usr/bin/env python3
"""
protogate CLI - Migration tool and delegation platform
"""
import argparse
import difflib
import os
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _swop_candidate_sort_key(candidate: Path) -> tuple[float, str]:
    return (candidate.stat().st_mtime, candidate.as_posix())


def _load_module_from_path(module_name: str, script_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _resolve_proto_input_dir(input_dir: Path) -> Path:
    """Resolve an input directory containing .proto files.

    For c2004-like layouts where `contracts/` contains JSON contracts and
    protobuf definitions live in sibling `proto/`, this function auto-switches
    to the protobuf directory.
    """
    resolved = input_dir.resolve()
    if not resolved.exists():
        return resolved

    proto_files = list(resolved.rglob("*.proto"))
    if proto_files:
        return resolved

    # Common c2004 layout: contracts/ (json) and sibling proto/ (protobuf)
    sibling_proto = resolved.parent / "proto"
    if resolved.name == "contracts" and sibling_proto.is_dir() and list(sibling_proto.rglob("*.proto")):
        print(
            f"[INFO] No .proto under {resolved}; using sibling protobuf dir {sibling_proto}",
            file=sys.stderr,
        )
        return sibling_proto

    # Fallback: prefer latest swop proto output if available
    swop_candidates = [
        candidate
        for candidate in (resolved.parent / "reports").glob("**/swop/proto")
        if candidate.is_dir() and list(candidate.rglob("*.proto"))
    ]
    if swop_candidates:
        selected = max(swop_candidates, key=_swop_candidate_sort_key)
        print(
            f"[INFO] No .proto under {resolved}; using swop protobuf dir {selected}",
            file=sys.stderr,
        )
        return selected

    return resolved


def _load_parse_proto_function():
    script_path = REPO_ROOT / "scripts" / "parse_proto.py"
    mod = _load_module_from_path("_parse_proto_mod", script_path)
    return getattr(mod, "parse_proto")


def run_command(cmd: list[str], cwd: Path | None = None) -> int:
    """Run a command and return its exit code."""
    result = subprocess.run(cmd, cwd=str(cwd or REPO_ROOT))
    return result.returncode


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate code from Protobuf contracts."""
    if args.target == "all":
        cmd = ["make", "proto-all"]
    elif args.target == "proto":
        cmd = ["make", "proto"]
    elif args.target == "zod":
        cmd = ["make", "zod"]
    elif args.target == "python":
        cmd = ["make", "python"]
    elif args.target == "json":
        cmd = ["make", "json"]
    elif args.target == "sql":
        cmd = ["make", "sql"]
    elif args.target == "incremental":
        cmd = ["make", "generate-incremental"]
    else:
        print(f"Unknown target: {args.target}", file=sys.stderr)
        return 1
    
    return run_command(cmd)


def cmd_registry(args: argparse.Namespace) -> int:
    """Schema registry operations."""
    script = str(REPO_ROOT / "scripts" / "schema_registry.py")
    if args.action == "register":
        proto_file = args.proto or "contracts/user/v1/user.proto"
        cmd = [sys.executable, script, "register", proto_file]
    elif args.action == "check":
        proto_file = args.proto or "contracts/user/v1/user.proto"
        cmd = [sys.executable, script, "check", proto_file]
    elif args.action == "list":
        cmd = [sys.executable, script, "list"]
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        return 1
    
    return run_command(cmd)


def cmd_legacy(args: argparse.Namespace) -> int:
    """Legacy schema migration operations."""
    if args.action == "register":
        cmd = ["make", "legacy-register"]
    elif args.action == "diff":
        cmd = ["make", "diff-legacy"]
    elif args.action == "report":
        cmd = ["make", "legacy-report"]
    elif args.action == "list":
        cmd = ["make", "legacy-list"]
    elif args.action == "sync-check":
        cmd = ["make", "sync-check"]
    elif args.action == "bootstrap":
        cmd = ["make", "bootstrap-legacy"]
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        return 1
    
    return run_command(cmd)


def cmd_gateway(args: argparse.Namespace) -> int:
    """Run the gateway server."""
    if args.docker:
        cmd = ["make", "gateway-docker"]
    else:
        cmd = ["make", "gateway"]
    return run_command(cmd)


def cmd_ci(args: argparse.Namespace) -> int:
    """Run full CI pipeline."""
    return run_command(["make", "ci"])


def cmd_discovery(args: argparse.Namespace) -> int:
    """Run the migration discovery orchestrator."""
    script = str(REPO_ROOT / "scripts" / "legacy_bridge" / "run_arch_migration_discovery.py")
    cmd = [
        sys.executable,
        script,
        "--repo-root",
        args.repo_root,
        "--output-dir",
        args.output_dir,
        "--delegation-limit",
        str(args.delegation_limit),
    ]
    if args.config:
        cmd.extend(["--config", args.config])
    if args.top_services is not None:
        cmd.extend(["--top-services", str(args.top_services)])
    if args.swop_repo:
        cmd.extend(["--swop-repo", args.swop_repo])
    if args.swop_cqrs_root:
        cmd.extend(["--swop-cqrs-root", args.swop_cqrs_root])
    for context in args.swop_contexts:
        cmd.extend(["--swop-context", context])
    if args.stdout:
        cmd.append("--stdout")
    return run_command(cmd)


def cmd_service_boundaries(args: argparse.Namespace) -> int:
    """Run service boundary analyzer only."""
    script = str(REPO_ROOT / "scripts" / "legacy_bridge" / "analyze_service_boundaries.py")
    cmd = [
        sys.executable,
        script,
        "--repo-root",
        args.repo_root,
        "--output-dir",
        args.output_dir,
        "--basename",
        args.basename,
    ]
    if args.config:
        cmd.extend(["--config", args.config])
    if args.top_services is not None:
        cmd.extend(["--top-services", str(args.top_services)])
    if args.stdout:
        cmd.append("--stdout")
    return run_command(cmd)


def cmd_cqrs_clusters(args: argparse.Namespace) -> int:
    """Run CQRS pattern cluster analysis only."""
    script = str(REPO_ROOT / "scripts" / "legacy_bridge" / "detect_cqrs_pattern_clusters.py")
    cmd = [
        sys.executable,
        script,
        "--repo-root",
        args.repo_root,
        "--output-dir",
        args.output_dir,
        "--basename",
        args.basename,
    ]
    if args.config:
        cmd.extend(["--config", args.config])
    if args.candidates:
        cmd.extend(["--candidates", args.candidates])
    if args.stdout:
        cmd.append("--stdout")
    return run_command(cmd)


def cmd_migration_candidates(args: argparse.Namespace) -> int:
    """Run migration candidate detection and optionally emit markdown report."""
    script = str(REPO_ROOT / "scripts" / "detect_migration_candidates.py")
    cmd = [
        sys.executable,
        script,
        "--repo-root",
        args.repo_root,
        "--output",
        args.output,
        "--limit",
        str(args.limit),
    ]
    if args.services_only:
        cmd.append("--services-only")
    exit_code = run_command(cmd)
    if exit_code != 0:
        return exit_code

    if args.output == "-" or not args.with_markdown:
        return 0

    output_path = Path(args.output)
    if not output_path.exists():
        return 0

    try:
        rows = json.loads(output_path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            return 0
        run_arch_module = _load_module_from_path(
            "_run_arch_discovery_mod",
            REPO_ROOT / "scripts" / "legacy_bridge" / "run_arch_migration_discovery.py",
        )
        render_markdown = getattr(run_arch_module, "render_module_candidates_markdown")
        markdown = render_markdown(rows)
        output_md = output_path.with_suffix(".md")
        output_md.write_text(markdown, encoding="utf-8")
        print(f"[INFO] wrote {output_md}")
    except Exception as exc:
        print(f"[WARN] could not generate markdown report: {exc}", file=sys.stderr)
    return 0


def cmd_shared_ts_candidates(args: argparse.Namespace) -> int:
    """Run shared TypeScript package candidate detection."""
    script = str(REPO_ROOT / "scripts" / "legacy_bridge" / "detect_shared_ts_packages.py")
    cmd = [
        sys.executable,
        script,
        "--repo-root",
        args.repo_root,
        "--output-dir",
        args.output_dir,
        "--basename",
        args.basename,
        "--min-occurrences",
        str(args.min_occurrences),
        "--min-modules-by-name",
        str(args.min_modules_by_name),
    ]
    if args.stdout:
        cmd.append("--stdout")
    return run_command(cmd)


def cmd_clean(args: argparse.Namespace) -> int:
    """Clean generated artifacts."""
    return run_command(["make", "clean"])


def _proto_to_output_name(proto_path: Path, suffix: str) -> str:
    """Derive an output filename from a .proto path.

    E.g. contracts/user/v1/user.proto -> user_v1_models.py  (suffix="_models.py")
         contracts/user/v1/user.proto -> user_v1.ts          (suffix=".ts")
    """
    parts = proto_path.with_suffix("").parts
    # Drop leading 'contracts/' if present
    if parts[0] == "contracts":
        parts = parts[1:]
    # Build versioned basename: user_v1
    name = "_".join(parts)
    return f"{name}{suffix}"


def _batch_generate(args: argparse.Namespace, suffix: str, script_name: str, generate_func_name: str) -> int:
    """Batch-run a generator over every .proto under input_dir."""
    input_dir = _resolve_proto_input_dir(Path(args.input_dir))
    output_dir = Path(args.output_dir)
    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    # Locate the script in scripts/
    script_path = REPO_ROOT / "scripts" / script_name
    if not script_path.exists():
        print(f"Generator script not found: {script_path}", file=sys.stderr)
        return 1

    # Load the module dynamically
    try:
        mod = _load_module_from_path("_gen_mod", script_path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    generate_func = getattr(mod, generate_func_name)
    parse_proto = _load_parse_proto_function()

    proto_files = sorted(input_dir.rglob("*.proto"))
    if not proto_files:
        print(
            f"No .proto files found under {input_dir}. For c2004, try '<repo>/proto' or '<repo>/reports/.../swop/proto'.",
            file=sys.stderr,
        )
        return 1

    ok = 0
    fail = 0
    for proto_file in proto_files:
        rel = proto_file.relative_to(input_dir)
        out_name = _proto_to_output_name(rel, suffix)
        out_path = output_dir / out_name
        try:
            ast = parse_proto(str(proto_file))
            content = generate_func(ast)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")
            print(f"  generated → {out_path}")
            ok += 1
        except Exception as exc:
            print(f"  FAILED    → {proto_file}: {exc}", file=sys.stderr)
            fail += 1

    print(f"\nDone: {ok} ok, {fail} failed")
    return 1 if fail else 0


def cmd_generate_pydantic(args: argparse.Namespace) -> int:
    """Batch-generate Pydantic models from .proto contracts."""
    return _batch_generate(args, "_models.py", "generate_pydantic.py", "generate")


def cmd_generate_zod(args: argparse.Namespace) -> int:
    """Batch-generate Zod schemas from .proto contracts."""
    return _batch_generate(args, ".ts", "generate_zod.py", "to_zod")


def _batch_generate_json_schema(args: argparse.Namespace) -> int:
    """Batch-generate JSON Schema from .proto contracts."""
    import json

    input_dir = _resolve_proto_input_dir(Path(args.input_dir))
    output_dir = Path(args.output_dir)
    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    script_path = REPO_ROOT / "scripts" / "generate_json_schema.py"
    if not script_path.exists():
        print(f"Generator script not found: {script_path}", file=sys.stderr)
        return 1

    try:
        mod = _load_module_from_path("_gen_json_mod", script_path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    generate_func = getattr(mod, "generate")
    parse_proto = _load_parse_proto_function()

    proto_files = sorted(input_dir.rglob("*.proto"))
    if not proto_files:
        print(
            f"No .proto files found under {input_dir}. For c2004, try '<repo>/proto' or '<repo>/reports/.../swop/proto'.",
            file=sys.stderr,
        )
        return 1

    ok = 0
    fail = 0
    for proto_file in proto_files:
        rel = proto_file.relative_to(input_dir)
        out_name = _proto_to_output_name(rel, ".schema.json")
        out_path = output_dir / out_name
        try:
            ast = parse_proto(str(proto_file))
            content = generate_func(ast)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(content, fh, indent=2)
                fh.write("\n")
            print(f"  generated → {out_path}")
            ok += 1
        except Exception as exc:
            print(f"  FAILED    → {proto_file}: {exc}", file=sys.stderr)
            fail += 1

    print(f"\nDone: {ok} ok, {fail} failed")
    return 1 if fail else 0


def cmd_generate_json_schema(args: argparse.Namespace) -> int:
    """Batch-generate JSON Schema definitions from .proto contracts."""
    return _batch_generate_json_schema(args)


def cmd_generate_sql(args: argparse.Namespace) -> int:
    """Batch-generate SQL DDL from .proto contracts."""
    return _batch_generate(args, ".sql", "generate_sql.py", "generate_sql")


def cmd_codegen_json_schema(args: argparse.Namespace) -> int:
    """Generate JSON Schema files from Pydantic models.

    Replaces ``c2004/scripts/generate_json_schemas.py`` per ADR-010 Sprint C.
    """
    from protogate.codegen import pydantic_json_schema as _pjs

    if not args.module:
        print("At least one --module is required", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir).resolve()
    project_root = Path(args.project_root).resolve() if args.project_root else None

    class_filters: dict[str, list[str]] = {}
    for raw in args.include or []:
        if "=" not in raw:
            print(f"--include expects MODULE=Class1,Class2 (got: {raw})", file=sys.stderr)
            return 1
        mod, classes = raw.split("=", 1)
        class_filters[mod] = [c.strip() for c in classes.split(",") if c.strip()]

    return _pjs.run_cli(
        modules=args.module,
        output_dir=output_dir,
        class_filters=class_filters,
        project_root=project_root,
        verbose=not args.quiet,
    )


def cmd_codegen_zod(args: argparse.Namespace) -> int:
    """Generate Zod TypeScript validators from JSON Schema files.

    Replaces ``c2004/scripts/generate_zod_validators.mjs`` per ADR-010 Sprint C.
    """
    from protogate.codegen import jsonschema_zod as _jz

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1
    return _jz.run_cli(input_dir=input_dir, output_dir=output_dir, verbose=not args.quiet)


def cmd_codegen_registry(args: argparse.Namespace) -> int:
    """Generate contract registry (registry.json + REGISTRY.md) from JSON contracts.

    Replaces the legacy ``c2004/scripts/generate-registry.py`` per ADR-010
    Sprint B. Input directory is scanned for ``*.command.json``,
    ``*.query.json`` and ``*.event.json`` files.
    """
    from protogate.codegen import registry as _reg

    contracts_dir = Path(args.contracts_dir).resolve()
    if not contracts_dir.exists():
        print(f"Contracts directory not found: {contracts_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir).resolve() if args.output_dir else contracts_dir
    layers_root = Path(args.layers_root).resolve() if args.layers_root else None

    return _reg.run_cli(
        contracts_dir=contracts_dir,
        output_dir=output_dir,
        layers_root=layers_root,
        check_only=args.check,
        cross_check_pydantic=getattr(args, "cross_check_pydantic", False),
        fix_safe=getattr(args, "fix_safe", False),
        auto_expand_output=getattr(args, "auto_expand_output", False),
        verbose=not args.quiet,
    )


def _configure_codegen_ts_parser(parser: argparse.ArgumentParser) -> None:
    """Configure shared arguments for TypeScript-from-Python codegen parsers."""
    parser.add_argument(
        "--script",
        required=True,
        help="Python script path exposing build_output() -> str",
    )
    parser.add_argument(
        "--output",
        action="append",
        required=True,
        help="Output TypeScript file path (repeatable for multi-target write)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check-only mode; returns non-zero if output drift is detected",
    )
    parser.add_argument(
        "--profile",
        choices=["strict", "compat"],
        default="compat",
        help="Generation profile passed to wrapper script (default: compat)",
    )
    parser.add_argument(
        "--show-diff",
        action="store_true",
        help="When used with --check, print unified diff (truncated)",
    )
    parser.add_argument(
        "--write-report",
        help="Write change report files: <path>.json and <path>.md",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success output",
    )
    parser.set_defaults(func=cmd_codegen_ts_from_python)


def cmd_codegen_ts_from_python(args: argparse.Namespace) -> int:
    """Generate TypeScript output from a Python wrapper script.

    The wrapper script must expose a callable ``build_output() -> str`` that
    returns full TypeScript file content.
    """
    script_path = Path(args.script).resolve()
    if not script_path.exists():
        print(f"Generator script not found: {script_path}", file=sys.stderr)
        return 1

    raw_outputs = getattr(args, "output", None) or []
    output_paths = [Path(raw).resolve() for raw in raw_outputs]
    if not output_paths:
        print("At least one --output is required", file=sys.stderr)
        return 1

    try:
        mod = _load_module_from_path("_ts_from_python_codegen", script_path)
    except Exception as exc:
        print(f"Failed to load generator script {script_path}: {exc}", file=sys.stderr)
        return 1

    build_output = getattr(mod, "build_output", None)
    if not callable(build_output):
        print(
            f"Generator script {script_path} must define callable build_output()",
            file=sys.stderr,
        )
        return 1

    profile = getattr(args, "profile", "compat")
    previous_profile = os.environ.get("PROTOGATE_TS_PROFILE")
    os.environ["PROTOGATE_TS_PROFILE"] = profile

    try:
        try:
            generated = build_output(profile=profile)
        except TypeError as exc:
            # Backward-compatible fallback for legacy wrapper scripts exposing build_output()
            # without a profile kwarg.
            message = str(exc)
            if "profile" in message or "unexpected keyword" in message:
                generated = build_output()
            else:
                raise
    except Exception as exc:
        print(f"build_output() failed in {script_path}: {exc}", file=sys.stderr)
        return 1
    finally:
        if previous_profile is None:
            os.environ.pop("PROTOGATE_TS_PROFILE", None)
        else:
            os.environ["PROTOGATE_TS_PROFILE"] = previous_profile

    if not isinstance(generated, str):
        print("build_output() must return str", file=sys.stderr)
        return 1

    report_rows: list[dict[str, object]] = []
    changed = 0
    added = 0
    unchanged = 0

    for output_path in output_paths:
        exists = output_path.exists()
        current = output_path.read_text(encoding="utf-8") if exists else ""
        status = "unchanged"
        if not exists:
            status = "added"
            added += 1
        elif current != generated:
            status = "changed"
            changed += 1
        else:
            unchanged += 1

        diff_lines = list(
            difflib.unified_diff(
                current.splitlines(),
                generated.splitlines(),
                fromfile=f"current:{output_path}",
                tofile=f"generated:{output_path}",
                lineterm="",
            )
        )
        added_lines = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
        removed_lines = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

        report_rows.append(
            {
                "path": str(output_path),
                "status": status,
                "line_additions": added_lines,
                "line_removals": removed_lines,
            }
        )

    report_target = getattr(args, "write_report", None)
    if report_target:
        report_base = Path(report_target).resolve()
        report_base.parent.mkdir(parents=True, exist_ok=True)

        report_json_path = report_base.with_suffix(".json")
        report_md_path = report_base.with_suffix(".md")

        summary = {
            "script": str(script_path),
            "profile": profile,
            "check_mode": bool(args.check),
            "totals": {
                "targets": len(output_paths),
                "changed": changed,
                "added": added,
                "unchanged": unchanged,
            },
            "rows": report_rows,
        }

        report_json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

        md_lines = [
            "# TS Codegen Change Report",
            "",
            f"- Script: {script_path}",
            f"- Profile: {profile}",
            f"- Check mode: {args.check}",
            f"- Targets: {len(output_paths)}",
            f"- Added: {added}",
            f"- Changed: {changed}",
            f"- Unchanged: {unchanged}",
            "",
            "| Target | Status | +Lines | -Lines |",
            "|---|---:|---:|---:|",
        ]
        for row in report_rows:
            md_lines.append(
                f"| {row['path']} | {row['status']} | {row['line_additions']} | {row['line_removals']} |"
            )
        report_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

        if not args.quiet:
            print(f"report -> {report_json_path}")
            print(f"report -> {report_md_path}")

    if args.check:
        drift_found = False
        for output_path in output_paths:
            if not output_path.exists():
                print(f"DRIFT: missing output file {output_path}", file=sys.stderr)
                drift_found = True
                continue

            existing = output_path.read_text(encoding="utf-8")
            if existing == generated:
                if not args.quiet:
                    print(f"OK: {output_path} is up-to-date")
                continue

            print(f"DRIFT: {output_path} is out-of-date", file=sys.stderr)
            drift_found = True
            if getattr(args, "show_diff", False):
                diff = difflib.unified_diff(
                    existing.splitlines(),
                    generated.splitlines(),
                    fromfile=f"current:{output_path}",
                    tofile=f"generated:{output_path}",
                    lineterm="",
                )
                for line in list(diff)[:200]:
                    print(line, file=sys.stderr)

        return 1 if drift_found else 0

    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(generated, encoding="utf-8")
        if not args.quiet:
            print(f"generated -> {output_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="protogate",
        description="Migration tool and delegation platform for extracting bounded slices from legacy systems"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate code from Protobuf contracts")
    gen_parser.add_argument(
        "target",
        choices=["all", "proto", "zod", "python", "json", "sql", "incremental"],
        help="Generation target"
    )
    gen_parser.set_defaults(func=cmd_generate)
    
    # registry command
    reg_parser = subparsers.add_parser("registry", help="Schema registry operations")
    reg_parser.add_argument(
        "action",
        choices=["register", "check", "list"],
        help="Registry action"
    )
    reg_parser.add_argument("--proto", help="Proto file path (default: contracts/user/v1/user.proto)")
    reg_parser.set_defaults(func=cmd_registry)
    
    # legacy command
    legacy_parser = subparsers.add_parser("legacy", help="Legacy schema migration operations")
    legacy_parser.add_argument(
        "action",
        choices=["register", "diff", "report", "list", "sync-check", "bootstrap"],
        help="Legacy action"
    )
    legacy_parser.set_defaults(func=cmd_legacy)
    
    # gateway command
    gateway_parser = subparsers.add_parser("gateway", help="Run the gateway server")
    gateway_parser.add_argument("--docker", action="store_true", help="Run via Docker")
    gateway_parser.set_defaults(func=cmd_gateway)
    
    # ci command
    ci_parser = subparsers.add_parser("ci", help="Run full CI pipeline")
    ci_parser.set_defaults(func=cmd_ci)

    # discovery command
    discovery_parser = subparsers.add_parser("discovery", help="Run the migration discovery orchestrator")
    discovery_parser.add_argument("--repo-root", required=True, help="Path to the repository to analyze")
    discovery_parser.add_argument("--config", help="Optional config path for service-boundary analysis")
    discovery_parser.add_argument("--output-dir", default="reports/migration-discovery", help="Output directory, relative to repo root if not absolute")
    discovery_parser.add_argument("--top-services", type=int, help="Number of top service candidates to recommend")
    discovery_parser.add_argument("--delegation-limit", type=int, default=8, help="Number of top module candidates to include in delegation outputs")
    discovery_parser.add_argument("--swop-repo", help="Optional path to the swop repository")
    discovery_parser.add_argument("--swop-cqrs-root", default="backend/app/cqrs", help="CQRS root inside the analyzed repository for swop scans")
    discovery_parser.add_argument("--swop-context", action="append", dest="swop_contexts", default=[], help="Explicit CQRS context for swop; can be passed multiple times")
    discovery_parser.add_argument("--stdout", action="store_true", help="Print discovery summary JSON to stdout")
    discovery_parser.set_defaults(func=cmd_discovery)

    # service-boundaries command
    sb_parser = subparsers.add_parser("service-boundaries", help="Run service boundary analyzer")
    sb_parser.add_argument("--repo-root", required=True, help="Path to repository root")
    sb_parser.add_argument("--config", help="Optional config path")
    sb_parser.add_argument("--output-dir", default="reports/service-boundaries", help="Output directory, relative to repo root if not absolute")
    sb_parser.add_argument("--basename", default="service-boundaries", help="Basename for output files")
    sb_parser.add_argument("--top-services", type=int, help="Number of top service candidates")
    sb_parser.add_argument("--stdout", action="store_true", help="Print JSON payload to stdout")
    sb_parser.set_defaults(func=cmd_service_boundaries)

    # cqrs-clusters command
    cqrs_parser = subparsers.add_parser("cqrs-clusters", help="Run CQRS pattern cluster analysis")
    cqrs_parser.add_argument("--repo-root", required=True, help="Path to repository root")
    cqrs_parser.add_argument("--config", help="Optional config path")
    cqrs_parser.add_argument("--output-dir", default="reports/cqrs-pattern-clusters", help="Output directory, relative to repo root if not absolute")
    cqrs_parser.add_argument("--basename", default="cqrs-pattern-clusters", help="Basename for output files")
    cqrs_parser.add_argument("--candidates", help="Optional path to module-candidates.json")
    cqrs_parser.add_argument("--stdout", action="store_true", help="Print JSON payload to stdout")
    cqrs_parser.set_defaults(func=cmd_cqrs_clusters)

    # migration-candidates command
    mc_parser = subparsers.add_parser("migration-candidates", help="Run migration candidate detection")
    mc_parser.add_argument("--repo-root", required=True, help="Path to repository root")
    mc_parser.add_argument("--output", default="-", help="Output JSON path or '-' for stdout")
    mc_parser.add_argument("--limit", type=int, default=20, help="Limit number of candidates")
    mc_parser.add_argument("--services-only", action="store_true", help="Only return service candidates")
    mc_parser.add_argument("--with-markdown", action="store_true", default=True, help="Also write markdown report when output is a file")
    mc_parser.set_defaults(func=cmd_migration_candidates)

    # shared-ts-candidates command
    sts_parser = subparsers.add_parser("shared-ts-candidates", help="Detect shared TypeScript package candidates")
    sts_parser.add_argument("--repo-root", required=True, help="Path to repository root")
    sts_parser.add_argument("--output-dir", default="migration", help="Output directory, relative to repo root if not absolute")
    sts_parser.add_argument("--basename", default="shared-ts-candidates", help="Basename for output files")
    sts_parser.add_argument("--min-occurrences", type=int, default=2, help="Minimum duplicate count")
    sts_parser.add_argument("--min-modules-by-name", type=int, default=3, help="Minimum module count for filename-pattern candidates")
    sts_parser.add_argument("--stdout", action="store_true", help="Print JSON payload to stdout")
    sts_parser.set_defaults(func=cmd_shared_ts_candidates)

    # clean command
    clean_parser = subparsers.add_parser("clean", help="Clean generated artifacts")
    clean_parser.set_defaults(func=cmd_clean)

    # generate-pydantic command
    pydantic_parser = subparsers.add_parser("generate-pydantic", help="Batch-generate Pydantic models from .proto contracts")
    pydantic_parser.add_argument("input_dir", help="Directory containing .proto files")
    pydantic_parser.add_argument("output_dir", help="Output directory for generated .py files")
    pydantic_parser.set_defaults(func=cmd_generate_pydantic)

    # generate-zod command
    zod_parser = subparsers.add_parser("generate-zod", help="Batch-generate Zod schemas from .proto contracts")
    zod_parser.add_argument("input_dir", help="Directory containing .proto files")
    zod_parser.add_argument("output_dir", help="Output directory for generated .ts files")
    zod_parser.set_defaults(func=cmd_generate_zod)

    # generate-json-schema command
    json_parser = subparsers.add_parser("generate-json-schema", help="Batch-generate JSON Schema from .proto contracts")
    json_parser.add_argument("input_dir", help="Directory containing .proto files")
    json_parser.add_argument("output_dir", help="Output directory for generated .schema.json files")
    json_parser.set_defaults(func=cmd_generate_json_schema)

    # generate-sql command
    sql_parser = subparsers.add_parser("generate-sql", help="Batch-generate SQL DDL from .proto contracts")
    sql_parser.add_argument("input_dir", help="Directory containing .proto files")
    sql_parser.add_argument("output_dir", help="Output directory for generated .sql files")
    sql_parser.set_defaults(func=cmd_generate_sql)

    # codegen (meta-command) — non-proto code generators (ADR-010 Sprint B)
    codegen_parser = subparsers.add_parser(
        "codegen",
        help="Non-proto code generators (registry, ts-from-python, ...)",
    )
    codegen_sub = codegen_parser.add_subparsers(dest="codegen_command", required=True)

    # codegen registry
    codegen_registry = codegen_sub.add_parser(
        "registry",
        help="Generate contract registry (registry.json + REGISTRY.md) from JSON contracts",
    )
    codegen_registry.add_argument(
        "contracts_dir",
        help="Directory containing *.command.json, *.query.json, *.event.json files",
    )
    codegen_registry.add_argument(
        "--output-dir",
        help="Output directory (default: same as contracts_dir)",
    )
    codegen_registry.add_argument(
        "--layers-root",
        help="Repository root used to validate 'layers' paths (default: contracts_dir parent)",
    )
    codegen_registry.add_argument(
        "--check",
        action="store_true",
        help="Validate only, do not write output files",
    )
    codegen_registry.add_argument(
        "--cross-check-pydantic",
        action="store_true",
        help=(
            "Cross-check every contract's enum values against Literal[...] "
            "annotations in layers.python. Catches drift between contract JSON "
            "and Pydantic models (ADR-012 Wave 2 regression)."
        ),
    )
    codegen_registry.add_argument(
        "--fix-safe",
        action="store_true",
        help=(
            "Auto-apply safe warning-level drift fixes to contract JSON on disk "
            "(remove enum values Pydantic never emits). Requires "
            "--cross-check-pydantic. Never modifies Python source."
        ),
    )
    codegen_registry.add_argument(
        "--auto-expand-output",
        action="store_true",
        help=(
            "With --fix-safe: also expand output/payload contract enums to "
            "cover values Pydantic Literal emits (opt-in; resolves Wave 2 "
            "regression class automatically but may bless a server-side bug)."
        ),
    )
    codegen_registry.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-contract progress output",
    )
    codegen_registry.set_defaults(func=cmd_codegen_registry)

    # codegen json-schema (from Pydantic models)
    codegen_json = codegen_sub.add_parser(
        "json-schema",
        help="Generate JSON Schema files from Pydantic models (replaces generate_json_schemas.py)",
    )
    codegen_json.add_argument(
        "--module",
        action="append",
        default=[],
        help="Dotted Python module containing Pydantic BaseModel subclasses (repeatable)",
    )
    codegen_json.add_argument(
        "--include",
        action="append",
        default=[],
        help="Pin specific classes per module: MODULE=Class1,Class2 (repeatable)",
    )
    codegen_json.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write *.schema.json and _index.json",
    )
    codegen_json.add_argument(
        "--project-root",
        help="Project root prepended to sys.path for module import resolution",
    )
    codegen_json.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file progress output",
    )
    codegen_json.set_defaults(func=cmd_codegen_json_schema)

    # codegen zod (from JSON Schema files)
    codegen_zod = codegen_sub.add_parser(
        "zod",
        help="Generate Zod TypeScript validators from JSON Schema (replaces generate_zod_validators.mjs)",
    )
    codegen_zod.add_argument(
        "input_dir",
        help="Directory containing *.schema.json files",
    )
    codegen_zod.add_argument(
        "output_dir",
        help="Output directory for generated *.validator.ts + index.ts",
    )
    codegen_zod.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file progress output",
    )
    codegen_zod.set_defaults(func=cmd_codegen_zod)

    # codegen ts-from-python (from wrapper script exposing build_output())
    codegen_ts = codegen_sub.add_parser(
        "ts-from-python",
        help="Generate TypeScript from Python wrapper script (requires build_output())",
    )
    _configure_codegen_ts_parser(codegen_ts)

    # codegen ts (namespace alias for ts-from-python)
    codegen_ts_alias = codegen_sub.add_parser(
        "ts",
        help="Alias for 'codegen ts-from-python'",
    )
    _configure_codegen_ts_parser(codegen_ts_alias)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
