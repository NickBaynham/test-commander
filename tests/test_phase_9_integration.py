"""Step 9.8 - Phase 9 integration smoke.

Drives the full Phase 2 -> ... -> 9 chain against a fresh tmp consuming project.
Reuses the Phase-8 integration's upstream sweep (which itself reuses Phase 7),
so the diagram sources (requirements inventory, requirements map, test map with
resolved results, system model, user journeys, automation plan, quality report)
are all produced by the real helpers. The risk register has no shipped producer
(it is human-authored), so it is seeded from the seeded-visuals fixture - the
one source the chain does not generate.

Asserts the Step 9.8 contract from planning/plan.md: every diagram type renders
valid Mermaid with cited sources; the infographic carries only measured facts;
/tc:render-visuals is refused under pytest; the write boundary holds (Phase 9
writes only under visuals/); /tc:next advances past /tc:visualize. Plus a
byte-stable re-run and PHASE_OWNERSHIP["9"] == ["visuals"].
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
sys.path.insert(0, str(REPO / "tests"))

import generate_infographic  # noqa: E402
import next_step  # noqa: E402
import render_visuals  # noqa: E402
import test_phase_8_integration as p8  # noqa: E402
import visualize  # noqa: E402
import workspace_state  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "seeded-visuals"

EXPECTED_DIAGRAMS = {
    "flow.md",
    "sequence.md",
    "state.md",
    "architecture.md",
    "risk.md",
    "coverage.md",
    "traceability.md",
    "test-strategy.md",
}


def mermaid_block(text: str) -> str:
    start = text.index("```mermaid")
    end = text.index("```", start + 3)
    return text[start + len("```mermaid") : end].strip()


def setup_through_phase_8(tmp_path: Path) -> Path:
    project = p8._setup_through_phase_7(tmp_path)
    p8.run_phase_8(project)
    # The risk register is human-authored (no shipped producer); seed it.
    ws = project / ".test-commander"
    (ws / "risk-register").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        FIXTURE / "risk-register" / "risk-register.md",
        ws / "risk-register" / "risk-register.md",
    )
    return project


def snapshot_outside_visuals(project: Path) -> dict[Path, bytes]:
    ws = project / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and "visuals" not in p.relative_to(ws).parts
    }


def test_phase_ownership_9_is_visuals():
    assert workspace_state.PHASE_OWNERSHIP["9"] == ["visuals"]


def test_full_phase_9_workflow(tmp_path: Path):
    project = setup_through_phase_8(tmp_path)
    outside_before = snapshot_outside_visuals(project)

    # Every diagram renders valid Mermaid with a cited-sources footer.
    written = visualize.visualize(project)
    names = {p.name for p in written}
    assert names >= EXPECTED_DIAGRAMS, f"missing diagrams: {EXPECTED_DIAGRAMS - names}"
    for p in written:
        text = p.read_text(encoding="utf-8")
        assert "```mermaid" in text and "> Sources:" in text, f"{p.name} malformed"
        assert mermaid_block(text), f"{p.name} has an empty Mermaid body"

    # The infographic carries only measured facts, with a sources footer.
    info = generate_infographic.generate_infographic(project)
    spec = next(p for p in info if p.name == "quality-spec.md").read_text(encoding="utf-8")
    assert "```yaml" in spec and "> Sources:" in spec
    assert "requirements:" in spec

    # /tc:render-visuals is refused under pytest (when the CLI is present).
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(render_visuals, "mmdc_available", lambda: True)
    with pytest.raises(render_visuals.RenderRefusedError):
        render_visuals.render_visuals(project)
    monkeypatch.undo()

    # Write boundary: nothing outside visuals/ changed.
    assert snapshot_outside_visuals(project) == outside_before, (
        "Phase 9 must write only under visuals/"
    )

    # /tc:next advances past /tc:visualize (phase 9 now in_progress).
    rec = next_step.next_step_for(project)
    if rec is not None:
        assert rec.command != "/tc:visualize", f"/tc:next still recommends /tc:visualize: {rec}"


def test_byte_stable_rerun_across_phase_9(tmp_path: Path):
    project = setup_through_phase_8(tmp_path)
    visualize.visualize(project)
    generate_infographic.generate_infographic(project)
    visuals = project / ".test-commander" / "visuals"
    targets = sorted(p for p in visuals.rglob("*.md") if p.is_file())
    first = {p: p.read_bytes() for p in targets}
    visualize.visualize(project)
    generate_infographic.generate_infographic(project)
    for path, data in first.items():
        assert path.read_bytes() == data, f"{path.name} not byte-stable on Phase 9 re-run"


def test_next_recommends_visualize_before_it_runs(tmp_path: Path):
    """Before Phase 9 runs, /tc:next should point at /tc:visualize (R10)."""
    project = setup_through_phase_8(tmp_path)
    rec = next_step.next_step_for(project)
    assert rec is not None and rec.command == "/tc:visualize"
