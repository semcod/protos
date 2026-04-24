from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from legacy_bridge.delegation_plan import build_output_row, build_slice_blueprint, render_markdown


def test_build_slice_blueprint_normalizes_module_name():
    blueprint = build_slice_blueprint("Connect Manager")

    assert blueprint["slice_name"] == "connect-manager"
    assert blueprint["contract_dir"] == "contracts/connect-manager/v1"
    assert blueprint["gateway"]["health"] == "/health/modules/connect-manager"


def test_build_output_row_keeps_original_fields_and_adds_slice():
    row = {
        "module": "identification",
        "score": 98.78,
        "phase": "phase-1",
        "effort": "low",
        "reasons": ["files: 2"],
    }

    output_row = build_output_row(row)

    assert output_row["module"] == "identification"
    assert output_row["score"] == 98.78
    assert output_row["slice"]["gateway"]["commands"] == "/commands/identification/*"
    assert output_row["readiness"]["reasons"] == ["files: 2"]


def test_render_markdown_includes_slice_blueprints_section():
    rows = [
        {
            "module": "connect-router",
            "score": 86.75,
            "phase": "phase-1",
            "effort": "low",
            "reasons": ["cross-module imports: 1", "api endpoints used: 1"],
        }
    ]

    markdown = render_markdown(rows, 1)

    assert "## Slice blueprints" in markdown
    assert "- Contract dir: `contracts/connect-router/v1`" in markdown
    assert "- Health: `/health/modules/connect-router`" in markdown
    assert "## Per-module execution checklist" in markdown
