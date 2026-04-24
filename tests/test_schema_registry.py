"""
tests/test_schema_registry.py – tests for the Schema Registry + compatibility engine.

Run with:
    python -m pytest tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"
sys.path.insert(0, str(SCRIPTS_DIR))

from schema_registry import (  # noqa: E402
    SchemaRegistry,
    IncompatibleSchemaError,
    check_compatibility,
    BACKWARD,
    FORWARD,
    FULL_TRANSITIVE,
    NONE,
)
from parse_proto import parse_proto  # noqa: E402

V1_PROTO = CONTRACTS_DIR / "user" / "v1" / "user.proto"
V2_PROTO = CONTRACTS_DIR / "user" / "v2" / "user.proto"


# ---------------------------------------------------------------------------
# Helpers to build minimal ASTs in tests without touching disk
# ---------------------------------------------------------------------------


def _make_ast(package: str, messages: list[dict]) -> dict:
    """Build a minimal AST dict for use in check_compatibility tests."""
    return {"package": package, "messages": messages}


def _msg(name: str, fields: list[dict], reserved_numbers=None, reserved_names=None) -> dict:
    return {
        "name": name,
        "fields": fields,
        "reserved_numbers": reserved_numbers or [],
        "reserved_names": reserved_names or [],
    }


def _field(name: str, ftype: str, number: int, repeated: bool = False) -> dict:
    return {"name": name, "type": ftype, "number": number, "repeated": repeated}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def registry(tmp_path):
    """Return a fresh SchemaRegistry backed by a temp SQLite file."""
    return SchemaRegistry(db_path=str(tmp_path / "test_registry.db"))


# ===========================================================================
# 1. Registration – happy path
# ===========================================================================


class TestRegistration:
    def test_register_v1_returns_version_1(self, registry):
        sv = registry.register(str(V1_PROTO))
        assert sv.version == 1
        assert sv.package == "user.v1"

    def test_register_twice_increments_version(self, registry, tmp_path):
        # Register same file twice; the second registration gets version 2
        registry.set_compatibility("user.v1", NONE)
        registry.register(str(V1_PROTO))
        sv2 = registry.register(str(V1_PROTO))
        assert sv2.version == 2

    def test_sha256_stored_correctly(self, registry):
        import hashlib

        sv = registry.register(str(V1_PROTO))
        expected = hashlib.sha256(V1_PROTO.read_bytes()).hexdigest()
        assert sv.sha256 == expected

    def test_ast_round_trips(self, registry):
        sv = registry.register(str(V1_PROTO))
        assert "messages" in sv.ast
        names = [m["name"] for m in sv.ast["messages"]]
        assert "User" in names
        assert "CreateUserCommand" in names


# ===========================================================================
# 2. Retrieval
# ===========================================================================


class TestRetrieval:
    def test_get_latest_returns_highest_version(self, registry):
        registry.set_compatibility("user.v1", NONE)
        registry.register(str(V1_PROTO))
        registry.register(str(V1_PROTO))
        latest = registry.get_latest("user.v1")
        assert latest is not None
        assert latest.version == 2

    def test_get_latest_none_when_empty(self, registry):
        assert registry.get_latest("does.not.exist") is None

    def test_get_by_version(self, registry):
        registry.set_compatibility("user.v1", NONE)
        registry.register(str(V1_PROTO))
        registry.register(str(V1_PROTO))
        sv = registry.get_by_version("user.v1", 1)
        assert sv is not None
        assert sv.version == 1

    def test_get_by_version_none_when_missing(self, registry):
        assert registry.get_by_version("user.v1", 99) is None

    def test_list_schemas_returns_all(self, registry):
        registry.set_compatibility("user.v1", NONE)
        registry.register(str(V1_PROTO))
        registry.register(str(V1_PROTO))
        rows = registry.list_schemas()
        assert len(rows) == 2
        assert all(r["package"] == "user.v1" for r in rows)


# ===========================================================================
# 3. Parsing – reserved fields reach the AST
# ===========================================================================


class TestReservedParsing:
    def test_v2_has_reserved_number(self):
        ast = parse_proto(str(V2_PROTO))
        cmd = next(m for m in ast["messages"] if m["name"] == "CreateUserCommand")
        assert 2 in cmd["reserved_numbers"]

    def test_v2_has_reserved_name(self):
        ast = parse_proto(str(V2_PROTO))
        cmd = next(m for m in ast["messages"] if m["name"] == "CreateUserCommand")
        assert "password" in cmd["reserved_names"]

    def test_v2_new_fields_present(self):
        ast = parse_proto(str(V2_PROTO))
        user = next(m for m in ast["messages"] if m["name"] == "User")
        field_names = [f["name"] for f in user["fields"]]
        assert "first_name" in field_names
        assert "last_name" in field_names


# ===========================================================================
# 4. check_compatibility – mode = BACKWARD
# ===========================================================================


class TestBackwardCompatibility:
    def test_adding_field_is_backward_compatible(self):
        old = _make_ast("p", [_msg("M", [_field("id", "string", 1)])])
        new = _make_ast(
            "p",
            [_msg("M", [_field("id", "string", 1), _field("name", "string", 2)])],
        )
        assert check_compatibility(new, old, BACKWARD) == []

    def test_removing_field_is_backward_violation(self):
        old = _make_ast(
            "p", [_msg("M", [_field("id", "string", 1), _field("email", "string", 2)])]
        )
        new = _make_ast("p", [_msg("M", [_field("id", "string", 1)])])
        violations = check_compatibility(new, old, BACKWARD)
        assert any(v["kind"] == "field_removed" for v in violations)

    def test_removing_field_with_reservation_is_backward_violation(self):
        # Reserving the field name/number is good proto practice, but
        # consumers of the old schema still can't read the removed field.
        old = _make_ast(
            "p", [_msg("M", [_field("id", "string", 1), _field("email", "string", 2)])]
        )
        new = _make_ast(
            "p",
            [_msg("M", [_field("id", "string", 1)], reserved_numbers=[2], reserved_names=["email"])],
        )
        violations = check_compatibility(new, old, BACKWARD)
        # field_removed IS still a backward violation; the reservation only
        # prevents number reuse – it does not restore the field semantics.
        assert any(v["kind"] == "field_removed" for v in violations)

    def test_type_change_is_backward_violation(self):
        old = _make_ast("p", [_msg("M", [_field("count", "int32", 1)])])
        new = _make_ast("p", [_msg("M", [_field("count", "string", 1)])])
        violations = check_compatibility(new, old, BACKWARD)
        assert any(v["kind"] == "field_type_changed" for v in violations)

    def test_number_change_is_backward_violation(self):
        old = _make_ast("p", [_msg("M", [_field("email", "string", 1)])])
        new = _make_ast("p", [_msg("M", [_field("email", "string", 2)])])
        violations = check_compatibility(new, old, BACKWARD)
        assert any(v["kind"] == "field_number_changed" for v in violations)

    def test_number_reuse_is_backward_violation(self):
        old = _make_ast("p", [_msg("M", [_field("email", "string", 1)])])
        new = _make_ast("p", [_msg("M", [_field("username", "string", 1)])])
        violations = check_compatibility(new, old, BACKWARD)
        assert any(v["kind"] == "field_number_reused" for v in violations)

    def test_v2_backward_compatible_with_v1_user_message(self):
        """User message in v2 only adds fields → backward compatible."""
        v1_ast = parse_proto(str(V1_PROTO))
        v2_ast = parse_proto(str(V2_PROTO))

        v1_user_ast = _make_ast(
            "user.v1",
            [m for m in v1_ast["messages"] if m["name"] == "User"],
        )
        v2_user_ast = _make_ast(
            "user.v2",
            [m for m in v2_ast["messages"] if m["name"] == "User"],
        )
        violations = check_compatibility(v2_user_ast, v1_user_ast, BACKWARD)
        assert violations == []


# ===========================================================================
# 5. check_compatibility – mode = FORWARD
# ===========================================================================


class TestForwardCompatibility:
    def test_removing_field_is_forward_compatible(self):
        """Old reader gets default value for missing field – that is acceptable."""
        old = _make_ast(
            "p", [_msg("M", [_field("id", "string", 1), _field("legacy", "string", 2)])]
        )
        new = _make_ast("p", [_msg("M", [_field("id", "string", 1)])])
        assert check_compatibility(new, old, FORWARD) == []

    def test_type_change_is_forward_violation(self):
        old = _make_ast("p", [_msg("M", [_field("count", "int32", 1)])])
        new = _make_ast("p", [_msg("M", [_field("count", "string", 1)])])
        violations = check_compatibility(new, old, FORWARD)
        assert any(v["kind"] == "field_type_changed" for v in violations)

    def test_number_reuse_is_forward_violation(self):
        old = _make_ast("p", [_msg("M", [_field("email", "string", 1)])])
        new = _make_ast("p", [_msg("M", [_field("username", "string", 1)])])
        violations = check_compatibility(new, old, FORWARD)
        assert any(v["kind"] == "field_number_reused" for v in violations)


# ===========================================================================
# 6. check_compatibility – mode = NONE
# ===========================================================================


class TestNoneCompatibility:
    def test_any_change_accepted(self):
        old = _make_ast(
            "p", [_msg("M", [_field("id", "string", 1), _field("email", "string", 2)])]
        )
        new = _make_ast("p", [_msg("M", [])])  # removed everything
        assert check_compatibility(new, old, NONE) == []


# ===========================================================================
# 7. Registry enforces compatibility on register()
# ===========================================================================


class TestRegistryEnforcement:
    def _make_proto(self, tmp_path: Path, package: str, content: str) -> str:
        """Write a minimal .proto file and return its path.

        *content* should be a multi-line string containing message definitions
        (the parser does not support one-liner ``message M { ... }`` syntax).
        """
        proto_dir = tmp_path / package.replace(".", "_")
        proto_dir.mkdir(parents=True, exist_ok=True)
        p = proto_dir / "schema.proto"
        p.write_text(
            f'syntax = "proto3";\npackage {package};\n{content}',
            encoding="utf-8",
        )
        return str(p)

    def test_backward_violation_raises(self, registry, tmp_path):
        p1 = self._make_proto(
            tmp_path,
            "test.pkg",
            "message M {\n  string email = 1;\n  string name = 2;\n}",
        )
        registry.register(p1, mode=NONE)
        # Remove field 'name' – backward violation
        p2 = self._make_proto(
            tmp_path / "v2",
            "test.pkg",
            "message M {\n  string email = 1;\n}",
        )
        with pytest.raises(IncompatibleSchemaError) as exc_info:
            registry.register(p2, mode=BACKWARD)
        assert exc_info.value.violations
        assert any(v["kind"] == "field_removed" for v in exc_info.value.violations)

    def test_forward_accepts_field_removal(self, registry, tmp_path):
        p1 = self._make_proto(
            tmp_path,
            "test.fwd",
            "message M {\n  string email = 1;\n  string legacy = 2;\n}",
        )
        registry.register(p1, mode=NONE)
        # Remove 'legacy' – should be FORWARD compatible
        p2 = self._make_proto(
            tmp_path / "v2",
            "test.fwd",
            "message M {\n  string email = 1;\n}",
        )
        sv = registry.register(p2, mode=FORWARD)
        assert sv.version == 2

    def test_full_transitive_checks_all_versions(self, registry, tmp_path):
        """FULL_TRANSITIVE: every version must be backward compatible with every prior."""
        p1 = self._make_proto(tmp_path, "test.ft", "message M {\n  string a = 1;\n}")
        registry.register(p1, mode=NONE)

        p2 = self._make_proto(
            tmp_path / "v2",
            "test.ft",
            "message M {\n  string a = 1;\n  string b = 2;\n}",
        )
        registry.register(p2, mode=NONE)

        # Now try to remove 'a' – should violate FULL_TRANSITIVE
        p3 = self._make_proto(
            tmp_path / "v3",
            "test.ft",
            "message M {\n  string b = 2;\n}",
        )
        with pytest.raises(IncompatibleSchemaError):
            registry.register(p3, mode=FULL_TRANSITIVE)

    def test_none_mode_accepts_breaking_change(self, registry, tmp_path):
        p1 = self._make_proto(tmp_path, "test.none", "message M {\n  string a = 1;\n}")
        registry.register(p1, mode=NONE)
        p2 = self._make_proto(tmp_path / "v2", "test.none", "message M {\n}")
        sv = registry.register(p2, mode=NONE)
        assert sv.version == 2

    def test_compatibility_mode_persisted(self, registry):
        registry.set_compatibility("my.pkg", FORWARD)
        assert registry.get_compatibility("my.pkg") == FORWARD

    def test_default_compatibility_is_backward(self, registry):
        assert registry.get_compatibility("unknown.pkg") == BACKWARD


# ===========================================================================
# 8. Violations carry structured diffs
# ===========================================================================


class TestViolationStructure:
    def test_field_removed_has_field_key(self):
        old = _make_ast("p", [_msg("M", [_field("id", "string", 1), _field("email", "string", 2)])])
        new = _make_ast("p", [_msg("M", [_field("id", "string", 1)])])
        violations = check_compatibility(new, old, BACKWARD)
        removed = next(v for v in violations if v["kind"] == "field_removed")
        assert removed["field"] == "email"
        assert removed["number"] == 2

    def test_type_changed_has_old_and_new_type(self):
        old = _make_ast("p", [_msg("M", [_field("count", "int32", 1)])])
        new = _make_ast("p", [_msg("M", [_field("count", "string", 1)])])
        violations = check_compatibility(new, old, BACKWARD)
        changed = next(v for v in violations if v["kind"] == "field_type_changed")
        assert changed["old_type"] == "int32"
        assert changed["new_type"] == "string"

    def test_number_reused_has_old_and_new_field_names(self):
        old = _make_ast("p", [_msg("M", [_field("email", "string", 1)])])
        new = _make_ast("p", [_msg("M", [_field("username", "string", 1)])])
        violations = check_compatibility(new, old, BACKWARD)
        reused = next(v for v in violations if v["kind"] == "field_number_reused")
        assert reused["old_field"] == "email"
        assert reused["new_field"] == "username"


# ===========================================================================
# 9. JSON Schema metadata embedding
# ===========================================================================


class TestJsonSchemaMetadata:
    def test_x_proto_version_embedded(self):
        from generate_json_schema import generate

        ast = parse_proto(str(V1_PROTO))
        schema = generate(ast, registry_id="abc123", registry_version=1)
        assert schema["x-registry-id"] == "abc123"
        assert schema["x-proto-version"] == 1

    def test_no_metadata_when_not_provided(self):
        from generate_json_schema import generate

        ast = parse_proto(str(V1_PROTO))
        schema = generate(ast)
        assert "x-registry-id" not in schema
        assert "x-proto-version" not in schema

    def test_existing_tests_still_pass(self):
        """Ensure the generate() signature change is backward compatible."""
        from generate_json_schema import generate

        ast = parse_proto(str(V1_PROTO))
        schema = generate(ast)
        assert "$schema" in schema
        assert "definitions" in schema
        assert "User" in schema["definitions"]
