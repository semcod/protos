"""
report_generator.py – generate markdown migration reports.
"""

from __future__ import annotations
import datetime
from .diff_engine import DiffReport, DiffKind


def generate_markdown_report(
    subject: str, 
    legacy_version: int, 
    proto_version: int, 
    report: DiffReport,
    suggestion: str
) -> str:
    """
    Generate a detailed markdown report for the migration status.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status_emoji = "✅" if report.readiness == 1.0 else "⚠️"
    if report.readiness < 0.5: status_emoji = "❌"

    lines = [
        f"# Migration Readiness Report: {subject}",
        f"Generated: {now}",
        "",
        f"## Status: {status_emoji} {report.readiness * 100:.1f}% Ready",
        "",
        "### Versions Compared",
        f"- **Legacy (JSON)**: v{legacy_version}",
        f"- **Proto (Contract)**: v{proto_version}",
        "",
        "### Discrepancy Summary",
    ]

    if not report.entries:
        lines.append("No discrepancies found. The systems are fully in sync.")
    else:
        lines.append("| Field | Kind | Severity | Message |")
        lines.append("|-------|------|----------|---------|")
        for e in report.entries:
            lines.append(f"| `{e.field_name}` | {e.kind} | {e.severity} | {e.message} |")

    lines.append("")
    lines.append("### Recommended Action")
    if report.readiness == 1.0:
        lines.append("No action required. The bridge is stable.")
    else:
        lines.append("Apply the following changes to the `.proto` contract to improve compatibility:")
        lines.append("```proto")
        lines.append(suggestion)
        lines.append("```")

    return "\n".join(lines)
