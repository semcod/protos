"""
test_legacy_registry.py – tests for the extended legacy schema registry.
"""

import os
import pytest
from scripts.legacy_registry import LegacySchemaRegistry

DB_TEST_PATH = "test_legacy_registry.db"


@pytest.fixture
def registry():
    if os.path.exists(DB_TEST_PATH):
        os.remove(DB_TEST_PATH)
    reg = LegacySchemaRegistry(db_path=DB_TEST_PATH)
    yield reg
    if os.path.exists(DB_TEST_PATH):
        os.remove(DB_TEST_PATH)


def test_register_and_get_latest(registry):
    schema = {"type": "object", "properties": {"id": {"type": "string"}}}
    sv1 = registry.register("user", "json_schema", schema)
    assert sv1.version == 1
    
    latest = registry.get_latest("user", "json_schema")
    assert latest.version == 1
    assert latest.schema_dict == schema
    
    # Register version 2
    schema2 = {"type": "object", "properties": {"id": {"type": "string"}, "email": {"type": "string"}}}
    sv2 = registry.register("user", "json_schema", schema2)
    assert sv2.version == 2
    
    latest2 = registry.get_latest("user", "json_schema")
    assert latest2.version == 2
    assert latest2.schema_dict == schema2


def test_different_formats_independent(registry):
    schema_json = {"type": "object"}
    schema_proto = {"messages": []}
    
    registry.register("user", "json_schema", schema_json)
    registry.register("user", "proto", schema_proto)
    
    latest_json = registry.get_latest("user", "json_schema")
    latest_proto = registry.get_latest("user", "proto")
    
    assert latest_json.format == "json_schema"
    assert latest_proto.format == "proto"
    assert latest_json.version == 1
    assert latest_proto.version == 1
