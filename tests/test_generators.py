"""
tests/test_generators.py – integration tests for the proto → multi-target pipeline.

Run with:
    python -m pytest tests/ -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make scripts importable without installing.
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from parse_proto import parse_proto  # noqa: E402
from generate_zod import to_zod  # noqa: E402
from generate_pydantic import generate as gen_pydantic  # noqa: E402
from generate_json_schema import generate as gen_json_schema  # noqa: E402
from generate_sql import generate_sql  # noqa: E402

PROTO_FILE = Path(__file__).parent.parent / "contracts" / "user" / "v1" / "user.proto"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def ast():
    return parse_proto(str(PROTO_FILE))


# ---------------------------------------------------------------------------
# parse_proto
# ---------------------------------------------------------------------------


class TestParseProto:
    def test_package_parsed(self, ast):
        assert ast["package"] == "user.v1"

    def test_message_count(self, ast):
        assert len(ast["messages"]) == 3

    def test_message_names(self, ast):
        names = [m["name"] for m in ast["messages"]]
        assert "CreateUserCommand" in names
        assert "GetUserQuery" in names
        assert "User" in names

    def test_user_fields(self, ast):
        user = next(m for m in ast["messages"] if m["name"] == "User")
        field_names = [f["name"] for f in user["fields"]]
        assert "id" in field_names
        assert "email" in field_names

    def test_create_user_command_fields(self, ast):
        cmd = next(m for m in ast["messages"] if m["name"] == "CreateUserCommand")
        field_names = [f["name"] for f in cmd["fields"]]
        assert "email" in field_names
        assert "password" in field_names

    def test_field_types(self, ast):
        user = next(m for m in ast["messages"] if m["name"] == "User")
        types = {f["name"]: f["type"] for f in user["fields"]}
        assert types["id"] == "string"
        assert types["email"] == "string"

    def test_field_numbers(self, ast):
        user = next(m for m in ast["messages"] if m["name"] == "User")
        numbers = {f["name"]: f["number"] for f in user["fields"]}
        assert numbers["id"] == 1
        assert numbers["email"] == 2

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            parse_proto("/nonexistent/path/file.proto")


# ---------------------------------------------------------------------------
# generate_zod
# ---------------------------------------------------------------------------


class TestGenerateZod:
    def test_contains_import(self, ast):
        output = to_zod(ast)
        assert 'import { z } from "zod"' in output

    def test_schema_exports_present(self, ast):
        output = to_zod(ast)
        assert "CreateUserCommandSchema" in output
        assert "UserSchema" in output

    def test_string_fields_use_z_string(self, ast):
        output = to_zod(ast)
        assert "z.string()" in output

    def test_type_exports_present(self, ast):
        output = to_zod(ast)
        assert "export type User" in output
        assert "export type CreateUserCommand" in output

    def test_output_to_file(self, ast, tmp_path):
        out = tmp_path / "user.ts"
        content = to_zod(ast)
        out.write_text(content, encoding="utf-8")
        assert out.exists()
        assert "z.object" in out.read_text()


# ---------------------------------------------------------------------------
# generate_pydantic
# ---------------------------------------------------------------------------


class TestGeneratePydantic:
    def test_pydantic_import(self, ast):
        output = gen_pydantic(ast)
        assert "from pydantic import BaseModel" in output

    def test_class_definitions(self, ast):
        output = gen_pydantic(ast)
        assert "class User(BaseModel):" in output
        assert "class CreateUserCommand(BaseModel):" in output

    def test_string_fields(self, ast):
        output = gen_pydantic(ast)
        assert "email: str" in output

    def test_output_is_valid_python(self, ast):
        output = gen_pydantic(ast)
        # Should not raise
        compile(output, "<string>", "exec")


# ---------------------------------------------------------------------------
# generate_json_schema
# ---------------------------------------------------------------------------


class TestGenerateJsonSchema:
    def test_schema_key_present(self, ast):
        schema = gen_json_schema(ast)
        assert "$schema" in schema
        assert "definitions" in schema

    def test_user_definition_present(self, ast):
        schema = gen_json_schema(ast)
        assert "User" in schema["definitions"]

    def test_user_properties(self, ast):
        schema = gen_json_schema(ast)
        user_def = schema["definitions"]["User"]
        assert "id" in user_def["properties"]
        assert "email" in user_def["properties"]

    def test_required_fields(self, ast):
        schema = gen_json_schema(ast)
        user_def = schema["definitions"]["User"]
        assert "id" in user_def["required"]
        assert "email" in user_def["required"]

    def test_json_serialisable(self, ast):
        schema = gen_json_schema(ast)
        dumped = json.dumps(schema)
        reloaded = json.loads(dumped)
        assert reloaded["definitions"]["User"]["type"] == "object"


# ---------------------------------------------------------------------------
# generate_sql
# ---------------------------------------------------------------------------


class TestGenerateSql:
    def test_create_table_users(self, ast):
        sql = generate_sql(ast)
        assert "CREATE TABLE users" in sql

    def test_primary_key_on_id(self, ast):
        sql = generate_sql(ast)
        assert "id TEXT PRIMARY KEY" in sql

    def test_email_not_null(self, ast):
        sql = generate_sql(ast)
        assert "email TEXT NOT NULL" in sql

    def test_no_command_tables(self, ast):
        sql = generate_sql(ast)
        assert "CREATE TABLE create_user_commands" not in sql
        assert "CREATE TABLE get_user_queries" not in sql
