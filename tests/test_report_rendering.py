from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from legacy_bridge.report_rendering import (
    render_delegation_decisions_markdown,
    render_excluded_candidates_markdown,
    render_service_boundary_decisions_markdown,
    render_summary_markdown,
)


def test_render_summary_markdown_contains_required_sections() -> None:
    summary = {
        "generated_at": "2026-04-24T12:00:00+00:00",
        "repo_root": "/tmp/repo",
        "profile": {
            "languages": [{"name": "python"}, {"name": "typescript"}],
            "frameworks": ["fastapi"],
            "architecture_hints": ["modular-monolith"],
        },
        "counts": {
            "candidate_modules": 2,
            "delegation_plan_modules": 1,
            "swop_contexts": 0,
        },
        "top_delegable_candidates": ["connect-id"],
        "top_candidates": ["connect-id", "connect-manager"],
        "top_service_candidates": ["connect-id"],
        "service_boundary_decision_reasons": [{"reason": "delivery mode: iframe-first", "count": 1}],
        "excluded_candidate_reasons": [{"reason": "too-few-files", "count": 1}],
        "delegation_decision_reasons": [{"reason": "high-priority", "count": 1}],
        "top_cqrs_pattern_candidates": ["connect-id"],
        "top_swop_contexts": [],
        "artifacts": {
            "summary_json": "reports/migration-discovery/migration-discovery.summary.json",
        },
    }

    markdown = render_summary_markdown(summary)

    assert "# Migration Discovery Summary" in markdown
    assert "## Top swop contexts" in markdown
    assert "- `none`" in markdown
    assert "| swop_contexts | 0 |" in markdown
    assert "| summary_json | `reports/migration-discovery/migration-discovery.summary.json` |" in markdown


def test_render_excluded_candidates_markdown_formats_details() -> None:
    payload = {
        "count": 1,
        "reason_counts": [{"reason": "not-delegable", "count": 1}],
        "rows": [
            {
                "module": "connect-id",
                "path": "frontend/src/modules/connect-id",
                "kind": "frontend",
                "score": 91,
                "phase": "phase-1",
                "reasons": ["has api", "has ui"],
            }
        ],
    }

    markdown = render_excluded_candidates_markdown(payload)

    assert "# Excluded Delegation Candidates" in markdown
    assert "### Excluded: connect-id" in markdown
    assert "- Score: `91.00`" in markdown
    assert "  - has api" in markdown


def test_render_delegation_markdown_empty_rows_message() -> None:
    payload = {
        "count": 0,
        "reason_counts": [],
        "rows": [],
    }

    markdown = render_delegation_decisions_markdown(payload)

    assert "# Delegation Decision Rationale" in markdown
    assert "No selected delegation candidates." in markdown
    assert "- `none`" in markdown


def test_render_service_boundary_markdown_empty_rows_message() -> None:
    payload = {
        "count": 0,
        "reason_counts": [],
        "rows": [],
    }

    markdown = render_service_boundary_decisions_markdown(payload)

    assert "# Service Boundary Decision Rationale" in markdown
    assert "No recommended service candidates." in markdown
    assert "## Repeated decision signals" in markdown
