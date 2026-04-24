from __future__ import annotations

from pathlib import Path

from protogate.cli import _resolve_proto_input_dir


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
