"""Step 1.3 — workspace_state snapshot tests.

Per the plan: three fixtures (empty / partial / full) plus determinism +
last-modified sanity checks. Fixtures are built from the bundled template
via init_workspace, then selectively modified.
"""

from pathlib import Path

import init_workspace
import workspace_state

REPO = Path(__file__).resolve().parent.parent


# --- empty case ---

def test_snapshot_when_workspace_missing(tmp_path):
    snap = workspace_state.snapshot(tmp_path)
    assert not snap.exists
    assert not snap.initialized
    assert snap.counts == {}
    assert snap.populated == {}
    assert snap.last_modified is None
    assert all(s == "not_started" for s in snap.phase_status.values())


# --- fresh-init case (empty in the user-content sense) ---

def test_snapshot_after_fresh_init_has_zero_populated(tmp_path):
    init_workspace.init_workspace(tmp_path)
    snap = workspace_state.snapshot(tmp_path)
    assert snap.exists
    assert snap.initialized
    assert sum(snap.counts.values()) == 63
    assert sum(snap.populated.values()) == 0
    assert all(s == "not_started" for s in snap.phase_status.values())
    assert snap.last_modified is not None


# --- partial case ---

def test_snapshot_partial_user_content(tmp_path):
    init_workspace.init_workspace(tmp_path)
    ws = tmp_path / ".test-commander"
    (ws / "requirements" / "requirements-inventory.md").write_text(
        "# Real Inventory\n\nLogin requirement.\n", encoding="utf-8"
    )
    snap = workspace_state.snapshot(tmp_path)
    assert snap.populated.get("requirements", 0) == 1
    assert snap.phase_status["2"] == "in_progress"
    # Other phases unaffected
    assert snap.phase_status["3"] == "not_started"
    assert snap.phase_status["8"] == "not_started"


# --- full case ---

def test_snapshot_full_user_content(tmp_path):
    init_workspace.init_workspace(tmp_path)
    ws = tmp_path / ".test-commander"
    per_phase_canonical = {
        "1": "project.md",
        "2": "requirements/requirements-inventory.md",
        "3": "product-knowledge/system-model.md",
        "4": "charters/README.md",
        "5": "bdd/features/README.md",
        "6": "automation-plan/README.md",
        "7": "quality-report/current-quality-report.md",
        "8": "learning/lessons-inbox.md",
        "9": "visuals/README.md",
        "10.5": "policy/permissions.yaml",
    }
    for phase, rel in per_phase_canonical.items():
        (ws / rel).write_text(f"# real content for phase {phase}\n", encoding="utf-8")
    snap = workspace_state.snapshot(tmp_path)
    not_started = {p for p, s in snap.phase_status.items() if s != "in_progress"}
    assert not not_started, (
        f"these phases stayed not_started despite user content: {sorted(not_started)}; "
        f"got status: {snap.phase_status}"
    )


# --- determinism + last-modified sanity ---

def test_snapshot_is_deterministic(tmp_path):
    init_workspace.init_workspace(tmp_path)
    a = workspace_state.snapshot(tmp_path)
    b = workspace_state.snapshot(tmp_path)
    assert a.counts == b.counts
    assert a.populated == b.populated
    assert a.phase_status == b.phase_status


def test_orphan_workspace_file_counts_as_populated(tmp_path):
    """A file in the workspace that has no template counterpart counts as populated."""
    init_workspace.init_workspace(tmp_path)
    ws = tmp_path / ".test-commander"
    (ws / "requirements" / "extra-note.md").write_text("# my own note\n", encoding="utf-8")
    snap = workspace_state.snapshot(tmp_path)
    assert snap.populated.get("requirements", 0) == 1
    assert snap.phase_status["2"] == "in_progress"
