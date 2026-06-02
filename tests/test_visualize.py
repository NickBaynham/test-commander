"""Step 9.2 - /tc:visualize, the shared render engine, and /tc:diagram-flow.

Drives the diagram-flow generator and the shared render_diagram engine against
a tmp workspace seeded from tests/fixtures/seeded-visuals/. Asserts:

- uninitialized workspace refused (exit 2);
- a missing source refused, pointing at the producing command;
- the seeded fixture renders a valid Mermaid `flowchart` whose every node traces
  to a source, with a `> Sources:` footer listing the artifact paths;
- byte-stable re-run;
- /tc:visualize regenerates the full set deterministically.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-visuals"

import visualize  # noqa: E402


def seed_workspace(tmp_path: Path) -> Path:
    """Copy the seeded-visuals slice into a tmp project's .test-commander/."""
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(FIXTURE, ws)
    return project


def mermaid_block(text: str) -> str:
    start = text.index("```mermaid")
    end = text.index("```", start + 3)
    return text[start + len("```mermaid") : end].strip()


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_refused(tmp_path: Path):
    with pytest.raises(visualize.UninitializedWorkspaceError):
        visualize.diagram_flow(tmp_path / "nope")


def test_missing_source_refused_points_at_producer(tmp_path: Path):
    project = seed_workspace(tmp_path)
    (project / ".test-commander" / "product-knowledge" / "user-journeys.md").unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        visualize.diagram_flow(project)
    msg = str(exc.value)
    assert "user-journeys.md" in msg
    assert "learn-from-docs" in msg, "the error must direct the user at the producing command"


# ---------------------------------------------------------------------------
# diagram-flow
# ---------------------------------------------------------------------------


def test_diagram_flow_renders_valid_mermaid_flowchart(tmp_path: Path):
    project = seed_workspace(tmp_path)
    out = visualize.diagram_flow(project)
    assert out == project / ".test-commander" / "visuals" / "mermaid" / "flow.md"
    text = out.read_text(encoding="utf-8")
    body = mermaid_block(text)
    assert body.startswith("flowchart"), "diagram-flow must emit a Mermaid flowchart"
    # Every user journey title appears as a node label.
    assert "Sign in and open a workspace" in body
    assert "Upload a file into a workspace" in body
    # Entities from the system model appear (both sources used).
    assert "Account" in body and "Workspace" in body


def test_diagram_flow_cites_its_sources(tmp_path: Path):
    project = seed_workspace(tmp_path)
    text = visualize.diagram_flow(project).read_text(encoding="utf-8")
    assert "> Sources:" in text, "every diagram must carry a Sources footer"
    assert "product-knowledge/user-journeys.md" in text
    assert "product-knowledge/system-model.md" in text


def test_diagram_flow_byte_stable_rerun(tmp_path: Path):
    project = seed_workspace(tmp_path)
    first = visualize.diagram_flow(project).read_bytes()
    second = visualize.diagram_flow(project).read_bytes()
    assert first == second, "diagram-flow must be byte-stable on re-run"


# ---------------------------------------------------------------------------
# /tc:visualize umbrella
# ---------------------------------------------------------------------------


def test_visualize_regenerates_the_set(tmp_path: Path):
    project = seed_workspace(tmp_path)
    written = visualize.visualize(project)
    assert any(p.name == "flow.md" for p in written), "visualize must regenerate diagram-flow"
    for p in written:
        assert p.is_file()


def test_visualize_byte_stable_rerun(tmp_path: Path):
    project = seed_workspace(tmp_path)
    visualize.visualize(project)
    mermaid_dir = project / ".test-commander" / "visuals" / "mermaid"
    first = {p: p.read_bytes() for p in sorted(mermaid_dir.glob("*.md"))}
    visualize.visualize(project)
    for path, data in first.items():
        assert path.read_bytes() == data, f"{path.name} not byte-stable on visualize re-run"


def test_visualize_writes_only_under_visuals(tmp_path: Path):
    project = seed_workspace(tmp_path)
    ws = project / ".test-commander"
    outside_before = {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and "visuals" not in p.relative_to(ws).parts
    }
    visualize.visualize(project)
    outside_after = {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and "visuals" not in p.relative_to(ws).parts
    }
    assert outside_after == outside_before, "visualize must write only under visuals/"
