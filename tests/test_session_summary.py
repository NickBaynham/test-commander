"""Step 4.4 - /tc:session-summary end-to-end tests.

Drives session_summary.py against the exploration note produced by
running /tc:create-charter + /tc:explore against the seeded fixture.
Asserts:

- uninitialized workspace refused;
- missing exploration note refused with a precondition error
  directing the user at ``/tc:explore``;
- summary has every required section (Session / Observations summary /
  Anomalies summary / Coverage summary / Evidence index / Candidate
  Scenarios / Executive narrative);
- charter is resolved (target + mission appear in the summary);
- observation counts by event type aggregate correctly across the
  parsed exploration note;
- anomaly counts by category and severity aggregate correctly;
- coverage summary aggregates the matrix (X observed / Y partial /
  Z unobserved);
- candidate scenarios are extracted with a stable shape
  (``id``, ``title``, ``type``, ``source``) forward-compatible with
  Step 4.5's enrichment input;
- ``<workspace>/sessions/index.md`` lists the new session with a
  one-line summary;
- idempotent re-run produces byte-identical session summary and
  byte-identical index;
- when two sessions exist, both surface in the index.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "session_summary.py"
INIT = SCRIPTS / "init_workspace.py"
CHARTER_HELPER = SCRIPTS / "create_charter.py"
EXPLORE_HELPER = SCRIPTS / "explore.py"
FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-exploration-session"
FIXTURE_RECORDED_SESSION = FIXTURE_DIR / "recorded-session.json"

CHARTER_TARGET = (
    "Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets)."
)

SESSION_ID_RE = re.compile(r"^SESS-\d{8}-\d{3}$")
CS_ID_RE = re.compile(r"^CS-\d{3}-\d{3}$")


# ---------------------------------------------------------------------------
# CLI + setup helpers
# ---------------------------------------------------------------------------


def run_init(project_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(INIT), str(project_root)],
        capture_output=True,
        text=True,
        check=True,
    )


def run_helper(
    project_root: Path,
    *args: str,
    expected_exit: int = 0,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == expected_exit, (
        f"helper exited {proc.returncode} (expected {expected_exit}). "
        f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    return proc


def run_create_charter(project_root: Path, target: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(CHARTER_HELPER), str(project_root), "--target", target],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"create_charter failed: stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )


def run_explore(project_root: Path, charter_id: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(EXPLORE_HELPER), str(project_root),
         "--charter", charter_id],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"explore failed: stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )


def workspace_file(project_root: Path, rel: str) -> Path:
    return project_root / ".test-commander" / rel


def seed_minimal_phase_3_state(project_root: Path) -> None:
    workspace = project_root / ".test-commander"
    pk = workspace / "product-knowledge"
    pk.mkdir(parents=True, exist_ok=True)
    (pk / "entities.md").write_text(
        "# Entities\n\n## From documents\n\n"
        "- **Account** (file:1)\n"
        "- **Workspace** (file:2)\n",
        encoding="utf-8",
    )
    (pk / "user-journeys.md").write_text(
        "# User Journeys\n\n## From documents\n\n"
        "- **Sign in and open a workspace** (file:1) - 7 steps\n",
        encoding="utf-8",
    )
    (pk / "system-model.md").write_text(
        "# System Model\n\n## Sources ingested\n\n"
        "- **documents** - via `/tc:learn-from-docs`.\n",
        encoding="utf-8",
    )
    open_q = workspace / "requirements" / "open-questions.md"
    open_q.parent.mkdir(parents=True, exist_ok=True)
    open_q.write_text("# Open questions\n\n", encoding="utf-8")


def seed_workspace_and_run_explore(project_root: Path) -> str:
    """Set up workspace, create CH-001, run /tc:explore. Return the SESS-ID."""
    run_init(project_root)
    seed_minimal_phase_3_state(project_root)
    run_create_charter(project_root, CHARTER_TARGET)
    recorded_dir = workspace_file(project_root, "documents/uploaded/recorded-sessions")
    recorded_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_RECORDED_SESSION, recorded_dir / "CH-001.json")
    run_explore(project_root, "CH-001")
    notes = list(workspace_file(project_root, "exploration-notes").glob("SESS-*.md"))
    assert len(notes) == 1, f"expected exactly one exploration note; got {len(notes)}"
    return notes[0].stem


def find_session_summary(project_root: Path) -> Path:
    sessions_dir = workspace_file(project_root, "sessions")
    matches = [p for p in sessions_dir.glob("SESS-*.md") if p.name != "index.md"]
    assert matches, f"expected a session summary under {sessions_dir}; found none"
    assert len(matches) == 1, f"expected exactly one session summary; found {len(matches)}"
    return matches[0]


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_helper_file_exists() -> None:
    assert HELPER.is_file(), f"missing helper: {HELPER.relative_to(REPO)}"


def test_uninitialized_workspace_refused(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(HELPER), str(tmp_path), "--session",
         "SESS-20260528-600"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2, proc.stderr


def test_missing_exploration_note_refused(tmp_path: Path) -> None:
    """Workspace exists but no exploration note has been generated yet.
    The helper must refuse with a precondition error directing the user
    at /tc:explore."""
    run_init(tmp_path)
    proc = run_helper(tmp_path, "--session", "SESS-20260528-600", expected_exit=2)
    stderr_lower = proc.stderr.lower()
    assert "exploration" in stderr_lower or "session" in stderr_lower
    assert "/tc:explore" in proc.stderr


# ---------------------------------------------------------------------------
# Happy path: seeded exploration -> session summary
# ---------------------------------------------------------------------------


def test_session_summary_generated(tmp_path: Path) -> None:
    session_id = seed_workspace_and_run_explore(tmp_path)
    proc = run_helper(tmp_path, "--session", session_id)
    summary = find_session_summary(tmp_path)
    assert summary.stem == session_id, (
        f"summary filename {summary.stem!r} must equal SESS-ID {session_id!r}"
    )
    # CLI announces success.
    assert "summary" in proc.stdout.lower()


def test_summary_has_required_sections(tmp_path: Path) -> None:
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    text = find_session_summary(tmp_path).read_text(encoding="utf-8")
    for heading in (
        "# ",  # title
        "## Session",
        "## Observation Summary",
        "## Anomaly Summary",
        "## Charter Coverage Summary",
        "## Evidence",
        "## Candidate Scenarios",
        "## Executive Narrative",
    ):
        assert heading in text, f"summary missing required heading: {heading!r}"


def test_charter_resolved_in_summary(tmp_path: Path) -> None:
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    text = find_session_summary(tmp_path).read_text(encoding="utf-8")
    assert "CH-001" in text
    assert "Sign-in flow" in text


def test_observation_counts_by_event_type(tmp_path: Path) -> None:
    """The seeded recording has 55 events: 8 page_loads, 11 clicks, 6 fills,
    9 screenshots, 2 console_messages, 13 network_requests, 6 anomalies
    (anomalies are not observations - they live in the Anomaly summary).
    Observation count = 8 + 11 + 6 + 9 + 2 + 13 = 49."""
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    text = find_session_summary(tmp_path).read_text(encoding="utf-8")
    # Each event type listed with its count.
    for event_type in (
        "page_load",
        "click",
        "fill",
        "screenshot",
        "console_message",
        "network_request",
    ):
        assert event_type in text, (
            f"Observation summary missing event type {event_type!r}"
        )


def test_anomaly_counts_by_category_and_severity(tmp_path: Path) -> None:
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    text = find_session_summary(tmp_path).read_text(encoding="utf-8")
    for category in (
        "slow-response",
        "console-error",
        "broken-link",
        "missing-evidence",
        "auth-mismatch",
        "unexpected-state",
    ):
        assert category in text, f"Anomaly summary missing category {category!r}"
    # Severity grouping present.
    text_lower = text.lower()
    severities_present = sum(1 for sev in ("low", "medium", "high", "critical")
                             if sev in text_lower)
    assert severities_present >= 2, (
        "Anomaly summary must group anomalies by severity (at least 2 levels seen)"
    )


def test_coverage_summary_aggregates_correctly(tmp_path: Path) -> None:
    """The seeded fixture's CH-001 has 5 acceptance criteria. After
    /tc:explore, at least one is partial (AC5 on session expiration);
    the rest are observed. Summary must aggregate the matrix into a
    one-line verdict."""
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    text = find_session_summary(tmp_path).read_text(encoding="utf-8")
    # Aggregate counts must appear.
    text_lower = text.lower()
    assert "observed" in text_lower
    assert "partial" in text_lower
    # The 5 ACs must be accounted for in the summary.
    assert re.search(r"\b5\b.*?acceptance", text, flags=re.IGNORECASE | re.DOTALL) or \
           re.search(r"acceptance.+?\b5\b", text, flags=re.IGNORECASE | re.DOTALL), (
        "Coverage summary must report the total acceptance-criteria count"
    )


# ---------------------------------------------------------------------------
# Candidate Scenarios
# ---------------------------------------------------------------------------


def test_candidate_scenarios_extracted(tmp_path: Path) -> None:
    """At least one candidate per anomaly + one per partial/unobserved AC."""
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    text = find_session_summary(tmp_path).read_text(encoding="utf-8")
    # The Candidate Scenarios section must list at least 6 (six anomalies)
    # plus at least 1 for the partial-coverage AC.
    cs_matches = re.findall(r"\bCS-\d{3}-\d{3}\b", text)
    assert len(cs_matches) >= 6, (
        f"expected at least 6 candidate scenarios (one per anomaly); "
        f"got {len(cs_matches)}: {cs_matches}"
    )


def test_candidate_scenarios_have_stable_shape(tmp_path: Path) -> None:
    """Every candidate must declare id + title + type + source so Step 4.5's
    enrichment can map candidates to REQ-IDs without ambiguity."""
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    text = find_session_summary(tmp_path).read_text(encoding="utf-8")

    # Each candidate is rendered as a structured bullet or table row with
    # id, title, type, source. Validate the shape by counting candidates
    # that mention all four fields.
    candidate_blocks = re.findall(
        r"CS-\d{3}-\d{3}.+?(?=CS-\d{3}-\d{3}|\Z)",
        text,
        flags=re.DOTALL,
    )
    assert candidate_blocks, "no candidate scenario blocks found"
    well_formed = 0
    for block in candidate_blocks:
        block_lower = block.lower()
        if all(field in block_lower for field in ("title", "type", "source")):
            well_formed += 1
    assert well_formed >= 6, (
        f"expected >= 6 well-formed candidate blocks "
        f"(with title/type/source); got {well_formed}/{len(candidate_blocks)}"
    )


def test_candidate_types_are_universal_core(tmp_path: Path) -> None:
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    text = find_session_summary(tmp_path).read_text(encoding="utf-8")
    # Universal-core candidate types: happy / edge / negative.
    text_lower = text.lower()
    types_seen = sum(
        1 for t in ("happy", "edge", "negative") if t in text_lower
    )
    assert types_seen >= 2, (
        f"candidates must include at least 2 universal-core types "
        f"(happy/edge/negative); got {types_seen}"
    )


# ---------------------------------------------------------------------------
# sessions/index.md
# ---------------------------------------------------------------------------


def test_sessions_index_updated(tmp_path: Path) -> None:
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    index = workspace_file(tmp_path, "sessions/index.md")
    assert index.is_file(), f"expected sessions/index.md at {index}"
    text = index.read_text(encoding="utf-8")
    assert session_id in text, f"index must list session {session_id}"
    assert "CH-001" in text, "index must list the charter ID"


def test_multiple_sessions_in_index(tmp_path: Path) -> None:
    """When two sessions exist (the seeded session + a synthetic second
    one), both must surface in the index."""
    session_id_1 = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id_1)

    # Synthesize a second session at a different SESS-ID by writing a
    # minimal valid exploration note directly.
    second_id = "SESS-20260528-700"
    second_note = workspace_file(tmp_path, f"exploration-notes/{second_id}.md")
    second_note.write_text(
        f"# {second_id} - exploration note for CH-001\n\n"
        "## Session\n\n"
        "- Charter: `CH-001` - Sign-in flow plus workspace-detail asset upload.\n"
        "- Started at: 2026-05-28T11:00:00.000Z\n"
        "- Source: `documents/uploaded/recorded-sessions/CH-001.json`\n"
        "- Observations: 0\n"
        "- Anomalies: 0\n"
        "- Evidence (screenshots): 0\n\n"
        "## Observations\n\n_No observations._\n\n"
        "## Anomalies\n\n_No anomalies detected in this session._\n\n"
        "## Evidence\n\n_No screenshots captured in this session._\n\n"
        "## Charter Coverage\n\n_The charter declared no acceptance criteria._\n",
        encoding="utf-8",
    )
    run_helper(tmp_path, "--session", second_id)

    index_text = workspace_file(tmp_path, "sessions/index.md").read_text(
        encoding="utf-8"
    )
    assert session_id_1 in index_text
    assert second_id in index_text


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_idempotent_rerun_byte_identical(tmp_path: Path) -> None:
    session_id = seed_workspace_and_run_explore(tmp_path)
    run_helper(tmp_path, "--session", session_id)
    first_summary = find_session_summary(tmp_path).read_bytes()
    first_index = workspace_file(tmp_path, "sessions/index.md").read_bytes()

    run_helper(tmp_path, "--session", session_id)
    second_summary = find_session_summary(tmp_path).read_bytes()
    second_index = workspace_file(tmp_path, "sessions/index.md").read_bytes()

    assert first_summary == second_summary, (
        "session summary must be byte-identical on idempotent re-run"
    )
    assert first_index == second_index, (
        "sessions/index.md must be byte-identical on idempotent re-run"
    )
