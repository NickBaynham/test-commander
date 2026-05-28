"""Step 1.7 — Phase 1 integration smoke.

Drives all four Phase 1 helpers in sequence against a fresh tmp consuming
project and asserts each transition matches expectations. Complements the
per-command unit tests in 1.2–1.5 by exercising the full
init -> status -> next -> journal -> next workflow end to end.
"""

from datetime import UTC, datetime

import init_workspace
import journal
import next_step
import workspace_state


def test_full_phase_1_workflow(tmp_path):
    project = tmp_path / "my-project"
    project.mkdir()

    # --- 1. /tc:init ---
    init_result = init_workspace.init_workspace(project)
    workspace = project / ".test-commander"
    assert init_result.workspace == workspace
    assert workspace.is_dir()
    # Per the Phase-2 Step-2.8 lesson: assert >= for monotonically
    # non-decreasing counts. Phase 1 shipped 63 starter files; Phase 3
    # Step 3.6 added tests-coverage.md (64); future phases may add more.
    initial_count = len(init_result.created)
    assert initial_count >= 63
    assert len(init_result.skipped) == 0

    # Re-init is a clean no-op (idempotency)
    rerun = init_workspace.init_workspace(project)
    assert len(rerun.created) == 0
    assert len(rerun.skipped) == initial_count

    # --- 2. /tc:status on fresh workspace ---
    snap = workspace_state.snapshot(project)
    assert snap.exists
    assert snap.initialized
    assert sum(snap.counts.values()) == initial_count
    assert sum(snap.populated.values()) == 0
    assert all(s == "not_started" for s in snap.phase_status.values())

    # --- 3. /tc:next on fresh workspace -> R2 (manual customize) ---
    rec = next_step.next_step_for(project)
    assert rec is not None
    assert rec.priority == 2
    assert rec.phase == "1"
    assert "project.md" in rec.explanation

    # --- 4. User customizes project metadata (the R2 action) ---
    (workspace / "project.md").write_text(
        "# my-project\n\nReal project metadata.\n", encoding="utf-8"
    )

    # --- 5. /tc:status sees the change ---
    snap2 = workspace_state.snapshot(project)
    assert snap2.populated.get("project.md", 0) == 1
    assert snap2.phase_status["1"] == "in_progress"
    assert snap2.phase_status["2"] == "not_started"

    # --- 6. /tc:next now recommends R3 (/tc:review-requirements) ---
    rec2 = next_step.next_step_for(project)
    assert rec2.command == "/tc:review-requirements"
    assert rec2.phase == "2"
    # And the ranked list has the downstream gaps too
    all_recs = next_step.recommendations_for(project)
    commands = [r.command for r in all_recs]
    assert commands[0] == "/tc:review-requirements"
    assert "/tc:learn-from-docs" in commands
    assert "/tc:create-charter" in commands

    # --- 7. /tc:journal append ---
    ts1 = datetime(2026, 5, 26, 14, 0, 0, tzinfo=UTC)
    body1 = "Initialized workspace and customized project.md."
    ar1 = journal.append(workspace, body1, timestamp=ts1)
    assert ar1.path == workspace / "journal" / "2026-05-26.md"

    ts2 = datetime(2026, 5, 26, 15, 30, 0, tzinfo=UTC)
    body2 = "Reviewed first three requirements."
    journal.append(workspace, body2, timestamp=ts2)

    # --- 8. /tc:journal summarize returns both entries chronologically ---
    summary = journal.summarize(workspace)
    assert len(summary.entries) == 2
    bodies = [e.body for e in summary.entries]
    assert bodies == [body1, body2]

    # --- 9. /tc:status reflects journal activity (phase 1 stays in_progress) ---
    snap3 = workspace_state.snapshot(project)
    assert snap3.phase_status["1"] == "in_progress"
    # last_modified is set and not None
    assert snap3.last_modified is not None
