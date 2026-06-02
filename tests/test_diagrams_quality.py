"""Step 9.4 - quality diagrams: risk, coverage, traceability, test-strategy.

Per command: a missing source is refused (pointing at the producer), it emits
valid Mermaid with a cited-sources footer, and it is byte-stable. The
traceability diagram renders the resolved result for resolved scenarios and
`pending` otherwise (never invents).
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
# diagram-risk
# ---------------------------------------------------------------------------


def test_risk_emits_valid_flowchart_with_severity_groups(tmp_path: Path):
    project = seed_workspace(tmp_path)
    out = visualize.diagram_risk(project)
    assert out.name == "risk.md"
    body = mermaid_block(out.read_text(encoding="utf-8"))
    assert body.startswith("flowchart")
    assert "RISK-001" in body and "RISK-004" in body
    assert "subgraph" in body, "risks must be grouped into severity subgraphs"
    assert "High" in body and "Medium" in body and "Low" in body


def test_risk_cites_and_stable_and_refuses(tmp_path: Path):
    project = seed_workspace(tmp_path)
    text = visualize.diagram_risk(project).read_text(encoding="utf-8")
    assert "> Sources:" in text and "risk-register/risk-register.md" in text
    assert visualize.diagram_risk(project).read_bytes() == \
        visualize.diagram_risk(project).read_bytes()
    (project / ".test-commander" / "risk-register" / "risk-register.md").unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        visualize.diagram_risk(project)
    assert "review-requirements" in str(exc.value)


# ---------------------------------------------------------------------------
# diagram-coverage
# ---------------------------------------------------------------------------


def test_coverage_emits_valid_flowchart(tmp_path: Path):
    project = seed_workspace(tmp_path)
    out = visualize.diagram_coverage(project)
    assert out.name == "coverage.md"
    body = mermaid_block(out.read_text(encoding="utf-8"))
    assert body.startswith("flowchart")
    assert "REQ-001" in body and "REQ-003" in body
    # REQ-001 has all three downstream artifacts; REQ-003 has none.
    assert "BDD" in body and "Automation" in body


def test_coverage_cites_and_stable_and_refuses(tmp_path: Path):
    project = seed_workspace(tmp_path)
    text = visualize.diagram_coverage(project).read_text(encoding="utf-8")
    assert "> Sources:" in text and "traceability/requirements-map.md" in text
    assert visualize.diagram_coverage(project).read_bytes() == \
        visualize.diagram_coverage(project).read_bytes()
    (project / ".test-commander" / "traceability" / "requirements-map.md").unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        visualize.diagram_coverage(project)
    assert "requirements-coverage" in str(exc.value)


# ---------------------------------------------------------------------------
# diagram-traceability
# ---------------------------------------------------------------------------


def test_traceability_renders_resolved_and_pending(tmp_path: Path):
    project = seed_workspace(tmp_path)
    out = visualize.diagram_traceability(project)
    assert out.name == "traceability.md"
    body = mermaid_block(out.read_text(encoding="utf-8"))
    assert body.startswith("flowchart")
    assert "REQ-001" in body and "CS-001-001" in body
    # Resolved results shown for resolved rows; pending for the unresolved one.
    assert "Passed" in body and "Failed" in body and "Flaky" in body
    assert "Pending" in body, "the pending row must render pending, not be invented"


def test_traceability_cites_and_stable_and_refuses(tmp_path: Path):
    project = seed_workspace(tmp_path)
    text = visualize.diagram_traceability(project).read_text(encoding="utf-8")
    assert "> Sources:" in text and "traceability/test-map.md" in text
    assert visualize.diagram_traceability(project).read_bytes() == \
        visualize.diagram_traceability(project).read_bytes()
    (project / ".test-commander" / "traceability" / "test-map.md").unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        visualize.diagram_traceability(project)
    assert "traceability-map" in str(exc.value)


# ---------------------------------------------------------------------------
# diagram-test-strategy
# ---------------------------------------------------------------------------


def test_test_strategy_emits_valid_flowchart(tmp_path: Path):
    project = seed_workspace(tmp_path)
    out = visualize.diagram_test_strategy(project)
    assert out.name == "test-strategy.md"
    body = mermaid_block(out.read_text(encoding="utf-8"))
    assert body.startswith("flowchart")
    # The automation plan ranks scenarios automate / consider.
    assert "Automate" in body and "Consider" in body
    assert "Requirements" in body, "the strategy ties to the requirements inventory"


def test_test_strategy_cites_and_stable_and_refuses(tmp_path: Path):
    project = seed_workspace(tmp_path)
    text = visualize.diagram_test_strategy(project).read_text(encoding="utf-8")
    assert "> Sources:" in text
    assert "requirements/requirements-inventory.md" in text
    assert visualize.diagram_test_strategy(project).read_bytes() == \
        visualize.diagram_test_strategy(project).read_bytes()
    for f in (project / ".test-commander" / "automation-plan").glob("*.md"):
        f.unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        visualize.diagram_test_strategy(project)
    assert "automation-plan" in str(exc.value)


# ---------------------------------------------------------------------------
# umbrella
# ---------------------------------------------------------------------------


def test_visualize_includes_quality_diagrams(tmp_path: Path):
    project = seed_workspace(tmp_path)
    names = {p.name for p in visualize.visualize(project)}
    assert {"risk.md", "coverage.md", "traceability.md", "test-strategy.md"} <= names
