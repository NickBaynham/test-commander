"""Step 9.6 - /tc:render-visuals.

Walks visuals/mermaid/*.md, extracts each Mermaid block, and plans SVG/PNG
output paths. The real Mermaid-CLI invocation is refused under pytest via the
PYTEST_CURRENT_TEST guard, so the suite asserts extraction + planned paths + the
CLI-missing graceful degradation, never a rendered binary.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-visuals"

import render_visuals  # noqa: E402
import visualize  # noqa: E402


def seed_and_generate(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    visualize.visualize(project)  # populate visuals/mermaid/*.md
    return project


def test_uninitialized_refused(tmp_path: Path):
    with pytest.raises(visualize.UninitializedWorkspaceError):
        render_visuals.render_visuals(tmp_path / "nope")


def test_no_mermaid_refused(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".test-commander").mkdir(parents=True)
    with pytest.raises(visualize.MissingSourceError) as exc:
        render_visuals.render_visuals(project)
    assert "/tc:visualize" in str(exc.value)


def test_extract_mermaid_pulls_the_block():
    text = "# T\n\nintro\n\n```mermaid\nflowchart TD\n    a --> b\n```\n\n> Sources: `x`\n"
    block = render_visuals.extract_mermaid(text)
    assert block is not None
    assert block.startswith("flowchart TD")
    assert "a --> b" in block


def test_plan_outputs_maps_each_mermaid_to_svg_and_png(tmp_path: Path):
    project = seed_and_generate(tmp_path)
    workspace = project / ".test-commander"
    plans = render_visuals.plan_visuals(workspace)
    names = {p.name for p, _svg, _png in plans}
    assert "flow.md" in names and "risk.md" in names
    for src, svg, png in plans:
        assert svg == workspace / "visuals" / "svg" / (src.stem + ".svg")
        assert png == workspace / "visuals" / "png" / (src.stem + ".png")


def test_cli_missing_degrades_gracefully(tmp_path: Path, monkeypatch):
    project = seed_and_generate(tmp_path)
    monkeypatch.setattr(render_visuals, "mmdc_available", lambda: False)
    result = render_visuals.render_visuals(project)  # no raise
    assert result.cli_missing is True
    assert result.rendered == []
    # No binary was written.
    ws = project / ".test-commander"
    assert not list((ws / "visuals" / "svg").glob("*.svg"))
    assert not list((ws / "visuals" / "png").glob("*.png"))


def test_real_render_refused_under_pytest(tmp_path: Path, monkeypatch):
    project = seed_and_generate(tmp_path)
    monkeypatch.setattr(render_visuals, "mmdc_available", lambda: True)
    with pytest.raises(render_visuals.RenderRefusedError) as exc:
        render_visuals.render_visuals(project)
    msg = str(exc.value).lower()
    assert "pytest" in msg


def test_invoke_mmdc_guarded_directly(tmp_path: Path):
    with pytest.raises(render_visuals.RenderRefusedError):
        render_visuals._invoke_mmdc("flowchart TD\n  a --> b", tmp_path / "a.svg")
