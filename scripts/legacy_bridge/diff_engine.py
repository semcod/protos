"""
diff_engine.py – detect discrepancies between legacy schemas and proto contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from .normalizer import NormalizedField


class DiffKind(str, Enum):
    OK = "OK"
    MISSING_IN_PROTO = "MISSING_IN_PROTO"
    MISSING_IN_LEGACY = "MISSING_IN_LEGACY"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    REQUIRED_MISMATCH = "REQUIRED_MISMATCH"
    REPEATED_MISMATCH = "REPEATED_MISMATCH"


@dataclass
class DiffEntry:
    kind: DiffKind
    field_name: str
    message: str
    legacy_type: str | None = None
    proto_type: str | None = None
    severity: str = "INFO"  # "ERROR" | "WARNING" | "INFO"
    suggestion: str = ""


@dataclass
class DiffReport:
    entries: list[DiffEntry]
    readiness: float  # 0.0 - 1.0


def diff_fields(legacy_fields: list[NormalizedField], proto_fields: list[NormalizedField]) -> DiffReport:
    """
    Compare two lists of normalized fields and return a report.
    """
    entries = []
    legacy_map = {f.name: f for f in legacy_fields}
    proto_map = {f.name: f for f in proto_fields}

    all_names = sorted(set(legacy_map.keys()) | set(proto_map.keys()))

    for name in all_names:
        l_field = legacy_map.get(name)
        p_field = proto_map.get(name)

        if not p_field:
            entries.append(
                DiffEntry(
                    kind=DiffKind.MISSING_IN_PROTO,
                    field_name=name,
                    message=f"Field '{name}' found in legacy but missing in proto.",
                    legacy_type=l_field.norm_type if l_field else None,
                    severity="ERROR",
                    suggestion=f"Add field '{name}' to the proto message.",
                )
            )
            continue

        if not l_field:
            entries.append(
                DiffEntry(
                    kind=DiffKind.MISSING_IN_LEGACY,
                    field_name=name,
                    message=f"Field '{name}' found in proto but missing in legacy.",
                    proto_type=p_field.norm_type,
                    severity="INFO",
                    suggestion="This is acceptable if the legacy system doesn't need this data.",
                )
            )
            continue

        # Check for type mismatch
        if l_field.norm_type != p_field.norm_type:
            entries.append(
                DiffEntry(
                    kind=DiffKind.TYPE_MISMATCH,
                    field_name=name,
                    message=f"Type mismatch for '{name}': legacy={l_field.norm_type}, proto={p_field.norm_type}",
                    legacy_type=l_field.norm_type,
                    proto_type=p_field.norm_type,
                    severity="ERROR",
                    suggestion=f"Update proto type to match legacy type: {l_field.norm_type}",
                )
            )

        # Check for repeated mismatch
        if l_field.repeated != p_field.repeated:
            entries.append(
                DiffEntry(
                    kind=DiffKind.REPEATED_MISMATCH,
                    field_name=name,
                    message=f"Repeated/Array mismatch for '{name}': legacy={l_field.repeated}, proto={p_field.repeated}",
                    severity="ERROR",
                    suggestion=f"Set 'repeated' in proto to {l_field.repeated}",
                )
            )

    # Calculate readiness
    total_checks = len(all_names)
    errors = len([e for e in entries if e.severity == "ERROR"])
    readiness = 1.0 - (errors / total_checks) if total_checks > 0 else 1.0

    return DiffReport(entries=entries, readiness=max(0.0, readiness))
