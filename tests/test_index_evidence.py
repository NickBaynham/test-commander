"""Step 7.3 - tc-evidence indexer (index_evidence) end-to-end tests.

Drives ``index_evidence.py`` against a tmp consuming project that has a
``/tc:run`` record (produced by ``run_tests.py``) referencing the evidence
stubs in ``tests/fixtures/seeded-results/``. The indexer routes each artifact
into the workspace evidence tree per the commit-versus-ignore policy, writes
``evidence/evidence-index.md`` with run + scenario provenance, and manages the
evidence ``.gitignore`` (videos and traces ignored; the documented git-lfs
opt-in).

Asserts the Step 7.3 contract from planning/plan.md:

- screenshots routed and committed;
- videos and traces routed and git-ignored (the ``.gitignore`` entry exists -
  not that the files are deleted);
- the evidence index lists every artifact with its run + scenario provenance;
- idempotent re-run is byte-stable;
- ``index_run_evidence()`` is the same code path ``/tc:run`` auto-runs
  (identity + ``--no-index`` suppression).
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "index_evidence.py"
RUN_HELPER = SCRIPTS / "run_tests.py"
INIT = SCRIPTS / "init_workspace.py"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-results"
FIXTURE_REPORT = FIXTURE_DIR / "results.json"
FIXTURE_MAP = FIXTURE_DIR / "automation-map.md"
FIXTURE_SPEC = FIXTURE_DIR / "sign-in.spec.ts"

FIXED_NOW = "2026-01-15T09:30:00"
RUN_ID = "RUN-20260115-093000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_init(project_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(INIT), str(project_root)],
        capture_output=True,
        text=True,
        check=True,
    )


def cli(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )


def seed_run_workspace(project_root: Path) -> Path:
    run_init(project_root)
    ws = project_root / ".test-commander"
    (ws / "traceability").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_MAP, ws / "traceability" / "automation-map.md")
    e2e = project_root / "tests" / "e2e"
    e2e.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_SPEC, e2e / "sign-in.spec.ts")
    return ws


def load(name: str, path: Path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_run_record(project_root: Path, *, no_index: bool) -> str:
    """Produce a runs/<RUN-ID>/ record via run_tests (the real upstream)."""
    run_mod = load("run_tests", RUN_HELPER)
    outcome = run_mod.run(
        project_root,
        now=datetime.fromisoformat(FIXED_NOW),
        report=FIXTURE_REPORT,
        no_index=no_index,
    )
    return outcome.run_id


def evidence_index(ws: Path) -> Path:
    return ws / "evidence" / "evidence-index.md"


def gitignore(ws: Path) -> Path:
    return ws / "evidence" / ".gitignore"


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path, "--run-id", RUN_ID)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_missing_run_record_refused(tmp_path):
    run_init(tmp_path)
    result = cli(tmp_path, "--run-id", "RUN-20990101-000000")
    assert result.returncode == 2, result.stdout
    assert "run" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Routing + policy
# ---------------------------------------------------------------------------


def test_screenshot_routed_and_committed(tmp_path):
    ws = seed_run_workspace(tmp_path)
    run_id = make_run_record(tmp_path, no_index=True)
    mod = load("index_evidence", HELPER)
    mod.index_run_evidence(tmp_path, run_id, source_root=FIXTURE_DIR)
    routed = ws / "evidence" / "screenshots" / "CS-001-002-failure.png"
    assert routed.is_file(), "screenshot must be routed into evidence/screenshots/"
    assert "screenshots" not in gitignore(ws).read_text(encoding="utf-8"), (
        "screenshots are committed - must not be git-ignored"
    )


def test_videos_and_traces_routed_and_gitignored(tmp_path):
    ws = seed_run_workspace(tmp_path)
    run_id = make_run_record(tmp_path, no_index=True)
    mod = load("index_evidence", HELPER)
    mod.index_run_evidence(tmp_path, run_id, source_root=FIXTURE_DIR)
    assert (ws / "evidence" / "videos" / "CS-001-002-failure.webm").is_file()
    assert (ws / "evidence" / "traces" / "CS-001-002-failure.zip").is_file()
    ignore_text = gitignore(ws).read_text(encoding="utf-8")
    assert "videos/" in ignore_text, "videos must be git-ignored by default"
    assert "traces/" in ignore_text, "traces must be git-ignored by default"
    assert "lfs" in ignore_text.lower(), "the .gitignore must document the git-lfs opt-in"


def test_evidence_index_lists_artifacts_with_provenance(tmp_path):
    ws = seed_run_workspace(tmp_path)
    run_id = make_run_record(tmp_path, no_index=True)
    mod = load("index_evidence", HELPER)
    mod.index_run_evidence(tmp_path, run_id, source_root=FIXTURE_DIR)
    index = evidence_index(ws).read_text(encoding="utf-8")
    for artifact in (
        "CS-001-002-failure.png",
        "CS-001-002-failure.webm",
        "CS-001-002-failure.zip",
        "CS-001-003-retry.zip",
    ):
        assert artifact in index, f"index must list {artifact}"
    assert RUN_ID in index, "index must carry the run provenance"
    assert "REQ-001" in index and "CS-001-002" in index, "index must carry scenario provenance"


# ---------------------------------------------------------------------------
# Determinism + the shared auto-run code path
# ---------------------------------------------------------------------------


def test_idempotent_byte_stable(tmp_path):
    ws = seed_run_workspace(tmp_path)
    run_id = make_run_record(tmp_path, no_index=True)
    mod = load("index_evidence", HELPER)
    mod.index_run_evidence(tmp_path, run_id, source_root=FIXTURE_DIR)
    first_index = evidence_index(ws).read_bytes()
    first_ignore = gitignore(ws).read_bytes()
    mod.index_run_evidence(tmp_path, run_id, source_root=FIXTURE_DIR)
    assert evidence_index(ws).read_bytes() == first_index
    assert gitignore(ws).read_bytes() == first_ignore


def test_run_autorun_matches_standalone(tmp_path):
    """/tc:run's auto-index produces the same evidence index as the standalone
    indexer (proving the shared code path)."""
    # Project A: auto-run via /tc:run.
    ws_a = seed_run_workspace(tmp_path / "a")
    make_run_record(tmp_path / "a", no_index=False)
    # Project B: suppressed, then standalone index.
    ws_b = seed_run_workspace(tmp_path / "b")
    run_id = make_run_record(tmp_path / "b", no_index=True)
    mod = load("index_evidence", HELPER)
    mod.index_run_evidence(tmp_path / "b", run_id, source_root=FIXTURE_DIR)
    assert evidence_index(ws_a).read_bytes() == evidence_index(ws_b).read_bytes()


def test_no_index_suppresses_the_autorun(tmp_path):
    ws = seed_run_workspace(tmp_path)
    make_run_record(tmp_path, no_index=True)
    assert not evidence_index(ws).exists(), "--no-index must suppress evidence indexing"
