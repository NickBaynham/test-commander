"""Step 8.9 - Phase 8 integration smoke.

Drives the full Phase 2 -> ... -> 8 helper chain in workflow order against a
fresh tmp consuming project. Reuses the Phase-7 integration's upstream sweep
(through the run -> analyze -> report -> gate chain, which produces the
analysis.md, exploration notes, and open-questions the capture commands read),
then runs the Phase 8 learning loop: capture (failures + exploration + feedback
+ manual) -> review -> promote --apply.

Asserts the Step 8.9 contract from planning/plan.md: the capture commands append
tc-lesson/v1 candidates from the upstream artifacts; /tc:review-lessons sorts
them into the buckets and clears the inbox; /tc:promote-lessons proposes by
default and applies under --apply into promoted-guidance.md; the write boundary
holds (everything outside learning/ byte-identical before/after Phase 8 -- the
loop writes ONLY under learning/, Q6); /tc:next advances past /tc:learn. Plus a
byte-stable re-run.
"""

from __future__ import annotations

import sys
from pathlib import Path

import capture_lesson
import learn_from_exploration
import learn_from_failures
import learn_from_feedback
import next_step
import promote_lessons
import review_lessons
import workspace_state

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))
import test_phase_7_integration as p7  # noqa: E402

NOW = p7.NOW


def snapshot_outside_learning(project: Path) -> dict[Path, bytes]:
    ws = project / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and "learning" not in p.relative_to(ws).parts
    }


def run_phase_8(project: Path) -> None:
    learn_from_failures.learn_from_failures(project, now=NOW)
    learn_from_exploration.learn_from_exploration(project, now=NOW)
    learn_from_feedback.learn_from_feedback(project, now=NOW)
    capture_lesson.learn(project, note="Prefer role-based locators over CSS.",
                         category="heuristic", now=NOW)
    review_lessons.review_lessons(project)
    promote_lessons.promote(project, apply=True)


def _setup_through_phase_7(tmp_path: Path) -> Path:
    project = p7.setup_consuming_project(tmp_path)
    p7.run_through_phase_6(project)
    p7.run_phase_7(project)
    return project


def test_phase_ownership_8_needs_no_narrowing():
    """Phase 8 writes only under learning/, which is already its unique signal."""
    assert workspace_state.PHASE_OWNERSHIP["8"] == ["learning"]


def test_full_phase_8_workflow(tmp_path: Path) -> None:
    project = _setup_through_phase_7(tmp_path)
    workspace = project / ".test-commander"
    learning = workspace / "learning"

    outside_before = snapshot_outside_learning(project)
    run_phase_8(project)

    # Capture appended candidates from the upstream artifacts, then review cleared them.
    inbox = (learning / "lessons-inbox.md").read_text(encoding="utf-8")
    assert "LESSON-" not in inbox, "review must clear the inbox of reviewed candidates"
    accepted = (learning / "accepted-lessons.md").read_text(encoding="utf-8")
    assert "tc-lesson/v1" in accepted, "review produced no accepted lessons"

    # Promote --apply moved accepted lessons into project guidance.
    guidance = (learning / "promoted-guidance.md").read_text(encoding="utf-8")
    assert "status: promoted" in guidance, "promote --apply did not write promoted-guidance.md"

    # Write boundary (Q6): nothing outside learning/ changed.
    assert snapshot_outside_learning(project) == outside_before, (
        "the learning loop must write only under learning/"
    )

    # /tc:next advances past /tc:learn.
    rec = next_step.next_step_for(project)
    if rec is not None:
        assert rec.command != "/tc:learn", f"/tc:next still recommends /tc:learn: {rec}"


def test_byte_stable_rerun_across_phase_8(tmp_path: Path) -> None:
    project = _setup_through_phase_7(tmp_path)
    learning = project / ".test-commander" / "learning"
    run_phase_8(project)
    targets = sorted(p for p in learning.glob("*.md") if p.is_file())
    first = {p: p.read_bytes() for p in targets}
    run_phase_8(project)  # dedup + idempotent review/promote -> no change
    for path, data in first.items():
        assert path.read_bytes() == data, f"{path.name} not byte-stable on Phase 8 re-run"
