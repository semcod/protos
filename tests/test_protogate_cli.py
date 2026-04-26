from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from protogate.cli import _resolve_proto_input_dir, cmd_codegen_ts_from_python


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_resolve_proto_input_dir_keeps_path_with_proto(tmp_path: Path) -> None:
    proto_root = tmp_path / "proto"
    _write(proto_root / "menu" / "v1" / "menu.proto", 'syntax = "proto3";\n')

    resolved = _resolve_proto_input_dir(proto_root)

    assert resolved == proto_root.resolve()


def test_resolve_proto_input_dir_switches_contracts_to_sibling_proto(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts"
    contracts_root.mkdir(parents=True)
    _write(contracts_root / "CreateUser.command.json", "{}\n")

    proto_root = tmp_path / "proto"
    _write(proto_root / "user" / "v1" / "user.proto", 'syntax = "proto3";\n')

    resolved = _resolve_proto_input_dir(contracts_root)

    assert resolved == proto_root.resolve()


def test_resolve_proto_input_dir_falls_back_to_swop_proto(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts"
    contracts_root.mkdir(parents=True)
    _write(contracts_root / "CreateUser.command.json", "{}\n")

    swop_proto_root = tmp_path / "reports" / "migration-discovery" / "swop" / "proto"
    _write(swop_proto_root / "events" / "v1" / "events.proto", 'syntax = "proto3";\n')

    resolved = _resolve_proto_input_dir(contracts_root)

    assert resolved == swop_proto_root.resolve()


def test_resolve_proto_input_dir_prefers_latest_swop_proto(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts"
    contracts_root.mkdir(parents=True)
    _write(contracts_root / "CreateUser.command.json", "{}\n")

    older = tmp_path / "reports" / "2026-01-01" / "swop" / "proto"
    newer = tmp_path / "reports" / "2026-02-01" / "swop" / "proto"
    _write(older / "events" / "v1" / "events.proto", 'syntax = "proto3";\n')
    _write(newer / "events" / "v1" / "events.proto", 'syntax = "proto3";\n')

    # Force deterministic ordering independent from filesystem timing defaults.
    os.utime(older, (1_700_000_000, 1_700_000_000))
    os.utime(newer, (1_800_000_000, 1_800_000_000))

    resolved = _resolve_proto_input_dir(contracts_root)

    assert resolved == newer.resolve()


def test_resolve_proto_input_dir_prefers_deterministic_candidate_on_equal_mtime(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts"
    contracts_root.mkdir(parents=True)
    _write(contracts_root / "CreateUser.command.json", "{}\n")

    left = tmp_path / "reports" / "alpha" / "swop" / "proto"
    right = tmp_path / "reports" / "beta" / "swop" / "proto"
    _write(left / "events" / "v1" / "events.proto", 'syntax = "proto3";\n')
    _write(right / "events" / "v1" / "events.proto", 'syntax = "proto3";\n')

    equal_time = (1_900_000_000, 1_900_000_000)
    os.utime(left, equal_time)
    os.utime(right, equal_time)

    resolved = _resolve_proto_input_dir(contracts_root)

    assert resolved == right.resolve()


def test_codegen_ts_from_python_writes_output(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out = tmp_path / "generated.ts"
    _write(
        script,
        "def build_output():\n"
        "    return 'export interface A { id: string; }\\n'\n",
    )

    args = argparse.Namespace(
        script=str(script),
        output=[str(out)],
        check=False,
        show_diff=False,
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 0
    assert out.exists()
    assert "export interface A" in out.read_text(encoding="utf-8")


def test_codegen_ts_from_python_check_detects_drift(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out = tmp_path / "generated.ts"
    _write(
        script,
        "def build_output():\n"
        "    return 'export interface A { id: string; }\\n'\n",
    )
    _write(out, "export interface B { id: string; }\n")

    args = argparse.Namespace(
        script=str(script),
        output=[str(out)],
        check=True,
        show_diff=False,
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 1


def test_codegen_ts_from_python_check_passes_when_synced(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out = tmp_path / "generated.ts"
    content = "export interface A { id: string; }\n"
    _write(
        script,
        "def build_output():\n"
        f"    return {content!r}\n",
    )
    _write(out, content)

    args = argparse.Namespace(
        script=str(script),
        output=[str(out)],
        check=True,
        show_diff=False,
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 0


def test_codegen_ts_from_python_writes_multiple_outputs(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out_a = tmp_path / "a" / "generated.ts"
    out_b = tmp_path / "b" / "generated.ts"
    content = "export interface Multi { id: string; }\n"
    _write(
        script,
        "def build_output():\n"
        f"    return {content!r}\n",
    )

    args = argparse.Namespace(
        script=str(script),
        output=[str(out_a), str(out_b)],
        check=False,
        show_diff=False,
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 0
    assert out_a.read_text(encoding="utf-8") == content
    assert out_b.read_text(encoding="utf-8") == content


def test_codegen_ts_from_python_check_detects_drift_for_any_output(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out_a = tmp_path / "a" / "generated.ts"
    out_b = tmp_path / "b" / "generated.ts"
    content = "export interface Multi { id: string; }\n"
    _write(
        script,
        "def build_output():\n"
        f"    return {content!r}\n",
    )
    _write(out_a, content)
    _write(out_b, "export interface Drift { id: string; }\n")

    args = argparse.Namespace(
        script=str(script),
        output=[str(out_a), str(out_b)],
        check=True,
        show_diff=False,
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 1


def test_codegen_ts_from_python_check_passes_for_all_outputs_in_sync(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out_a = tmp_path / "a" / "generated.ts"
    out_b = tmp_path / "b" / "generated.ts"
    content = "export interface Multi { id: string; }\n"
    _write(
        script,
        "def build_output():\n"
        f"    return {content!r}\n",
    )
    _write(out_a, content)
    _write(out_b, content)

    args = argparse.Namespace(
        script=str(script),
        output=[str(out_a), str(out_b)],
        check=True,
        show_diff=False,
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 0


def test_codegen_ts_from_python_passes_profile_kwarg(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out = tmp_path / "generated.ts"
    _write(
        script,
        "def build_output(profile='compat'):\n"
        "    return f'// profile:{profile}\\n'\n",
    )

    args = argparse.Namespace(
        script=str(script),
        output=[str(out)],
        check=False,
        profile="strict",
        show_diff=False,
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 0
    assert out.read_text(encoding="utf-8") == "// profile:strict\n"


def test_codegen_ts_from_python_profile_env_fallback_for_legacy_wrapper(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out = tmp_path / "generated.ts"
    _write(
        script,
        "import os\n"
        "def build_output():\n"
        "    return f'// env-profile:{os.getenv(\"PROTOGATE_TS_PROFILE\", \"compat\")}\\n'\n",
    )

    args = argparse.Namespace(
        script=str(script),
        output=[str(out)],
        check=False,
        profile="strict",
        show_diff=False,
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 0
    assert out.read_text(encoding="utf-8") == "// env-profile:strict\n"


def test_codegen_ts_from_python_write_report_generates_json_and_md(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out = tmp_path / "generated.ts"
    report_base = tmp_path / "reports" / "ts-codegen-report"
    content = "export interface Reported { id: string; }\n"
    _write(
        script,
        "def build_output():\n"
        f"    return {content!r}\n",
    )

    args = argparse.Namespace(
        script=str(script),
        output=[str(out)],
        check=False,
        profile="compat",
        show_diff=False,
        write_report=str(report_base),
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 0

    report_json = report_base.with_suffix(".json")
    report_md = report_base.with_suffix(".md")
    assert report_json.exists()
    assert report_md.exists()

    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["totals"]["targets"] == 1
    assert payload["totals"]["added"] == 1
    assert payload["totals"]["changed"] == 0
    assert payload["totals"]["unchanged"] == 0
    assert payload["rows"][0]["status"] == "added"
    assert "TS Codegen Change Report" in report_md.read_text(encoding="utf-8")


def test_codegen_ts_from_python_write_report_tracks_changed_and_unchanged(tmp_path: Path) -> None:
    script = tmp_path / "gen.py"
    out_a = tmp_path / "a" / "generated.ts"
    out_b = tmp_path / "b" / "generated.ts"
    report_base = tmp_path / "reports" / "multi"
    target_content = "export interface R { id: string; }\n"
    _write(
        script,
        "def build_output():\n"
        f"    return {target_content!r}\n",
    )
    _write(out_a, target_content)
    _write(out_b, "export interface Old { id: string; }\n")

    args = argparse.Namespace(
        script=str(script),
        output=[str(out_a), str(out_b)],
        check=True,
        profile="compat",
        show_diff=False,
        write_report=str(report_base),
        quiet=True,
    )

    rc = cmd_codegen_ts_from_python(args)
    assert rc == 1

    payload = json.loads(report_base.with_suffix(".json").read_text(encoding="utf-8"))
    assert payload["totals"]["targets"] == 2
    assert payload["totals"]["changed"] == 1
    assert payload["totals"]["unchanged"] == 1
