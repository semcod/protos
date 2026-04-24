"""
test_diff_engine.py – tests for the legacy bridge diff engine.
"""

import pytest
from scripts.legacy_bridge.normalizer import NormalizedField, normalize_json_schema, normalize_proto_ast
from scripts.legacy_bridge.diff_engine import diff_fields, DiffKind


def test_identical_schemas():
    legacy = [NormalizedField("id", "string", False, True, "json_schema", "string")]
    proto = [NormalizedField("id", "string", False, True, "proto", "string")]
    
    report = diff_fields(legacy, proto)
    assert report.readiness == 1.0
    assert len(report.entries) == 0


def test_missing_in_proto():
    legacy = [
        NormalizedField("id", "string", False, True, "json_schema", "string"),
        NormalizedField("age", "int", False, False, "json_schema", "integer")
    ]
    proto = [NormalizedField("id", "string", False, True, "proto", "string")]
    
    report = diff_fields(legacy, proto)
    assert report.readiness == 0.5
    assert len(report.entries) == 1
    assert report.entries[0].kind == DiffKind.MISSING_IN_PROTO
    assert report.entries[0].field_name == "age"


def test_type_mismatch():
    legacy = [NormalizedField("id", "string", False, True, "json_schema", "string")]
    proto = [NormalizedField("id", "int", False, True, "proto", "int32")]
    
    report = diff_fields(legacy, proto)
    assert report.readiness == 0.0
    assert len(report.entries) == 1
    assert report.entries[0].kind == DiffKind.TYPE_MISMATCH


def test_repeated_mismatch():
    legacy = [NormalizedField("tags", "string", True, True, "json_schema", "array")]
    proto = [NormalizedField("tags", "string", False, True, "proto", "string")]
    
    report = diff_fields(legacy, proto)
    assert report.readiness == 0.0
    assert len(report.entries) == 1
    assert report.entries[0].kind == DiffKind.REPEATED_MISMATCH


def test_normalize_json_schema():
    schema = {
        "properties": {
            "email": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["email"]
    }
    fields = normalize_json_schema(schema)
    assert len(fields) == 2
    
    email_f = next(f for f in fields if f.name == "email")
    assert email_f.norm_type == "string"
    assert email_f.required is True
    
    age_f = next(f for f in fields if f.name == "age")
    assert age_f.norm_type == "int"
    assert age_f.required is False
