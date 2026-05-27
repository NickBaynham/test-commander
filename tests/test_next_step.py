"""Step 1.5 — next_step heuristics engine tests.

One fixture per R-rule from next-step-inference.md, plus a ranked-list
test and a format() test.
"""

from pathlib import Path

import init_workspace
import next_step

REPO = Path(__file__).resolve().parent.parent

# canonical workspace file to modify per phase, used to flip the phase to in_progress
PHASE_CANONICAL = {
    1: "project.md",
    2: "requirements/requirements-inventory.md",
    3: "product-knowledge/system-model.md",
    4: "charters/README.md",
    5: "bdd/features/README.md",
    6: "automation-plan/README.md",
    7: "quality-report/current-quality-report.md",
    8: "learning/lessons-inbox.md",
}


def _through_phase(tmp_path: Path, last_phase: int) -> Path:
    """Init workspace and populate one canonical file per phase 1..last_phase."""
    init_workspace.init_workspace(tmp_path)
    for phase in range(1, last_phase + 1):
        rel = PHASE_CANONICAL[phase]
        (tmp_path / ".test-commander" / rel).write_text(
            f"# user content for phase {phase}\n", encoding="utf-8"
        )
    return tmp_path


# R1 — workspace missing -> /tc:init
def test_r1_recommends_init_when_workspace_missing(tmp_path):
    rec = next_step.next_step_for(tmp_path)
    assert rec is not None
    assert rec.command == "/tc:init"
    assert rec.phase == "1"
    assert rec.priority == 1


# R2 — fresh init, no metadata edits -> manual customize
def test_r2_recommends_metadata_customize_after_fresh_init(tmp_path):
    init_workspace.init_workspace(tmp_path)
    rec = next_step.next_step_for(tmp_path)
    assert rec is not None
    assert rec.phase == "1"
    assert rec.priority == 2
    assert "project.md" in rec.explanation


# R3 — Phase 1 in_progress, Phase 2 not_started -> /tc:review-requirements
def test_r3_recommends_review_requirements_after_phase_1(tmp_path):
    _through_phase(tmp_path, 1)
    rec = next_step.next_step_for(tmp_path)
    assert rec.command == "/tc:review-requirements"
    assert rec.phase == "2"


# R4 — Phase 2 in_progress, Phase 3 not_started -> /tc:learn-from-docs
def test_r4_recommends_learn_from_docs_after_phase_2(tmp_path):
    _through_phase(tmp_path, 2)
    rec = next_step.next_step_for(tmp_path)
    assert rec.command == "/tc:learn-from-docs"
    assert rec.phase == "3"


# R5 — Phase 3 in_progress, Phase 4 not_started -> /tc:create-charter
def test_r5_recommends_create_charter_after_phase_3(tmp_path):
    _through_phase(tmp_path, 3)
    rec = next_step.next_step_for(tmp_path)
    assert rec.command == "/tc:create-charter"
    assert rec.phase == "4"


# R6 — Phase 4 in_progress, Phase 5 not_started -> /tc:generate-bdd
def test_r6_recommends_generate_bdd_after_phase_4(tmp_path):
    _through_phase(tmp_path, 4)
    rec = next_step.next_step_for(tmp_path)
    assert rec.command == "/tc:generate-bdd"
    assert rec.phase == "5"


# R7 — Phase 5 in_progress, Phase 6 not_started -> /tc:automation-plan
def test_r7_recommends_automation_plan_after_phase_5(tmp_path):
    _through_phase(tmp_path, 5)
    rec = next_step.next_step_for(tmp_path)
    assert rec.command == "/tc:automation-plan"
    assert rec.phase == "6"


# R8 — Phase 6 in_progress, Phase 7 not_started -> /tc:run
def test_r8_recommends_run_after_phase_6(tmp_path):
    _through_phase(tmp_path, 6)
    rec = next_step.next_step_for(tmp_path)
    assert rec.command == "/tc:run"
    assert rec.phase == "7"


# R9 — Phase 7 in_progress, Phase 8 not_started -> /tc:learn
def test_r9_recommends_learn_after_phase_7(tmp_path):
    _through_phase(tmp_path, 7)
    rec = next_step.next_step_for(tmp_path)
    assert rec.command == "/tc:learn"
    assert rec.phase == "8"


# R10 — all of phases 1-8 in_progress -> /tc:report
def test_r10_recommends_report_when_mvp_complete(tmp_path):
    _through_phase(tmp_path, 8)
    rec = next_step.next_step_for(tmp_path)
    assert rec.command == "/tc:report"
    assert rec.priority == 10


# --- ranked-list + format ---

def test_recommendations_are_ranked_lowest_priority_first(tmp_path):
    _through_phase(tmp_path, 1)
    recs = next_step.recommendations_for(tmp_path)
    assert len(recs) > 1, "expected several gap recommendations after only Phase 1 populated"
    priorities = [r.priority for r in recs]
    assert priorities == sorted(priorities), f"recs not sorted by priority: {priorities}"
    # The top is R3 (Phase 2) given the fixture.
    assert recs[0].command == "/tc:review-requirements"


def test_format_starts_with_next_line(tmp_path):
    """Formatted output must begin with 'next: ' on the first line."""
    rec = next_step.next_step_for(tmp_path)  # missing workspace -> R1 fires
    text = next_step.format_recommendations([rec] if rec else [])
    first_line = text.splitlines()[0] if text else ""
    assert first_line.startswith("next: "), f"unexpected first line: {first_line!r}"


def test_format_includes_followups_when_multiple_matches(tmp_path):
    _through_phase(tmp_path, 1)
    recs = next_step.recommendations_for(tmp_path)
    text = next_step.format_recommendations(recs)
    assert "next: " in text
    assert "followups:" in text
