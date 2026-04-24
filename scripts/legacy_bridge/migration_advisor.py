"""
migration_advisor.py – generate proto snippets and migration advice from diff reports.
"""

from __future__ import annotations

from .diff_engine import DiffReport, DiffKind


def suggest_proto_additions(report: DiffReport, message_name: str) -> str:
    """
    Generate a suggested proto message block based on missing fields.
    """
    missing = [e for e in report.entries if e.kind == DiffKind.MISSING_IN_PROTO]
    if not missing:
        return "// No missing fields detected."

    lines = [f"message {message_name} {{"]
    
    # Simple heuristic for field numbers: start high to avoid collisions
    start_num = 100 
    
    for i, entry in enumerate(missing):
        field_type = entry.legacy_type or "string"
        # Map normalized type back to proto type
        proto_type = "string"
        if field_type == "int": proto_type = "int32"
        elif field_type == "float": proto_type = "float"
        elif field_type == "bool": proto_type = "bool"
        
        lines.append(f"  {proto_type} {entry.field_name} = {start_num + i};")

    lines.append("}")
    return "\n".join(lines)


def get_migration_summary(report: DiffReport) -> str:
    """
    Return a human-readable summary of the migration readiness.
    """
    summary = [
        f"Migration Readiness: {report.readiness * 100:.1f}%",
        f"Total Issues: {len(report.entries)}",
    ]
    
    errors = [e for e in report.entries if e.severity == "ERROR"]
    if errors:
        summary.append(f"Critical Errors: {len(errors)}")
        for e in errors:
            summary.append(f"  - [{e.kind}] {e.field_name}: {e.message}")
    else:
        summary.append("No critical errors detected. Ready for migration!")
        
    return "\n".join(summary)
