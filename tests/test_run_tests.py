"""Step 7.2 - /tc:run (run_tests) end-to-end tests.

Drives ``run_tests.py`` against a tmp consuming project seeded with the
recorded Playwright report and the Phase-6 chain from
``tests/fixtures/seeded-results/``. The helper ingests the JSON report and
writes a per-run record under ``runs/<RUN-ID>/`` mapping each pass / fail /
flaky case to its scenario, candidate, and requirement via the ``@req:``/
``@cs:`` provenance and the Phase-6 ``automation-map.md``.

Asserts the Step 7.2 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- the real ``npx playwright test`` invocation is refused under pytest (the
  hermetic boundary) with a directing message;
- a recorded ``results.json`` is ingested into a ``runs/<RUN-ID>/`` record
  mapping each result to its scenario via provenance;
- run modes (smoke / regression / failed-only / feature / tagged) filter the
  result set;
- the injected clock makes the run record byte-stable across re-runs;
- ``automation-map.md`` and the generated specs are byte-identical
  before/after (read-only upstream).

Evidence indexing (the ``--no-index`` auto-run) ships in Step 7.3; 7.2 is
execution + ingestion only.
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
HELPER = SCRIPTS / "run_tests.py"
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


def run_cli(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )


def seed_run_workspace(project_root: Path) -> Path:
    """Init a workspace and drop the Phase-6 chain the report belongs to."""
    run_init(project_root)
    ws = project_root / ".test-commander"
    (ws / "traceability").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_MAP, ws / "traceability" / "automation-map.md")
    e2e = project_root / "tests" / "e2e"
    e2e.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_SPEC, e2e / "sign-in.spec.ts")
    return ws


def run_record_dir(ws: Path, run_id: str = RUN_ID) -> Path:
    return ws / "runs" / run_id


def load_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("run_tests", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def do_run(project_root: Path, **kwargs):
    """In-process run with the injected clock defaulted to FIXED_NOW."""
    mod = load_module()
    kwargs.setdefault("now", datetime.fromisoformat(FIXED_NOW))
    kwargs.setdefault("report", FIXTURE_REPORT)
    return mod, mod.run(project_root, **kwargs)


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = run_cli(tmp_path, "--report", str(FIXTURE_REPORT))
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_real_execution_refused_under_pytest(tmp_path):
    """With no recorded report, run() must shell out to Playwright - and that
    is refused under pytest via the PYTEST_CURRENT_TEST guard."""
    seed_run_workspace(tmp_path)
    mod = load_module()
    try:
        mod.run(tmp_path, now=datetime.fromisoformat(FIXED_NOW), report=None)
    except mod.ExecutionRefusedError as exc:
        assert "pytest" in str(exc).lower()
        assert "--report" in str(exc)
    else:
        raise AssertionError("expected ExecutionRefusedError under pytest")


def test_real_execution_refused_via_cli(tmp_path):
    seed_run_workspace(tmp_path)
    result = run_cli(tmp_path)  # no --report -> execution path
    assert result.returncode == 2, result.stdout
    assert "pytest" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


def test_recorded_report_ingested_writes_run_record(tmp_path):
    ws = seed_run_workspace(tmp_path)
    _, outcome = do_run(tmp_path)
    record_dir = run_record_dir(ws)
    assert record_dir.is_dir(), "expected runs/<RUN-ID>/ record directory"
    summary = (record_dir / "run.md").read_text(encoding="utf-8")
    # Every result maps to its requirement and candidate via provenance.
    for cs in ("CS-001-001", "CS-001-002", "CS-001-003"):
        assert cs in summary, f"run record must map {cs}"
    assert "REQ-001" in summary
    # The three result classes are all represented.
    assert "passed" in summary and "failed" in summary and "flaky" in summary


def test_run_record_maps_result_to_spec_via_automation_map(tmp_path):
    ws = seed_run_workspace(tmp_path)
    _, outcome = do_run(tmp_path)
    summary = (run_record_dir(ws) / "run.md").read_text(encoding="utf-8")
    assert "tests/e2e/sign-in.spec.ts" in summary, "each result must resolve its spec"


def test_outcome_reports_run_id_and_counts(tmp_path):
    seed_run_workspace(tmp_path)
    _, outcome = do_run(tmp_path)
    assert outcome.run_id == RUN_ID
    assert outcome.total == 3
    assert outcome.passed == 1 and outcome.failed == 1 and outcome.flaky == 1


# ---------------------------------------------------------------------------
# Run modes
# ---------------------------------------------------------------------------


def test_smoke_mode_filters_to_smoke_tagged(tmp_path):
    seed_run_workspace(tmp_path)
    _, outcome = do_run(tmp_path, mode="smoke")
    assert outcome.total == 1
    assert outcome.candidates == ["CS-001-001"]


def test_failed_only_mode_filters_to_failures(tmp_path):
    seed_run_workspace(tmp_path)
    _, outcome = do_run(tmp_path, mode="failed-only")
    assert outcome.candidates == ["CS-001-002"]


def test_feature_mode_requires_area_and_filters(tmp_path):
    seed_run_workspace(tmp_path)
    _, outcome = do_run(tmp_path, mode="feature", area="sign-in")
    assert outcome.total == 3  # all three scenarios are @area:sign-in


def test_tagged_mode_filters_by_tag(tmp_path):
    seed_run_workspace(tmp_path)
    _, outcome = do_run(tmp_path, mode="tagged", tag="@regression")
    assert sorted(outcome.candidates) == ["CS-001-002", "CS-001-003"]


# ---------------------------------------------------------------------------
# Determinism + read-only upstream
# ---------------------------------------------------------------------------


def test_injected_clock_makes_run_record_byte_stable(tmp_path):
    ws = seed_run_workspace(tmp_path)
    do_run(tmp_path)
    first = {p.name: p.read_bytes() for p in sorted(run_record_dir(ws).iterdir())}
    do_run(tmp_path)
    second = {p.name: p.read_bytes() for p in sorted(run_record_dir(ws).iterdir())}
    assert first == second, "same injected clock must produce byte-identical records"


def test_upstream_is_read_only(tmp_path):
    ws = seed_run_workspace(tmp_path)
    map_before = (ws / "traceability" / "automation-map.md").read_bytes()
    spec_before = (tmp_path / "tests" / "e2e" / "sign-in.spec.ts").read_bytes()
    do_run(tmp_path)
    assert (ws / "traceability" / "automation-map.md").read_bytes() == map_before
    assert (tmp_path / "tests" / "e2e" / "sign-in.spec.ts").read_bytes() == spec_before
