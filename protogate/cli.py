#!/usr/bin/env python3
"""
protogate CLI - Migration tool and delegation platform
"""
import argparse
import sys
import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run a command and return its exit code."""
    result = subprocess.run(cmd)
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
    if args.action == "register":
        proto_file = args.proto or "contracts/user/v1/user.proto"
        cmd = ["python", "scripts/schema_registry.py", "register", proto_file]
    elif args.action == "check":
        proto_file = args.proto or "contracts/user/v1/user.proto"
        cmd = ["python", "scripts/schema_registry.py", "check", proto_file]
    elif args.action == "list":
        cmd = ["python", "scripts/schema_registry.py", "list"]
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


def cmd_clean(args: argparse.Namespace) -> int:
    """Clean generated artifacts."""
    return run_command(["make", "clean"])


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
    
    # clean command
    clean_parser = subparsers.add_parser("clean", help="Clean generated artifacts")
    clean_parser.set_defaults(func=cmd_clean)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
