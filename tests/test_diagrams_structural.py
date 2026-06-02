"""Step 9.3 - structural diagrams: sequence, state, architecture.

Each generator mirrors 9.2's shared engine. Per command: a missing source is
refused (pointing at the producer), it emits valid Mermaid of the right kind
with a cited-sources footer, and it is byte-stable on re-run.
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
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    return project


def mermaid_block(text: str) -> str:
    start = text.index("```mermaid")
    end = text.index("```", start + 3)
    return text[start + len("```mermaid") : end].strip()


# ---------------------------------------------------------------------------
# diagram-sequence
# ---------------------------------------------------------------------------


def test_sequence_emits_valid_sequence_diagram(tmp_path: Path):
    project = seed_workspace(tmp_path)
    out = visualize.diagram_sequence(project)
    assert out.name == "sequence.md"
    body = mermaid_block(out.read_text(encoding="utf-8"))
    assert body.startswith("sequenceDiagram")
    assert "Sign in and open a workspace" in body, "each journey is a message"


def test_sequence_cites_and_is_stable(tmp_path: Path):
    project = seed_workspace(tmp_path)
    text = visualize.diagram_sequence(project).read_text(encoding="utf-8")
    assert "> Sources:" in text and "product-knowledge/user-journeys.md" in text
    first = visualize.diagram_sequence(project).read_bytes()
    second = visualize.diagram_sequence(project).read_bytes()
    assert first == second


def test_sequence_missing_source_refused(tmp_path: Path):
    project = seed_workspace(tmp_path)
    (project / ".test-commander" / "product-knowledge" / "user-journeys.md").unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        visualize.diagram_sequence(project)
    assert "learn-from-docs" in str(exc.value)


# ---------------------------------------------------------------------------
# diagram-state
# ---------------------------------------------------------------------------


def test_state_emits_valid_state_diagram(tmp_path: Path):
    project = seed_workspace(tmp_path)
    out = visualize.diagram_state(project)
    assert out.name == "state.md"
    body = mermaid_block(out.read_text(encoding="utf-8"))
    assert body.startswith("stateDiagram-v2")
    # The fixture test-map carries passed / failed / flaky / pending results.
    for state in ("Passed", "Failed", "Flaky", "Pending"):
        assert state in body, f"the result lifecycle must include {state}"


def test_state_cites_and_is_stable(tmp_path: Path):
    project = seed_workspace(tmp_path)
    text = visualize.diagram_state(project).read_text(encoding="utf-8")
    assert "> Sources:" in text and "traceability/test-map.md" in text
    first = visualize.diagram_state(project).read_bytes()
    second = visualize.diagram_state(project).read_bytes()
    assert first == second


def test_state_missing_source_refused(tmp_path: Path):
    project = seed_workspace(tmp_path)
    (project / ".test-commander" / "traceability" / "test-map.md").unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        visualize.diagram_state(project)
    assert "traceability-map" in str(exc.value)


# ---------------------------------------------------------------------------
# diagram-architecture
# ---------------------------------------------------------------------------


def test_architecture_emits_valid_flowchart(tmp_path: Path):
    project = seed_workspace(tmp_path)
    out = visualize.diagram_architecture(project)
    assert out.name == "architecture.md"
    body = mermaid_block(out.read_text(encoding="utf-8"))
    assert body.startswith("flowchart")
    for entity in ("Account", "Workspace", "File"):
        assert entity in body, f"architecture must include the {entity} entity"


def test_architecture_cites_and_is_stable(tmp_path: Path):
    project = seed_workspace(tmp_path)
    text = visualize.diagram_architecture(project).read_text(encoding="utf-8")
    assert "> Sources:" in text and "product-knowledge/system-model.md" in text
    first = visualize.diagram_architecture(project).read_bytes()
    second = visualize.diagram_architecture(project).read_bytes()
    assert first == second


def test_architecture_missing_source_refused(tmp_path: Path):
    project = seed_workspace(tmp_path)
    (project / ".test-commander" / "product-knowledge" / "system-model.md").unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        visualize.diagram_architecture(project)
    assert "learn-from-docs" in str(exc.value)


# ---------------------------------------------------------------------------
# The umbrella now regenerates these too.
# ---------------------------------------------------------------------------


def test_visualize_includes_structural_diagrams(tmp_path: Path):
    project = seed_workspace(tmp_path)
    names = {p.name for p in visualize.visualize(project)}
    assert {"flow.md", "sequence.md", "state.md", "architecture.md"} <= names
