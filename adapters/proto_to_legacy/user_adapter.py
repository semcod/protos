"""
user_adapter.py – convert proto event payload back to legacy user JSON.
"""

from __future__ import annotations
from typing import Any


def proto_to_legacy(proto_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Map proto fields back to legacy fields.
    """
    return {
        "id": proto_dict.get("id"),
        "email": proto_dict.get("email"),
        "first_name": proto_dict.get("first_name"),
        "last_name": proto_dict.get("last_name"),
        "age": proto_dict.get("age"),
        "is_active": proto_dict.get("is_active"),
        "tags": proto_dict.get("tags"),
    }
