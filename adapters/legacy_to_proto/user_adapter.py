"""
user_adapter.py – convert legacy user JSON to proto-compatible dictionary.
"""

from __future__ import annotations
import json
from typing import Any


def legacy_to_proto(legacy_json: dict[str, Any]) -> dict[str, Any]:
    """
    Map legacy fields to proto fields.
    In this case, the fields are identical by name, 
    but we might want to handle missing values or type conversions.
    """
    return {
        "id": str(legacy_json.get("id", "")),
        "email": legacy_json.get("email", ""),
        "first_name": legacy_json.get("first_name", ""),
        "last_name": legacy_json.get("last_name", ""),
        "age": int(legacy_json.get("age", 0)),
        "is_active": bool(legacy_json.get("is_active", False)),
        "tags": list(legacy_json.get("tags", [])),
    }


def wrap_for_event_store(legacy_json: dict[str, Any]) -> dict[str, Any]:
    """
    Wraps the legacy data into a standard event payload.
    """
    proto_data = legacy_to_proto(legacy_json)
    return {
        "event_type": "LegacyUserMigrated",
        "aggregate_id": proto_data["id"],
        "payload": proto_data
    }
